#!/usr/bin/env python3
"""
WorkingTime Database Health Monitoring Script

This script provides comprehensive database health monitoring, including
connection pool status, query performance, table statistics, and system metrics.
"""

import asyncio
import sys
import os
import time
import argparse
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database.database_optimized import db_config

@dataclass
class HealthMetric:
    """Data class for health metrics"""
    name: str
    value: Any
    unit: str
    status: str  # 'good', 'warning', 'critical'
    threshold: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

@dataclass
class HealthCheckResult:
    """Data class for health check results"""
    overall_status: str
    checks: List[HealthMetric]
    timestamp: datetime
    database_connected: bool

class DatabaseHealthMonitor:
    """Comprehensive database health monitoring tool"""
    
    def __init__(self):
        from backend.database.database_optimized import db_config
        self.db_config = db_config
        self.warning_threshold = 0.8
        self.critical_threshold = 0.9
    
    @property
    def session(self):
        """Get database session context manager"""
        return self.db_config.get_session()
    
    def evaluate_metric(self, value: float, thresholds: Dict[str, float]) -> str:
        """Evaluate metric value against thresholds"""
        if 'critical' in thresholds and value >= thresholds['critical']:
            return 'critical'
        elif 'warning' in thresholds and value >= thresholds['warning']:
            return 'warning'
        else:
            return 'good'
    
    async def check_connection_pool(self) -> List[HealthMetric]:
        """Check connection pool health"""
        metrics = []
        
        try:
            pool_stats = await self.db_config.get_connection_pool_stats()
            
            # Connection pool utilization
            total_connections = pool_stats.get('total_connections', 0)
            active_connections = pool_stats.get('checked_out', 0)
            
            if total_connections > 0:
                utilization = active_connections / total_connections
                status = self.evaluate_metric(utilization, {
                    'warning': self.warning_threshold,
                    'critical': self.critical_threshold
                })
                
                metrics.append(HealthMetric(
                    name="Connection Pool Utilization",
                    value=f"{utilization:.1%}",
                    unit="percentage",
                    status=status,
                    threshold={'warning': self.warning_threshold, 'critical': self.critical_threshold},
                    description=f"Active: {active_connections}/{total_connections}"
                ))
            
            # Overflow connections
            overflow = pool_stats.get('overflow', 0)
            overflow_status = 'critical' if overflow > 5 else ('warning' if overflow > 0 else 'good')
            
            metrics.append(HealthMetric(
                name="Overflow Connections",
                value=overflow,
                unit="connections",
                status=overflow_status,
                threshold={'warning': 0, 'critical': 5},
                description="Number of connections exceeding pool size"
            ))
            
            # Invalid connections (may not exist in all pool types)
            invalid = pool_stats.get('invalid', 0)
            if invalid > 0:  # Only add if invalid connections exist
                invalid_status = 'critical' if invalid > 2 else ('warning' if invalid > 0 else 'good')
                
                metrics.append(HealthMetric(
                    name="Invalid Connections",
                    value=invalid,
                    unit="connections",
                    status=invalid_status,
                    threshold={'warning': 0, 'critical': 2},
                    description="Number of invalid connections in pool"
                ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                name="Connection Pool Status",
                value=f"Error: {str(e)}",
                unit="status",
                status="critical",
                description="Unable to retrieve connection pool statistics"
            ))
        
        return metrics
    
    async def check_database_size(self) -> List[HealthMetric]:
        """Check database size and growth"""
        metrics = []
        
        try:
            async with self.session as session:
                # Get database size
                result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """))
                db_size = result.fetchone()
                
                metrics.append(HealthMetric(
                    name="Database Size",
                    value=db_size.size,
                    unit="bytes",
                    status="good",
                    description=f"Current database size: {db_size.size}"
                ))
                
                # Get table sizes
                result = await session.execute(text("""
                    SELECT 
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                    LIMIT 10
                """))
                large_tables = result.fetchall()
                
                # Check for unusually large tables
                total_size = sum(row.size_bytes for row in large_tables)
                avg_table_size = total_size / len(large_tables) if large_tables else 0
                
                for table in large_tables:
                    if table.size_bytes > avg_table_size * 3:  # More than 3x average
                        metrics.append(HealthMetric(
                            name=f"Large Table: {table.tablename}",
                            value=table.size,
                            unit="bytes",
                            status="warning",
                            description=f"Table {table.tablename} is unusually large"
                        ))
                
        except Exception as e:
            metrics.append(HealthMetric(
                name="Database Size Check",
                value=f"Error: {str(e)}",
                unit="status",
                status="critical",
                description="Unable to retrieve database size information"
            ))
        
        return metrics
    
    async def check_query_performance(self) -> List[HealthMetric]:
        """Check query performance metrics"""
        metrics = []
        
        try:
            async with self.session as session:
                # Check for long-running queries
                result = await session.execute(text("""
                    SELECT 
                        pid,
                        now() - pg_stat_activity.query_start AS duration,
                        query,
                        state
                    FROM pg_stat_activity 
                    WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                    AND state = 'active'
                    AND query NOT LIKE '%pg_stat_activity%'
                """))
                long_queries = result.fetchall()
                
                if long_queries:
                    for query in long_queries:
                        duration_minutes = query.duration.total_seconds() / 60
                        status = 'critical' if duration_minutes > 30 else 'warning'
                        
                        metrics.append(HealthMetric(
                            name="Long Running Query",
                            value=f"{duration_minutes:.1f} min",
                            unit="minutes",
                            status=status,
                            threshold={'warning': 5, 'critical': 30},
                            description=f"PID {query.pid}: {query.query[:100]}..."
                        ))
                else:
                    metrics.append(HealthMetric(
                        name="Long Running Queries",
                        value=0,
                        unit="queries",
                        status="good",
                        description="No queries running longer than 5 minutes"
                    ))
                
                # Check query statistics (if pg_stat_statements is available)
                try:
                    result = await session.execute(text("""
                        SELECT 
                            COUNT(*) as total_queries,
                            SUM(calls) as total_calls,
                            AVG(mean_exec_time) as avg_exec_time
                        FROM pg_stat_statements
                        WHERE calls > 10
                    """))
                    query_stats = result.fetchone()
                    
                    if query_stats and query_stats.avg_exec_time:
                        avg_time_ms = query_stats.avg_exec_time
                        status = self.evaluate_metric(avg_time_ms, {
                            'warning': 100,  # 100ms
                            'critical': 500  # 500ms
                        })
                        
                        metrics.append(HealthMetric(
                            name="Average Query Time",
                            value=f"{avg_time_ms:.1f}",
                            unit="milliseconds",
                            status=status,
                            threshold={'warning': 100, 'critical': 500},
                            description=f"Average execution time across {query_stats.total_calls} calls"
                        ))
                        
                except Exception:
                    # pg_stat_statements not available
                    metrics.append(HealthMetric(
                        name="Query Statistics",
                        value="N/A",
                        unit="status",
                        status="warning",
                        description="pg_stat_statements extension not available"
                    ))
                
        except Exception as e:
            metrics.append(HealthMetric(
                name="Query Performance Check",
                value=f"Error: {str(e)}",
                unit="status",
                status="critical",
                description="Unable to retrieve query performance information"
            ))
        
        return metrics
    
    async def check_table_statistics(self) -> List[HealthMetric]:
        """Check table health statistics"""
        metrics = []
        
        try:
            async with self.session as session:
                # Check for tables needing vacuum
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        relname as tablename,
                        n_live_tup,
                        n_dead_tup,
                        ROUND(((n_dead_tup::float / GREATEST(n_dead_tup + n_live_tup, 1)) * 100)::numeric, 2) as dead_percentage,
                        last_vacuum,
                        last_autovacuum
                    FROM pg_stat_user_tables
                    WHERE n_dead_tup > 1000
                    ORDER BY dead_percentage DESC
                    LIMIT 10
                """))
                vacuum_needed = result.fetchall()
                
                for table in vacuum_needed:
                    # Access by index or attribute name
                    if hasattr(table, 'tablename'):
                        table_name = table.tablename
                        dead_pct = table.dead_percentage
                    else:
                        # Access by index if tuple-like
                        table_name = table[1]  # schemaname, tablename
                        dead_pct = table[4]  # dead_percentage
                    
                    status = 'critical' if dead_pct > 30 else ('warning' if dead_pct > 15 else 'good')
                    
                    metrics.append(HealthMetric(
                        name=f"Dead Tuples: {table_name}",
                        value=f"{dead_pct}%",
                        unit="percentage",
                        status=status,
                        threshold={'warning': 15, 'critical': 30},
                        description=f"Table {table_name}: Dead tuples percentage"
                    ))
                
                # Check for tables needing analyze
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        relname as tablename,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables
                    WHERE (last_analyze IS NULL OR last_analyze < NOW() - INTERVAL '7 days')
                    AND (last_autoanalyze IS NULL OR last_autoanalyze < NOW() - INTERVAL '7 days')
                """))
                analyze_needed = result.fetchall()
                
                for table in analyze_needed:
                    metrics.append(HealthMetric(
                        name=f"Statistics Stale: {table.tablename}",
                        value="Old",
                        unit="status",
                        status="warning",
                        description=f"Table {table.tablename} needs ANALYZE"
                    ))
                
        except Exception as e:
            metrics.append(HealthMetric(
                name="Table Statistics Check",
                value=f"Error: {str(e)}",
                unit="status",
                status="warning",
                description="Unable to retrieve table statistics"
            ))
        
        return metrics
    
    async def check_system_resources(self) -> List[HealthMetric]:
        """Check system-level resources"""
        metrics = []
        
        try:
            async with self.session as session:
                # Check database connections
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_connections,
                        COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                        COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                        COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                    FROM pg_stat_activity
                    WHERE pid != pg_backend_pid()
                """))
                conn_stats = result.fetchone()
                
                total_conn = conn_stats.total_connections
                idle_tx = conn_stats.idle_in_transaction
                
                # Check against max_connections
                result = await session.execute(text("SHOW max_connections"))
                max_conn = int(result.fetchone()[0])
                
                conn_utilization = total_conn / max_conn
                conn_status = self.evaluate_metric(conn_utilization, {
                    'warning': 0.8,
                    'critical': 0.95
                })
                
                metrics.append(HealthMetric(
                    name="Connection Utilization",
                    value=f"{conn_utilization:.1%}",
                    unit="percentage",
                    status=conn_status,
                    threshold={'warning': 0.8, 'critical': 0.95},
                    description=f"{total_conn}/{max_conn} connections"
                ))
                
                if idle_tx > 5:
                    metrics.append(HealthMetric(
                        name="Idle in Transaction",
                        value=idle_tx,
                        unit="connections",
                        status="critical",
                        threshold={'warning': 2, 'critical': 5},
                        description="Many connections idle in transaction"
                    ))
                
                # Check lock waits
                result = await session.execute(text("""
                    SELECT COUNT(*) as blocked_queries
                    FROM pg_stat_activity 
                    WHERE wait_event_type = 'Lock'
                    AND state = 'active'
                """))
                blocked = result.fetchone().blocked_queries
                
                if blocked > 0:
                    block_status = 'critical' if blocked > 10 else ('warning' if blocked > 3 else 'good')
                    metrics.append(HealthMetric(
                        name="Blocked Queries",
                        value=blocked,
                        unit="queries",
                        status=block_status,
                        threshold={'warning': 3, 'critical': 10},
                        description="Queries waiting for locks"
                    ))
                
        except Exception as e:
            metrics.append(HealthMetric(
                name="System Resources Check",
                value=f"Error: {str(e)}",
                unit="status",
                status="critical",
                description="Unable to retrieve system resource information"
            ))
        
        return metrics
    
    async def check_performance_tests(self) -> List[HealthMetric]:
        """Run performance tests and check results"""
        metrics = []
        
        try:
            from backend.database.database_optimized import db_manager
            
            async with db_manager.config.get_session() as session:
                test_queries = [
                    ("Simple Query", "SELECT 1 as test", 0.1),
                    ("User Count", "SELECT COUNT(*) FROM users", 0.5),
                    ("TimeLog Count", "SELECT COUNT(*) FROM timelogs", 1.0),
                    ("Recent TimeLogs", "SELECT * FROM timelogs ORDER BY id DESC LIMIT 100", 1.0),
                ]
                
                for query_name, query, threshold in test_queries:
                    start = time.perf_counter()
                    await session.execute(text(query))
                    exec_time = time.perf_counter() - start
                    
                    status = 'critical' if exec_time > threshold * 2 else ('warning' if exec_time > threshold else 'good')
                    
                    metrics.append(HealthMetric(
                        name=f"Performance: {query_name}",
                        value=f"{exec_time:.3f}s",
                        unit="seconds",
                        status=status,
                        threshold={'warning': threshold, 'critical': threshold * 2},
                        description=f"Query took {exec_time:.3f}s (threshold: {threshold}s)"
                    ))
                
                result = await session.execute(text("SELECT COUNT(*) as slow_count FROM pg_stat_statements WHERE mean_exec_time > 1000"))
                slow_queries = result.fetchone().slow_count
                
                if slow_queries > 0:
                    metrics.append(HealthMetric(
                        name="Slow Queries (pg_stat_statements)",
                        value=slow_queries,
                        unit="queries",
                        status='warning',
                        threshold={'warning': 10, 'critical': 50},
                        description=f"{slow_queries} queries with execution time > 1s"
                    ))
                    
        except Exception as e:
            metrics.append(HealthMetric(
                name="Performance Tests",
                value=f"Error: {str(e)}",
                unit="status",
                status="warning",
                description="Could not run performance tests"
            ))
        
        return metrics
    
    async def run_health_check(self) -> HealthCheckResult:
        """Run comprehensive health check"""
        print("🏥 Running WorkingTime Database Health Check...")
        
        all_checks = []
        database_connected = True
        
        try:
            # Test basic connectivity
            async with self.session as session:
                await session.execute(text("SELECT 1"))
            
            # Run all health checks
            checks = [
                ("Connection Pool", self.check_connection_pool),
                ("Database Size", self.check_database_size),
                ("Query Performance", self.check_query_performance),
                ("Table Statistics", self.check_table_statistics),
                ("System Resources", self.check_system_resources),
                ("Performance Tests", self.check_performance_tests),
            ]
            
            for check_name, check_func in checks:
                try:
                    metrics = await check_func()
                    all_checks.extend(metrics)
                    print(f"   ✅ {check_name} - {len(metrics)} metrics collected")
                except Exception as e:
                    print(f"   ❌ {check_name} - Error: {e}")
                    all_checks.append(HealthMetric(
                        name=f"{check_name} Check",
                        value=f"Error: {str(e)}",
                        unit="status",
                        status="critical"
                    ))
                    database_connected = False
        
        except Exception as e:
            print(f"   ❌ Database Connection Failed - {e}")
            database_connected = False
            all_checks.append(HealthMetric(
                name="Database Connectivity",
                value="Failed",
                unit="status",
                status="critical",
                description="Unable to connect to database"
            ))
        
        # Determine overall status
        critical_count = sum(1 for m in all_checks if m.status == 'critical')
        warning_count = sum(1 for m in all_checks if m.status == 'warning')
        
        if critical_count > 0:
            overall_status = 'critical'
        elif warning_count > 0:
            overall_status = 'warning'
        else:
            overall_status = 'good'
        
        return HealthCheckResult(
            overall_status=overall_status,
            checks=all_checks,
            timestamp=datetime.now(),
            database_connected=database_connected
        )
    
    def print_health_report(self, result: HealthCheckResult):
        """Print formatted health report"""
        print("\n" + "=" * 80)
        print(f"🏥 WORKINGTIME DATABASE HEALTH REPORT")
        print("=" * 80)
        
        # Overall status
        status_icon = {"good": "✅", "warning": "⚠️", "critical": "❌"}[result.overall_status]
        status_text = {"good": "HEALTHY", "warning": "WARNING", "critical": "CRITICAL"}[result.overall_status]
        
        print(f"\n{status_icon} OVERALL STATUS: {status_text}")
        print(f"📅 Checked at: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔌 Database Connected: {'Yes' if result.database_connected else 'No'}")
        
        # Categorize checks by status
        good_checks = [c for c in result.checks if c.status == 'good']
        warning_checks = [c for c in result.checks if c.status == 'warning']
        critical_checks = [c for c in result.checks if c.status == 'critical']
        
        # Print critical issues first
        if critical_checks:
            print(f"\n❌ CRITICAL ISSUES ({len(critical_checks)}):")
            print("-" * 60)
            for check in critical_checks:
                print(f"   🔴 {check.name}: {check.value} {check.unit}")
                if check.description:
                    print(f"      💬 {check.description}")
                if check.threshold:
                    threshold_info = ", ".join([f"{k}: {v}" for k, v in check.threshold.items()])
                    print(f"      📊 Thresholds: {threshold_info}")
                print()
        
        # Print warnings
        if warning_checks:
            print(f"\n⚠️  WARNINGS ({len(warning_checks)}):")
            print("-" * 60)
            for check in warning_checks:
                print(f"   🟡 {check.name}: {check.value} {check.unit}")
                if check.description:
                    print(f"      💬 {check.description}")
                if check.threshold:
                    threshold_info = ", ".join([f"{k}: {v}" for k, v in check.threshold.items()])
                    print(f"      📊 Thresholds: {threshold_info}")
                print()
        
        # Print good checks (summary)
        if good_checks:
            print(f"\n✅ HEALTHY METRICS ({len(good_checks)}):")
            print("-" * 60)
            for check in good_checks[:10]:  # Show first 10
                print(f"   🟢 {check.name}: {check.value} {check.unit}")
            
            if len(good_checks) > 10:
                print(f"   ... and {len(good_checks) - 10} more healthy metrics")
            print()
        
        # Summary statistics
        print(f"\n📊 SUMMARY:")
        print(f"   Total Checks: {len(result.checks)}")
        print(f"   Critical: {len(critical_checks)}")
        print(f"   Warning: {len(warning_checks)}")
        print(f"   Healthy: {len(good_checks)}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 60)
        
        if not result.database_connected:
            print("   🔧 Fix database connection issues immediately")
        
        if critical_checks:
            print("   🚨 Address critical issues immediately")
            
        if warning_checks:
            print("   ⚠️  Monitor warnings and schedule maintenance")
            
        if len(critical_checks) == 0 and len(warning_checks) == 0:
            print("   🎉 All systems healthy! Continue monitoring")
        
        # Connection pool specific recommendations
        pool_checks = [c for c in result.checks if "Connection Pool" in c.name]
        critical_pool = [c for c in pool_checks if c.status == 'critical']
        if critical_pool:
            print("   🔗 Consider increasing connection pool size")
        
        # Performance recommendations
        perf_checks = [c for c in result.checks if "Query" in c.name or "Dead Tuples" in c.name]
        critical_perf = [c for c in perf_checks if c.status == 'critical']
        if critical_perf:
            print("   📈 Consider query optimization and index tuning")

async def run_health_check_once(monitor: 'DatabaseHealthMonitor', output_json: bool = False):
    """Run health check once"""
    result = await monitor.run_health_check()
    
    if output_json:
        report_data = {
            'overall_status': result.overall_status,
            'timestamp': result.timestamp.isoformat(),
            'database_connected': result.database_connected,
            'checks': [asdict(check) for check in result.checks]
        }
        print(json.dumps(report_data, indent=2, default=str))
    else:
        monitor.print_health_report(result)
        
        report_file = f"health_report_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'overall_status': result.overall_status,
                'timestamp': result.timestamp.isoformat(),
                'database_connected': result.database_connected,
                'checks': [asdict(check) for check in result.checks]
            }, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")
    
    return result

async def run_watch_mode(monitor: 'DatabaseHealthMonitor', interval: int, output_json: bool):
    """Run health check in watch mode"""
    print(f"🔄 Starting watch mode (checking every {interval} seconds)...")
    print("Press Ctrl+C to stop\n")
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Stopping watch mode...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        try:
            result = await run_health_check_once(monitor, output_json)
            
            if result.overall_status == 'critical':
                print(f"\n🔴 CRITICAL - Status: {result.overall_status}")
            elif result.overall_status == 'warning':
                print(f"\n🟡 WARNING - Status: {result.overall_status}")
            else:
                print(f"\n🟢 OK - Status: {result.overall_status}")
            
            print(f"\n⏳ Next check in {interval} seconds...")
            await asyncio.sleep(interval)
        except Exception as e:
            print(f"❌ Error in watch mode: {e}")
            await asyncio.sleep(interval)

async def main():
    """Main function to run health check"""
    parser = argparse.ArgumentParser(description='WorkingTime Database Health Monitor')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--watch', action='store_true', help='Run in watch mode (continuous monitoring)')
    parser.add_argument('--interval', type=int, default=60, help='Watch mode interval in seconds (default: 60)')
    parser.add_argument('--no-save', action='store_true', help='Do not save JSON report to file')
    
    args = parser.parse_args()
    
    monitor = DatabaseHealthMonitor()
    
    try:
        if args.watch:
            await run_watch_mode(monitor, args.interval, args.json)
        else:
            result = await run_health_check_once(monitor, args.json)
            
            if not args.json:
                pass
            elif result.overall_status == 'critical':
                sys.exit(2)
            elif result.overall_status == 'warning':
                sys.exit(1)
            else:
                sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error during health check: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())
