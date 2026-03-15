"""
Optimized DataLoader Implementation
Comprehensive batch loading for GraphQL N+1 problem resolution
"""

import asyncio
from collections import defaultdict
from typing import List, Dict, Any, Optional, Type, Union
from datetime import datetime, date, time
from decimal import Decimal

from strawberry.dataloader import DataLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select, 
    and_, 
    or_, 
    func, 
    text,
    desc,
    asc,
    extract
)
from sqlalchemy.orm import selectinload, joinedload

from backend.database.models import (
    User, Role, TimeLog, WorkSchedule, Shift, LeaveRequest, 
    Payslip, Payroll, Bonus, Notification, Department, Company,
    Position, LeaveBalance, UserSession, AuditLog, PublicHoliday
)

# Type aliases for better readability
ModelType = Type[Any]
KeyType = Union[int, str, tuple]
ResultType = Any

class OptimizedDataLoader:
    """Base class for optimized data loaders with caching and batching"""
    
    def __init__(self, session: AsyncSession, max_batch_size: int = 1000):
        self.session = session
        self.max_batch_size = max_batch_size
        self._cache: Dict[KeyType, Any] = {}
        self._cache_enabled = True
    
    def enable_cache(self, enabled: bool = True) -> None:
        """Enable or disable caching"""
        self._cache_enabled = enabled
        if not enabled:
            self._cache.clear()
    
    def get_from_cache(self, key: KeyType) -> Optional[Any]:
        """Get value from cache if enabled"""
        if self._cache_enabled:
            return self._cache.get(key)
        return None
    
    def set_cache(self, key: KeyType, value: Any) -> None:
        """Set value in cache if enabled"""
        if self._cache_enabled:
            self._cache[key] = value
    
    async def batch_load(self, keys: List[KeyType]) -> List[Optional[Any]]:
        """Override this method in subclasses"""
        raise NotImplementedError

class UserDataLoader(OptimizedDataLoader):
    """Optimized user data loader with comprehensive relationship loading"""
    
    async def load_users_by_ids(self, keys: List[int]) -> List[Optional[User]]:
        """Load users by IDs with all necessary relationships"""
        if not keys:
            return []
        
        # Check cache first
        cached_results = [self.get_from_cache(key) for key in keys]
        uncached_keys = [key for key in keys if not self.get_from_cache(key)]
        
        if not uncached_keys:
            return cached_results
        
        # Batch query with all necessary relationships
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.company_rel),
                selectinload(User.department_rel),
                selectinload(User.position_rel),
                selectinload(User.timelogs).limit(10),  # Limit recent timelogs
                selectinload(User.schedules).limit(10),  # Limit recent schedules
                selectinload(User.leave_requests).limit(10),  # Limit recent requests
            )
            .where(User.id.in_(uncached_keys))
        )
        
        users = result.scalars().unique().all()
        user_map = {int(user.id): user for user in users}
        
        # Update cache
        for key in uncached_keys:
            self.set_cache(int(key), user_map.get(int(key)))
        
        # Return results in original order
        return [user_map.get(int(key)) for key in keys]

class TimeLogDataLoader(OptimizedDataLoader):
    """Optimized time log data loader with date range support"""
    
    async def load_timelogs_by_user_date(
        self, 
        keys: List[tuple[int, date, date]]
    ) -> List[List[TimeLog]]:
        """
        Load time logs for multiple users within date ranges
        keys: List of (user_id, start_date, end_date) tuples
        """
        if not keys:
            return []
        
        results = []
        
        # Process in batches to avoid large queries
        for i in range(0, len(keys), self.max_batch_size):
            batch_keys = keys[i:i + self.max_batch_size]
            
            # Build complex query for date ranges
            conditions = []
            for user_id, start_date, end_date in batch_keys:
                conditions.append(
                    and_(
                        TimeLog.user_id == user_id,
                        TimeLog.start_time >= datetime.combine(start_date, datetime.min.time()),
                        TimeLog.start_time <= datetime.combine(end_date, datetime.max.time())
                    )
                )
            
            # Combine all conditions with OR
            query = select(TimeLog).where(or_(*conditions)).order_by(TimeLog.user_id, TimeLog.start_time)
            
            result = await self.session.execute(query)
            timelogs = result.scalars().all()
            
            # Group by user
            user_timelogs = defaultdict(list)
            for log in timelogs:
                user_timelogs[log.user_id].append(log)
            
            # Return results for each key
            for user_id, start_date, end_date in batch_keys:
                user_logs = [
                    log for log in user_timelogs[user_id]
                    if start_date <= log.start_time.date() <= end_date
                ]
                results.append(user_logs)
        
        return results
    
    async def load_active_timelogs(self, user_ids: List[int]) -> List[Optional[TimeLog]]:
        """Load currently active time logs for users"""
        if not user_ids:
            return []
        
        result = await self.session.execute(
            select(TimeLog)
            .where(
                and_(
                    TimeLog.user_id.in_(user_ids),
                    TimeLog.end_time.is_(None)
                )
            )
            .order_by(TimeLog.start_time.desc())
        )
        
        timelogs = result.scalars().all()
        timelog_map = defaultdict(list)
        
        for log in timelogs:
            timelog_map[log.user_id].append(log)
        
        # Return only the most recent active timelog for each user
        return [timelog_map[user_id][0] if timelog_map[user_id] else None for user_id in user_ids]

class WorkScheduleDataLoader(OptimizedDataLoader):
    """Optimized work schedule data loader"""
    
    async def load_schedules_by_users_date(
        self, 
        keys: List[tuple[int, date, date]]
    ) -> List[List[WorkSchedule]]:
        """
        Load work schedules for multiple users within date ranges
        keys: List of (user_id, start_date, end_date) tuples
        """
        if not keys:
            return []
        
        results = []
        
        for i in range(0, len(keys), self.max_batch_size):
            batch_keys = keys[i:i + self.max_batch_size]
            
            conditions = []
            for user_id, start_date, end_date in batch_keys:
                conditions.append(
                    and_(
                        WorkSchedule.user_id == user_id,
                        WorkSchedule.date >= start_date,
                        WorkSchedule.date <= end_date
                    )
                )
            
            query = (
                select(WorkSchedule)
                .options(selectinload(WorkSchedule.shift))
                .where(or_(*conditions))
                .order_by(WorkSchedule.user_id, WorkSchedule.date)
            )
            
            result = await self.session.execute(query)
            schedules = result.scalars().all()
            
            user_schedules = defaultdict(list)
            for schedule in schedules:
                user_schedules[schedule.user_id].append(schedule)
            
            for user_id, start_date, end_date in batch_keys:
                user_schedule_list = [
                    s for s in user_schedules[user_id]
                    if start_date <= s.date <= end_date
                ]
                results.append(user_schedule_list)
        
        return results

class LeaveRequestDataLoader(OptimizedDataLoader):
    """Optimized leave request data loader"""
    
    async def load_leaves_by_users_date(
        self, 
        keys: List[tuple[int, date, date]]
    ) -> List[List[LeaveRequest]]:
        """
        Load leave requests for multiple users within date ranges
        keys: List of (user_id, start_date, end_date) tuples
        """
        if not keys:
            return []
        
        results = []
        
        for i in range(0, len(keys), self.max_batch_size):
            batch_keys = keys[i:i + self.max_batch_size]
            
            conditions = []
            for user_id, start_date, end_date in batch_keys:
                # Check for overlapping leave requests
                conditions.append(
                    and_(
                        LeaveRequest.user_id == user_id,
                        LeaveRequest.status == 'approved',
                        or_(
                            and_(LeaveRequest.start_date >= start_date, LeaveRequest.start_date <= end_date),
                            and_(LeaveRequest.end_date >= start_date, LeaveRequest.end_date <= end_date),
                            and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= end_date)
                        )
                    )
                )
            
            query = (
                select(LeaveRequest)
                .where(or_(*conditions))
                .order_by(LeaveRequest.user_id, LeaveRequest.start_date)
            )
            
            result = await self.session.execute(query)
            leaves = result.scalars().all()
            
            user_leaves = defaultdict(list)
            for leave in leaves:
                user_leaves[leave.user_id].append(leave)
            
            for user_id, start_date, end_date in batch_keys:
                user_leave_list = []
                for leave in user_leaves[user_id]:
                    # Check if leave overlaps with the date range
                    if (leave.start_date <= end_date and leave.end_date >= start_date):
                        user_leave_list.append(leave)
                results.append(user_leave_list)
        
        return results
    
    async def load_pending_leaves(self) -> List[LeaveRequest]:
        """Load all pending leave requests"""
        result = await self.session.execute(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.user))
            .where(LeaveRequest.status == 'pending')
            .order_by(LeaveRequest.created_at)
        )
        return list(result.scalars().all())

class PayslipDataLoader(OptimizedDataLoader):
    """Optimized payslip data loader"""
    
    async def load_payslips_by_user_period(
        self, 
        keys: List[tuple[int, date, date]]
    ) -> List[List[Payslip]]:
        """
        Load payslips for multiple users within date ranges
        keys: List of (user_id, period_start, period_end) tuples
        """
        if not keys:
            return []
        
        results = []
        
        for i in range(0, len(keys), self.max_batch_size):
            batch_keys = keys[i:i + self.max_batch_size]
            
            conditions = []
            for user_id, period_start, period_end in batch_keys:
                conditions.append(
                    and_(
                        Payslip.user_id == user_id,
                        Payslip.period_start >= period_start,
                        Payslip.period_end <= period_end
                    )
                )
            
            query = (
                select(Payslip)
                .where(or_(*conditions))
                .order_by(Payslip.user_id, Payslip.period_start.desc())
            )
            
            result = await self.session.execute(query)
            payslips = result.scalars().all()
            
            user_payslips = defaultdict(list)
            for payslip in payslips:
                user_payslips[payslip.user_id].append(payslip)
            
            for user_id, period_start, period_end in batch_keys:
                user_payslip_list = [
                    p for p in user_payslips[user_id]
                    if p.period_start >= period_start and p.period_end <= period_end
                ]
                results.append(user_payslip_list)
        
        return results

class UserPresenceDataLoader(OptimizedDataLoader):
    """Specialized data loader for user presence calculations"""
    
    async def load_presence_data(self, target_date: date) -> Dict[int, Dict[str, Any]]:
        """
        Load all necessary data for user presence calculation in one query
        Returns dictionary keyed by user_id with all presence data
        """
        presence_data = {}
        
        # 1. Load active users with their relationships
        users_result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.company_rel),
                selectinload(User.department_rel),
                selectinload(User.position_rel)
            )
            .where(User.is_active == True)
        )
        users = users_result.scalars().all()
        
        # Initialize presence data for all active users
        for user in users:
            presence_data[user.id] = {
                'user': user,
                'schedule': None,
                'timelogs': [],
                'leave': None
            }
        
        # 2. Load work schedules for the target date
        schedules_result = await self.session.execute(
            select(WorkSchedule)
            .options(selectinload(WorkSchedule.shift))
            .where(WorkSchedule.date == target_date)
        )
        schedules = schedules_result.scalars().all()
        for schedule in schedules:
            if schedule.user_id in presence_data:
                presence_data[schedule.user_id]['schedule'] = schedule
        
        # 3. Load time logs for the target date
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        
        timelogs_result = await self.session.execute(
            select(TimeLog)
            .where(and_(TimeLog.start_time >= start_dt, TimeLog.start_time <= end_dt))
            .order_by(TimeLog.user_id, TimeLog.start_time)
        )
        timelogs = timelogs_result.scalars().all()
        
        for log in timelogs:
            if log.user_id in presence_data:
                presence_data[log.user_id]['timelogs'].append(log)
        
        # 4. Load approved leave requests for the target date
        leaves_result = await self.session.execute(
            select(LeaveRequest)
            .where(
                and_(
                    LeaveRequest.status == 'approved',
                    LeaveRequest.start_date <= target_date,
                    LeaveRequest.end_date >= target_date
                )
            )
        )
        leaves = leaves_result.scalars().all()
        for leave in leaves:
            if leave.user_id in presence_data:
                presence_data[leave.user_id]['leave'] = leave
        
        return presence_data

class DataLoaderFactory:
    """Factory class for creating and managing data loaders"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._loaders: Dict[str, DataLoader] = {}
        self._optimized_loaders: Dict[str, OptimizedDataLoader] = {}
    
    def get_user_loader(self) -> DataLoader:
        """Get user data loader"""
        if 'user' not in self._loaders:
            user_loader = UserDataLoader(self.session)
            self._loaders['user'] = DataLoader(
                load_fn=user_loader.load_users_by_ids,
                max_batch_size=1000
            )
            self._optimized_loaders['user'] = user_loader
        return self._loaders['user']
    
    def get_timelog_loader(self) -> TimeLogDataLoader:
        """Get timelog data loader"""
        if 'timelog' not in self._optimized_loaders:
            self._optimized_loaders['timelog'] = TimeLogDataLoader(self.session)
        return self._optimized_loaders['timelog']
    
    def get_schedule_loader(self) -> WorkScheduleDataLoader:
        """Get work schedule data loader"""
        if 'schedule' not in self._optimized_loaders:
            self._optimized_loaders['schedule'] = WorkScheduleDataLoader(self.session)
        return self._optimized_loaders['schedule']
    
    def get_leave_loader(self) -> LeaveRequestDataLoader:
        """Get leave request data loader"""
        if 'leave' not in self._optimized_loaders:
            self._optimized_loaders['leave'] = LeaveRequestDataLoader(self.session)
        return self._optimized_loaders['leave']
    
    def get_payslip_loader(self) -> PayslipDataLoader:
        """Get payslip data loader"""
        if 'payslip' not in self._optimized_loaders:
            self._optimized_loaders['payslip'] = PayslipDataLoader(self.session)
        return self._optimized_loaders['payslip']
    
    def get_presence_loader(self) -> UserPresenceDataLoader:
        """Get user presence data loader"""
        if 'presence' not in self._optimized_loaders:
            self._optimized_loaders['presence'] = UserPresenceDataLoader(self.session)
        return self._optimized_loaders['presence']
    
    def clear_cache(self) -> None:
        """Clear all data loader caches"""
        for loader in self._optimized_loaders.values():
            loader.enable_cache(False)
            loader.enable_cache(True)
    
    def disable_cache(self) -> None:
        """Disable caching for all loaders"""
        for loader in self._optimized_loaders.values():
            loader.enable_cache(False)
    
    def enable_cache(self) -> None:
        """Enable caching for all loaders"""
        for loader in self._optimized_loaders.values():
            loader.enable_cache(True)

def create_optimized_dataloaders(session: AsyncSession) -> dict:
    """
    Create and return a dictionary of optimized DataLoader instances.
    Each DataLoader is specific to a database session.
    """
    factory = DataLoaderFactory(session)
    
    return {
        "user_by_id": factory.get_user_loader(),
        "timelog_loader": factory.get_timelog_loader(),
        "schedule_loader": factory.get_schedule_loader(),
        "leave_loader": factory.get_leave_loader(),
        "payslip_loader": factory.get_payslip_loader(),
        "presence_loader": factory.get_presence_loader(),
        "factory": factory,
    }

# Backward compatibility function
def create_dataloaders(session: AsyncSession) -> dict:
    """Legacy function for backward compatibility"""
    factory = DataLoaderFactory(session)
    
    return {
        "role_by_id": DataLoader(load_fn=lambda keys: load_roles_by_ids(session, keys)),
        "user_by_id": factory.get_user_loader(),
    }

# Legacy function for role loading
async def load_roles_by_ids(session: AsyncSession, keys: List[int]) -> List[Optional[Role]]:
    """
    Load roles by their IDs from the database.
    This function is maintained for backward compatibility.
    """
    if not keys:
        return []

    result = await session.execute(
        select(Role).filter(Role.id.in_(keys))
    )
    roles = result.scalars().all()

    role_map = {role.id: role for role in roles}
    return [role_map.get(key) for key in keys]

# Export all components
__all__ = [
    'OptimizedDataLoader',
    'UserDataLoader',
    'TimeLogDataLoader', 
    'WorkScheduleDataLoader',
    'LeaveRequestDataLoader',
    'PayslipDataLoader',
    'UserPresenceDataLoader',
    'DataLoaderFactory',
    'create_optimized_dataloaders',
    'create_dataloaders',  # Backward compatibility
    'load_roles_by_ids',    # Backward compatibility
]
