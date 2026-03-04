#!/usr/bin/env python3
"""
WorkingTime Database Performance Testing Script

This script provides comprehensive performance testing for database queries,
including N+1 problem detection, index usage analysis, and query optimization validation.
"""

import asyncio
import time
import sys
import os
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_, or_
from backend.database.database_optimized import db_manager
from backend.database.models import User, TimeLog, WorkSchedule, LeaveRequest

@dataclass
class PerformanceMetric:
    """Data class for performance metrics"""
    query_name: str
    execution_time: float
    rows_affected: int
    memory_usage: Optional[float] = None
    cache_hit: Optional[bool] = None
    index_used: Optional[str] = None

@dataclass
class TestResult:
    """Data class for test results"""
    test_name: str
    metrics: List[PerformanceMetric]
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    passed: bool
    threshold: float

class PerformanceTester:
    """Comprehensive database performance testing suite"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.test_results: List[TestResult] = []
        self.session: Optional[AsyncSession] = None
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session for testing"""
        async with self.db_manager.config.get_session() as session:
            yield session
    
    async def run_query_with_timing(self, query: str, params: Dict = None) -> PerformanceMetric:
        """Execute query with performance timing and metrics collection"""
        params = params or {}
        
        start_time = time.perf_counter()
        
        async with self.get_session() as session:
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            execution_time = time.perf_counter() - start_time
            
            return PerformanceMetric(
                query_name=query[:50] + "..." if len(query) > 50 else query,
                execution_time=execution_time,
                rows_affected=len(rows),
                index_used=None
            )
    
    def _extract_index_usage(self, plan_info: Dict) -> Optional[str]:
        """Extract index usage information from execution plan"""
        def find_index_usage(node):
            if isinstance(node, dict):
                if 'Index Name' in node:
                    return node['Index Name']
                if 'Plan' in node:
                    return find_index_usage(node['Plan'])
                if 'Plans' in node:
                    for subplan in node['Plans']:
                        result = find_index_usage(subplan)
                        if result:
                            return result
            return None
        
        return find_index_usage(plan_info.get('Plan', {}))
    
    async def test_user_presence_query(self) -> TestResult:
        """Test the optimized user presence query"""
        test_date = datetime.now().date()
        
        query = """
        SELECT DISTINCT u.id, u.first_name, u.last_name,
               ws.shift_id, ws.date,
               tl.id as timelog_id, tl.start_time, tl.end_time,
               lr.id as leave_id, lr.leave_type, lr.start_date as leave_start, lr.end_date as leave_end
        FROM users u
        LEFT JOIN work_schedules ws ON u.id = ws.user_id AND ws.date = :date
        LEFT JOIN timelogs tl ON u.id = tl.user_id 
                               AND DATE(tl.start_time) = :date
        LEFT JOIN leave_requests lr ON u.id = lr.user_id 
                                   AND lr.status = 'approved'
                                   AND lr.start_date <= :date 
                                   AND lr.end_date >= :date
        WHERE u.is_active = true
        """
        
        metrics = []
        for _ in range(5):  # Run multiple times for statistical significance
            metric = await self.run_query_with_timing(query, {'date': test_date})
            metrics.append(metric)
        
        return self._calculate_test_result("User Presence Query", metrics, threshold=2.0)
    
    async def test_timelog_date_range_query(self) -> TestResult:
        """Test time log date range query with indexing"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        query = """
        SELECT tl.id, tl.user_id, tl.start_time, tl.end_time, u.first_name, u.last_name
        FROM timelogs tl
        JOIN users u ON tl.user_id = u.id
        WHERE tl.start_time >= :start_date 
        AND tl.start_time <= :end_date
        ORDER BY tl.user_id, tl.start_time DESC
        """
        
        metrics = []
        for _ in range(5):
            metric = await self.run_query_with_timing(
                query, 
                {'start_date': start_date, 'end_date': end_date}
            )
            metrics.append(metric)
        
        return self._calculate_test_result("TimeLog Date Range Query", metrics, threshold=1.5)
    
    async def test_leave_requests_query(self) -> TestResult:
        """Test leave requests query with status filtering"""
        query = """
        SELECT lr.id, lr.user_id, lr.start_date, lr.end_date, lr.status, lr.leave_type,
               u.first_name, u.last_name
        FROM leave_requests lr
        JOIN users u ON lr.user_id = u.id
        WHERE lr.status = :status
        ORDER BY lr.created_at DESC
        LIMIT 100
        """
        
        metrics = []
        for _ in range(5):
            metric = await self.run_query_with_timing(query, {'status': 'pending'})
            metrics.append(metric)
        
        return self._calculate_test_result("Leave Requests Status Query", metrics, threshold=0.5)
    
    async def test_work_schedule_query(self) -> TestResult:
        """Test work schedule query with date filtering"""
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)
        
        query = """
        SELECT ws.id, ws.user_id, ws.date, ws.shift_id,
               u.first_name, u.last_name,
               s.name as shift_name, s.start_time as shift_start, s.end_time as shift_end
        FROM work_schedules ws
        JOIN users u ON ws.user_id = u.id
        LEFT JOIN shifts s ON ws.shift_id = s.id
        WHERE ws.date BETWEEN :start_date AND :end_date
        ORDER BY ws.date, u.first_name
        """
        
        metrics = []
        for _ in range(5):
            metric = await self.run_query_with_timing(
                query,
                {'start_date': start_date, 'end_date': end_date}
            )
            metrics.append(metric)
        
        return self._calculate_test_result("Work Schedule Date Range Query", metrics, threshold=0.5)
    
    async def test_payslip_aggregation_query(self) -> TestResult:
        """Test payslip aggregation query for management stats"""
        query = """
        SELECT 
            to_char(period_start, 'YYYY-MM') as month,
            SUM(total_amount) as total_payroll,
            SUM(overtime_amount) as total_overtime,
            COUNT(*) as payslip_count
        FROM payslips
        WHERE period_start >= NOW() - INTERVAL '12 months'
        GROUP BY to_char(period_start, 'YYYY-MM')
        ORDER BY month DESC
        """
        
        metrics = []
        for _ in range(5):
            metric = await self.run_query_with_timing(query)
            metrics.append(metric)
        
        return self._calculate_test_result("Payslip Aggregation Query", metrics, threshold=1.0)
    
    async def test_n1_problem_detection(self) -> TestResult:
        """Test for N+1 query problems"""
        # This simulates a bad N+1 query pattern
        user_ids_query = "SELECT id FROM users WHERE is_active = true LIMIT 10"
        
        async with self.get_session() as session:
            # Get user IDs
            result = await session.execute(text(user_ids_query))
            user_ids = [row[0] for row in result.fetchall()]
        
        total_time = 0
        queries_executed = 0
        
        for user_id in user_ids:
            # Simulate individual queries for each user (N+1 problem)
            query = """
            SELECT tl.id, tl.start_time, tl.end_time 
            FROM timelogs tl 
            WHERE tl.user_id = :user_id 
            ORDER BY tl.start_time DESC 
            LIMIT 5
            """
            
            metric = await self.run_query_with_timing(query, {'user_id': user_id})
            total_time += metric.execution_time
            queries_executed += 1
        
        # Now test the optimized batch version
        batch_query = """
        SELECT tl.id, tl.user_id, tl.start_time, tl.end_time 
        FROM timelogs tl 
        WHERE tl.user_id = ANY(:user_ids)
        ORDER BY tl.user_id, tl.start_time DESC
        """
        
        batch_metric = await self.run_query_with_timing(
            batch_query, 
            {'user_ids': user_ids}
        )
        
        metrics = [
            PerformanceMetric(
                query_name="N+1 Individual Queries",
                execution_time=total_time,
                rows_affected=queries_executed
            ),
            PerformanceMetric(
                query_name="Optimized Batch Query",
                execution_time=batch_metric.execution_time,
                rows_affected=batch_metric.rows_affected
            )
        ]
        
        return self._calculate_test_result("N+1 Problem Detection", metrics, threshold=1.0)
    
    def _calculate_test_result(self, test_name: str, metrics: List[PerformanceMetric], threshold: float) -> TestResult:
        """Calculate test statistics and determine if test passed"""
        if not metrics:
            return TestResult(
                test_name=test_name,
                metrics=[],
                avg_time=0,
                min_time=0,
                max_time=0,
                std_dev=0,
                passed=False,
                threshold=threshold
            )
        
        times = [m.execution_time for m in metrics]
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        passed = avg_time <= threshold
        
        return TestResult(
            test_name=test_name,
            metrics=metrics,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            passed=passed,
            threshold=threshold
        )
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all performance tests"""
        print("🚀 Starting WorkingTime Database Performance Tests\n")
        
        tests = [
            ("User Presence Query", self.test_user_presence_query),
            ("TimeLog Date Range Query", self.test_timelog_date_range_query),
            ("Leave Requests Query", self.test_leave_requests_query),
            ("Work Schedule Query", self.test_work_schedule_query),
            ("Payslip Aggregation Query", self.test_payslip_aggregation_query),
            ("N+1 Problem Detection", self.test_n1_problem_detection),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"⏱️  Running {test_name}...")
            try:
                result = await test_func()
                results.append(result)
                
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                print(f"   {status} - Avg: {result.avg_time:.3f}s (Threshold: {result.threshold}s)")
                
                if result.metrics and len(result.metrics) > 0 and result.metrics[0].index_used:
                    print(f"   📊 Index used: {result.metrics[0].index_used}")
                
            except Exception as e:
                print(f"   ❌ ERROR - {str(e)[:100]}")
                results.append(TestResult(
                    test_name=test_name,
                    metrics=[],
                    avg_time=0,
                    min_time=0,
                    max_time=0,
                    std_dev=0,
                    passed=False,
                    threshold=0
                ))
            
            print()
        
        self.test_results = results
        return results
    
    def print_summary(self):
        """Print test summary"""
        if not self.test_results:
            print("No test results available")
            return
        
        passed = sum(1 for r in self.test_results if r.passed)
        total = len(self.test_results)
        
        print("=" * 80)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        print("Detailed Results:")
        print("-" * 80)
        for result in self.test_results:
            status = "✅" if result.passed else "❌"
            print(f"{status} {result.test_name}")
            print(f"   Avg Time: {result.avg_time:.3f}s")
            print(f"   Range: {result.min_time:.3f}s - {result.max_time:.3f}s")
            print(f"   Std Dev: {result.std_dev:.3f}s")
            print(f"   Threshold: {result.threshold}s")
            print()
    
    async def check_index_usage(self) -> Dict[str, Any]:
        """Check index usage statistics"""
        query = """
        SELECT 
            schemaname,
            relname as table_name,
            indexrelname as index_name,
            idx_tup_read,
            idx_tup_fetch,
            idx_scan
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan DESC
        """
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query))
                indexes = result.fetchall()
            
            return {
                'total_indexes': len(indexes),
                'unused_indexes': len([i for i in indexes if i.idx_scan == 0]),
                'most_used': [
                    {
                        'index_name': i.index_name,
                        'table_name': i.table_name,
                        'scans': i.idx_scan,
                        'tuples_read': i.idx_tup_read
                    }
                    for i in indexes[:10] if i.index_name
                ]
            }
        except Exception as e:
            return {
                'total_indexes': 0,
                'unused_indexes': 0,
                'most_used': [],
                'error': str(e)
            }
    
    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        try:
            return await self.db_manager.get_connection_pool_stats()
        except Exception as e:
            return {'error': str(e)}

async def main():
    """Main function to run performance tests"""
    tester = PerformanceTester()
    
    try:
        # Run all tests
        await tester.run_all_tests()
        
        # Print summary
        tester.print_summary()
        
        # Additional statistics
        print("\n📈 Index Usage Statistics:")
        print("-" * 40)
        index_stats = await tester.check_index_usage()
        print(f"Total indexes: {index_stats['total_indexes']}")
        print(f"Unused indexes: {index_stats['unused_indexes']}")
        
        print("\n🔗 Connection Pool Statistics:")
        print("-" * 40)
        pool_stats = await tester.get_connection_pool_stats()
        for key, value in pool_stats.items():
            print(f"{key}: {value}")
        
        print("\n✅ Performance testing completed!")
        
    except Exception as e:
        print(f"❌ Error during performance testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
