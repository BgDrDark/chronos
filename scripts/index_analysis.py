#!/usr/bin/env python3
"""
WorkingTime Database Index Analysis Script

This script provides comprehensive index analysis, including unused index detection,
missing index recommendations, and index performance optimization suggestions.
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database.database_optimized import db_manager

@dataclass
class IndexInfo:
    """Data class for index information"""
    schema: str
    table: str
    index_name: str
    index_type: str
    is_unique: bool
    is_primary: bool
    columns: List[str]
    size_mb: float
    scans: int
    tuples_read: int
    tuples_fetch: int
    last_used: str = None

@dataclass
class MissingIndex:
    """Data class for missing index recommendations"""
    table: str
    columns: List[str]
    query_type: str
    estimated_benefit: str
    query_sample: str

class IndexAnalyzer:
    """Comprehensive database index analysis tool"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def get_session(self):
        """Get database session"""
        return self.db_manager.config.get_session()
    
    async def get_all_indexes(self) -> List[IndexInfo]:
        """Get comprehensive index information"""
        query = """
        SELECT 
            n.nspname as schema_name,
            t.relname as table_name,
            i.relname as index_name,
            am.amname as index_type,
            ix.indisunique as is_unique,
            ix.indisprimary as is_primary,
            pg_get_indexdef(ix.indexrelid) as index_def,
            pg_relation_size(i.oid) as size_bytes,
            COALESCE(idx.idx_scan, 0) as scans,
            COALESCE(idx.idx_tup_read, 0) as tuples_read,
            COALESCE(idx.idx_tup_fetch, 0) as tuples_fetch
        FROM pg_class t
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_am am ON i.relam = am.oid
        LEFT JOIN pg_stat_user_indexes idx ON 
            idx.schemaname = n.nspname AND 
            idx.relname = t.relname AND 
            idx.indexrelname = i.relname
        WHERE n.nspname = 'public'
        AND t.relkind = 'r'  -- Only regular tables
        ORDER BY t.relname, i.relname
        """
        
        async with await self.get_session() as session:
            result = await session.execute(text(query))
            rows = result.fetchall()
        
        indexes = []
        for row in rows:
            # Extract column names from index definition
            index_def = row.index_def
            columns = self._extract_columns_from_def(index_def)
            
            index_info = IndexInfo(
                schema=row.schema_name,
                table=row.table_name,
                index_name=row.index_name,
                index_type=row.index_type,
                is_unique=row.is_unique,
                is_primary=row.is_primary,
                columns=columns,
                size_mb=row.size_bytes / (1024 * 1024),  # Convert to MB
                scans=row.scans,
                tuples_read=row.tuples_read,
                tuples_fetch=row.tuples_fetch
            )
            indexes.append(index_info)
        
        return indexes
    
    def _extract_columns_from_def(self, index_def: str) -> List[str]:
        """Extract column names from index definition"""
        # Simple parsing - extract column names between parentheses
        import re
        
        # Find content between parentheses
        match = re.search(r'\((.*?)\)', index_def)
        if not match:
            return []
        
        content = match.group(1)
        
        # Split by commas and clean up column names
        columns = []
        for col in content.split(','):
            # Remove functions, quotes, and whitespace
            col = col.strip()
            col = re.sub(r'[^a-zA-Z0-9_]', '', col)
            if col and col.lower() not in ['where', 'and', 'or', 'asc', 'desc']:
                columns.append(col)
        
        return columns
    
    async def get_unused_indexes(self) -> List[IndexInfo]:
        """Find indexes that are never used"""
        all_indexes = await self.get_all_indexes()
        return [idx for idx in all_indexes if idx.scans == 0 and not idx.is_primary]
    
    async def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow queries that might benefit from additional indexes"""
        query = """
        SELECT 
            query,
            calls,
            total_exec_time,
            mean_exec_time,
            rows
        FROM pg_stat_statements
        WHERE mean_exec_time > 100  -- Queries taking more than 100ms on average
        ORDER BY mean_exec_time DESC
        LIMIT 20
        """
        
        try:
            async with await self.get_session() as session:
                result = await session.execute(text(query))
                return [dict(row._mapping) for row in result.fetchall()]
        except Exception:
            # pg_stat_statements might not be available
            return []
    
    async def get_missing_index_recommendations(self) -> List[MissingIndex]:
        """Analyze query patterns to recommend missing indexes"""
        recommendations = []
        
        # Check for common patterns that need indexes
        
        # 1. Foreign key columns
        fk_query = """
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema = 'public'
        """
        
        async with await self.get_session() as session:
            result = await session.execute(text(fk_query))
            foreign_keys = result.fetchall()
        
        # Check if foreign key columns have indexes
        all_indexes = await self.get_all_indexes()
        indexed_columns = defaultdict(set)
        
        for idx in all_indexes:
            for col in idx.columns:
                indexed_columns[f"{idx.table}.{col}"].add(idx.index_name)
        
        for fk in foreign_keys:
            table_col = f"{fk.table_name}.{fk.column_name}"
            if table_col not in indexed_columns:
                recommendations.append(MissingIndex(
                    table=fk.table_name,
                    columns=[fk.column_name],
                    query_type="Foreign Key",
                    estimated_benefit="High - Improves join performance",
                    query_sample=f"SELECT * FROM {fk.table_name} WHERE {fk.column_name} = ?"
                ))
        
        # 2. Check for WHERE clause patterns
        # This would require query log analysis in a real implementation
        
        return recommendations
    
    async def get_index_size_analysis(self) -> Dict[str, Any]:
        """Analyze index sizes and suggest optimizations"""
        all_indexes = await self.get_all_indexes()
        
        total_size = sum(idx.size_mb for idx in all_indexes)
        unused_size = sum(idx.size_mb for idx in all_indexes if idx.scans == 0 and not idx.is_primary)
        
        # Find largest indexes
        largest_indexes = sorted(all_indexes, key=lambda x: x.size_mb, reverse=True)[:10]
        
        # Find most used indexes
        most_used_indexes = sorted(all_indexes, key=lambda x: x.scans, reverse=True)[:10]
        
        return {
            'total_size_mb': total_size,
            'unused_size_mb': unused_size,
            'wasted_percentage': (unused_size / total_size * 100) if total_size > 0 else 0,
            'largest_indexes': [
                {
                    'table': idx.table,
                    'index': idx.index_name,
                    'size_mb': idx.size_mb,
                    'scans': idx.scans
                }
                for idx in largest_indexes
            ],
            'most_used_indexes': [
                {
                    'table': idx.table,
                    'index': idx.index_name,
                    'scans': idx.scans,
                    'size_mb': idx.size_mb
                }
                for idx in most_used_indexes
            ]
        }
    
    async def get_query_performance_insights(self) -> List[Dict[str, Any]]:
        """Get insights about query performance patterns"""
        insights = []
        
        # Check for sequential scans
        seq_scan_query = """
        SELECT 
            schemaname,
            relname as tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            n_tup_ins + n_tup_upd + n_tup_del as total_writes
        FROM pg_stat_user_tables
        WHERE seq_scan > 1000  -- Tables with many sequential scans
        ORDER BY seq_scan DESC
        LIMIT 10
        """
        
        async with await self.get_session() as session:
            result = await session.execute(text(seq_scan_query))
            seq_scans = result.fetchall()
        
        for scan in seq_scans:
            scan_ratio = scan.seq_scan / (scan.seq_scan + scan.idx_scan) if (scan.seq_scan + scan.idx_scan) > 0 else 1
            
            if scan_ratio > 0.5:  # More than 50% sequential scans
                insights.append({
                    'type': 'high_sequential_scans',
                    'table': scan.tablename,
                    'seq_scans': scan.seq_scan,
                    'idx_scans': scan.idx_scan,
                    'scan_ratio': scan_ratio,
                    'recommendation': f"Consider adding indexes to {scan.tablename} table to reduce sequential scans"
                })
        
        # Check for tables with high dead tuple ratios
        dead_tuple_query = """
        SELECT 
            schemaname,
            relname as tablename,
            n_dead_tup,
            n_live_tup,
            ROUND((n_dead_tup::numeric / GREATEST(n_dead_tup + n_live_tup, 1)) * 100, 2) as dead_percentage
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000
        ORDER BY dead_percentage DESC
        LIMIT 10
        """
        
        async with await self.get_session() as session:
            result = await session.execute(text(dead_tuple_query))
            dead_tuples = result.fetchall()
        
        for dead in dead_tuples:
            if dead.dead_percentage > 20:  # More than 20% dead tuples
                insights.append({
                    'type': 'high_dead_tuples',
                    'table': dead.tablename,
                    'dead_percentage': dead.dead_percentage,
                    'dead_tuples': dead.n_dead_tup,
                    'live_tuples': dead.n_live_tup,
                    'recommendation': f"Consider running VACUUM on {dead.tablename} table"
                })
        
        return insights
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive index analysis report"""
        print("🔍 Analyzing database indexes...")
        
        all_indexes = await self.get_all_indexes()
        unused_indexes = await self.get_unused_indexes()
        missing_indexes = await self.get_missing_index_recommendations()
        size_analysis = await self.get_index_size_analysis()
        performance_insights = await self.get_query_performance_insights()
        slow_queries = await self.get_slow_queries()
        
        return {
            'summary': {
                'total_indexes': len(all_indexes),
                'unused_indexes': len(unused_indexes),
                'total_size_mb': size_analysis['total_size_mb'],
                'unused_size_mb': size_analysis['unused_size_mb'],
                'wasted_percentage': size_analysis['wasted_percentage']
            },
            'unused_indexes': [
                {
                    'table': idx.table,
                    'index_name': idx.index_name,
                    'size_mb': idx.size_mb,
                    'columns': idx.columns
                }
                for idx in unused_indexes
            ],
            'missing_indexes': [
                {
                    'table': idx.table,
                    'columns': idx.columns,
                    'query_type': idx.query_type,
                    'estimated_benefit': idx.estimated_benefit,
                    'query_sample': idx.query_sample
                }
                for idx in missing_indexes
            ],
            'size_analysis': size_analysis,
            'performance_insights': performance_insights,
            'slow_queries': slow_queries
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted analysis report"""
        print("=" * 80)
        print("📊 WORKINGTIME DATABASE INDEX ANALYSIS REPORT")
        print("=" * 80)
        
        summary = report['summary']
        print(f"\n📋 SUMMARY:")
        print(f"   Total Indexes: {summary['total_indexes']}")
        print(f"   Unused Indexes: {summary['unused_indexes']}")
        print(f"   Total Size: {summary['total_size_mb']:.2f} MB")
        print(f"   Unused Size: {summary['unused_size_mb']:.2f} MB")
        print(f"   Wasted Space: {summary['wasted_percentage']:.1f}%")
        
        if report['unused_indexes']:
            print(f"\n⚠️  UNUSED INDEXES ({len(report['unused_indexes'])}):")
            print("-" * 40)
            for idx in report['unused_indexes'][:10]:  # Show top 10
                print(f"   📎 {idx['index_name']} ({idx['table']})")
                print(f"      Size: {idx['size_mb']:.2f} MB")
                print(f"      Columns: {', '.join(idx['columns'])}")
                print()
        
        if report['missing_indexes']:
            print(f"\n💡 RECOMMENDED INDEXES ({len(report['missing_indexes'])}):")
            print("-" * 40)
            for idx in report['missing_indexes'][:10]:  # Show top 10
                print(f"   📈 {idx['table']}.({', '.join(idx['columns'])})")
                print(f"      Type: {idx['query_type']}")
                print(f"      Benefit: {idx['estimated_benefit']}")
                print()
        
        if report['performance_insights']:
            print(f"\n🔥 PERFORMANCE INSIGHTS ({len(report['performance_insights'])}):")
            print("-" * 40)
            for insight in report['performance_insights']:
                if insight['type'] == 'high_sequential_scans':
                    print(f"   📊 Table '{insight['table']}' has {insight['scan_ratio']:.1%} sequential scans")
                    print(f"      {insight['recommendation']}")
                elif insight['type'] == 'high_dead_tuples':
                    print(f"   🧹 Table '{insight['table']}' has {insight['dead_percentage']}% dead tuples")
                    print(f"      {insight['recommendation']}")
                print()
        
        # Show largest indexes
        size_analysis = report['size_analysis']
        if size_analysis['largest_indexes']:
            print(f"\n📏 LARGEST INDEXES:")
            print("-" * 40)
            for idx in size_analysis['largest_indexes'][:5]:
                print(f"   📦 {idx['index']} ({idx['table']})")
                print(f"      Size: {idx['size_mb']:.2f} MB")
                print(f"      Scans: {idx['scans']}")
                print()
        
        # Show most used indexes
        if size_analysis['most_used_indexes']:
            print(f"\n🏆 MOST USED INDEXES:")
            print("-" * 40)
            for idx in size_analysis['most_used_indexes'][:5]:
                print(f"   🎯 {idx['index']} ({idx['table']})")
                print(f"      Scans: {idx['scans']}")
                print(f"      Size: {idx['size_mb']:.2f} MB")
                print()
        
        # Generate SQL commands for cleanup
        if report['unused_indexes']:
            print(f"\n🧹 CLEANUP SQL COMMANDS:")
            print("-" * 40)
            print("-- WARNING: Review carefully before executing!")
            print("-- Some indexes might be used rarely but still important")
            for idx in report['unused_indexes']:
                print(f"DROP INDEX CONCURRENTLY IF EXISTS {idx['index_name']};")
        
        # Generate SQL commands for missing indexes
        if report['missing_indexes']:
            print(f"\n🆕 CREATE INDEX SQL COMMANDS:")
            print("-" * 40)
            for idx in report['missing_indexes']:
                columns_str = ', '.join(idx['columns'])
                print(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS ")
                print(f"idx_{idx['table']}_{'_'.join(idx['columns'])} ")
                print(f"ON {idx['table']} ({columns_str});")
                print()

async def main():
    """Main function to run index analysis"""
    analyzer = IndexAnalyzer()
    
    try:
        # Generate comprehensive report
        report = await analyzer.generate_report()
        
        # Print formatted report
        analyzer.print_report(report)
        
        print(f"\n✅ Index analysis completed!")
        
        # Save report to file
        import json
        report_file = "index_analysis_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"📄 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during index analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
