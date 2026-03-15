import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.orm import selectinload

from backend.database.database import AsyncSessionLocal
from backend.database.models import (
    GoogleCalendarAccount, GoogleCalendarSyncSettings, GoogleSyncLog,
    GoogleCalendarEvent, WorkSchedule, TimeLog, LeaveRequest, PublicHoliday
)
from backend.services.google_calendar_service import google_calendar_service

logger = logging.getLogger(__name__)


class GoogleSyncJob:
    def __init__(self):
        self.is_running = False
        self.sync_interval_minutes = 15
        
    async def start_sync_scheduler(self):
        """Start the background sync scheduler"""
        self.is_running = True
        logger.info("Google Calendar sync scheduler started")
        
        while self.is_running:
            try:
                await self.process_all_user_syncs()
                await asyncio.sleep(self.sync_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in sync scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop_sync_scheduler(self):
        """Stop the background sync scheduler"""
        self.is_running = False
        logger.info("Google Calendar sync scheduler stopped")
    
    async def process_all_user_syncs(self):
        """Process sync for all users with Google Calendar integration"""
        async with AsyncSessionLocal() as db:
            # Get all active Google Calendar accounts with settings
            stmt = select(GoogleCalendarAccount).where(
                GoogleCalendarAccount.is_active == True
            ).options(
                selectinload(GoogleCalendarAccount.user),
                selectinload(GoogleCalendarAccount.sync_settings)
            )
            
            result = await db.execute(stmt)
            accounts = result.scalars().all()
            
            for account in accounts:
                try:
                    await self.sync_user_calendar(db, account)
                except Exception as e:
                    logger.error(f"Failed to sync user {account.user_id}: {e}")
    
    async def sync_user_calendar(self, db: AsyncSession, account: GoogleCalendarAccount):
        """Sync calendar for a specific user"""
        if not account.sync_settings:
            logger.info(f"No sync settings for user {account.user_id}")
            return
            
        settings = account.sync_settings
        
        # Check if sync is due based on frequency
        last_sync_time = datetime.now() - timedelta(minutes=settings.sync_frequency_minutes)
        
        # Check for recent successful sync
        recent_sync_query = select(GoogleSyncLog).where(
            and_(
                GoogleSyncLog.user_id == account.user_id,
                GoogleSyncLog.started_at > last_sync_time,
                GoogleSyncLog.status == 'completed'
            )
        ).order_by(GoogleSyncLog.started_at.desc())
        
        recent_sync_result = await db.execute(recent_sync_query)
        if recent_sync_result.scalars().first():
            return  # Skip if recently synced
        
        # Create sync log entry
        sync_log = GoogleSyncLog(
            account_id=account.id,
            sync_type='incremental',
            started_at=datetime.now()
        )
        db.add(sync_log)
        await db.commit()
        await db.refresh(sync_log)
        
        try:
            # Refresh access token if needed
            if account.token_expires_at and datetime.now() >= account.token_expires_at.replace(tzinfo=None):
                token_response = await google_calendar_service.refresh_access_token(account.refresh_token)
                account.access_token = token_response['access_token']
                account.token_expires_at = (datetime.now() + timedelta(seconds=token_response['expires_in'])).replace(tzinfo=None)
                await db.commit()
            
            # Get sync date range
            start_date = datetime.now() - timedelta(days=30)  # Sync last 30 days
            end_date = datetime.now() + timedelta(days=90)    # Sync next 90 days
            
            events_processed = 0
            events_created = 0
            events_updated = 0
            events_deleted = 0
            
            # Sync work schedules
            if settings.sync_work_schedules:
                result = await self.sync_work_schedules(
                    db, account, start_date, end_date, settings.privacy_level
                )
                events_processed += result['processed']
                events_created += result['created']
                events_updated += result['updated']
            
            # Sync time logs
            if settings.sync_time_logs:
                result = await self.sync_time_logs(
                    db, account, start_date, end_date, settings.privacy_level
                )
                events_processed += result['processed']
                events_created += result['created']
                events_updated += result['updated']
            
            # Sync leave requests
            if settings.sync_leave_requests:
                result = await self.sync_leave_requests(
                    db, account, start_date, end_date, settings.privacy_level
                )
                events_processed += result['processed']
                events_created += result['created']
                events_updated += result['updated']
            
            # Sync public holidays
            if settings.sync_public_holidays:
                result = await self.sync_public_holidays(
                    db, account, start_date, end_date, settings.privacy_level
                )
                events_processed += result['processed']
                events_created += result['created']
                events_updated += result['updated']
            
            # Sync from Google if bidirectional
            if settings.sync_direction == 'bidirectional':
                result = await self.sync_from_google(db, account, start_date, end_date)
                events_processed += result['processed']
                events_updated += result['updated']
                events_deleted += result['deleted']
            
            # Update sync log
            sync_log.events_processed = int(events_processed)
            sync_log.events_created = int(events_created)
            sync_log.events_updated = int(events_updated)
            sync_log.events_deleted = int(events_deleted)
            sync_log.completed_at = datetime.now()
            sync_log.status = str('completed')
            
        except Exception as e:
            logger.error(f"Sync failed for user {account.user_id}: {e}")
            sync_log.status = 'failed'
            sync_log.error_details = str(e)
        
        await db.commit()
    
    async def sync_work_schedules(
        self, 
        db: AsyncSession, 
        account: GoogleCalendarAccount,
        start_date: datetime, 
        end_date: datetime,
        privacy_level: str
    ) -> dict:
        """Sync work schedules to Google Calendar"""
        # Get work schedules to sync
        stmt = select(WorkSchedule).where(
            and_(
                WorkSchedule.user_id == account.user_id,
                WorkSchedule.date >= start_date.date(),
                WorkSchedule.date <= end_date.date()
            )
        ).options(
            selectinload(WorkSchedule.shift),
            selectinload(WorkSchedule.user)
        )
        
        result = await db.execute(stmt)
        schedules = result.scalars().all()
        
        processed = 0
        created = 0
        updated = 0
        
        for schedule in schedules:
            existing = None
            try:
                # Check if already synced
                existing_event_query = select(GoogleCalendarEvent).where(
                    and_(
                        GoogleCalendarEvent.account_id == account.id,
                        GoogleCalendarEvent.source_type == 'work_schedule',
                        GoogleCalendarEvent.source_id == schedule.id
                    )
                )
                existing_result = await db.execute(existing_event_query)
                existing = existing_result.scalar_one_or_none()
                
                event_data = google_calendar_service.format_work_schedule_event(
                    schedule, schedule.user, privacy_level
                )
                
                if existing:
                    # Update existing event
                    await google_calendar_service.update_event(
                        account.access_token,
                        existing.google_calendar_id,
                        existing.google_event_id,
                        event_data
                    )
                    existing.last_sync_at = datetime.now()
                    existing.sync_status = 'synced'
                    existing.sync_error = ''
                    updated += 1
                else:
                    # Create new event
                    google_event = await google_calendar_service.create_event(
                        account.access_token,
                        account.sync_settings.calendar_id,
                        event_data
                    )
                    
                    new_event = GoogleCalendarEvent(
                        account_id=account.id,
                        google_event_id=google_event['id'],
                        google_calendar_id=account.sync_settings.calendar_id,
                        source_type='work_schedule',
                        source_id=schedule.id,
                        title=event_data['summary'],
                        description=event_data.get('description', ''),
                        start_time=datetime.combine(schedule.date, schedule.shift.start_time),
                        end_time=datetime.combine(schedule.date, schedule.shift.end_time),
                        google_updated_at=datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00')),
                        last_sync_at=datetime.now(),
                        sync_status='synced'
                    )
                    db.add(new_event)
                    created += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to sync schedule {schedule.id}: {e}")
                # Mark as error if existing event
                if existing:
                    existing.sync_status = 'error'
                    existing.sync_error = str(e)
        
        await db.commit()
        return {'processed': processed, 'created': created, 'updated': updated}
    
    async def sync_time_logs(
        self, 
        db: AsyncSession, 
        account: GoogleCalendarAccount,
        start_date: datetime, 
        end_date: datetime,
        privacy_level: str
    ) -> dict:
        """Sync time logs to Google Calendar"""
        stmt = select(TimeLog).where(
            and_(
                TimeLog.user_id == account.user_id,
                TimeLog.start_time >= start_date,
                TimeLog.start_time <= end_date,
                TimeLog.end_time.isnot(None)  # Only completed time logs
            )
        ).options(
            selectinload(TimeLog.user)
        )
        
        result = await db.execute(stmt)
        timelogs = result.scalars().all()
        
        processed = 0
        created = 0
        updated = 0
        
        for timelog in timelogs:
            try:
                # Check if already synced
                existing_event_query = select(GoogleCalendarEvent).where(
                    and_(
                        GoogleCalendarEvent.account_id == account.id,
                        GoogleCalendarEvent.source_type == 'time_log',
                        GoogleCalendarEvent.source_id == timelog.id
                    )
                )
                existing_result = await db.execute(existing_event_query)
                existing = existing_result.scalar_one_or_none()
                
                event_data = google_calendar_service.format_time_log_event(
                    timelog, timelog.user, privacy_level
                )
                
                if existing:
                    # Update existing event
                    await google_calendar_service.update_event(
                        account.access_token,
                        existing.google_calendar_id,
                        existing.google_event_id,
                        event_data
                    )
                    existing.last_sync_at = datetime.now()
                    existing.sync_status = 'synced'
                    updated += 1
                else:
                    # Create new event
                    google_event = await google_calendar_service.create_event(
                        account.access_token,
                        account.sync_settings.calendar_id,
                        event_data
                    )
                    
                    new_event = GoogleCalendarEvent(
                        account_id=account.id,
                        google_event_id=google_event['id'],
                        google_calendar_id=account.sync_settings.calendar_id,
                        source_type='time_log',
                        source_id=timelog.id,
                        title=event_data['summary'],
                        description=event_data.get('description', ''),
                        start_time=timelog.start_time,
                        end_time=timelog.end_time,
                        google_updated_at=datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00')),
                        last_sync_at=datetime.now(),
                        sync_status='synced'
                    )
                    db.add(new_event)
                    created += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to sync timelog {timelog.id}: {e}")
        
        await db.commit()
        return {'processed': processed, 'created': created, 'updated': updated}
    
    async def sync_leave_requests(
        self, 
        db: AsyncSession, 
        account: GoogleCalendarAccount,
        start_date: datetime, 
        end_date: datetime,
        privacy_level: str
    ) -> dict:
        """Sync leave requests to Google Calendar"""
        stmt = select(LeaveRequest).where(
            and_(
                LeaveRequest.user_id == account.user_id,
                LeaveRequest.start_date >= start_date.date(),
                LeaveRequest.end_date <= end_date.date(),
                LeaveRequest.status == 'approved'  # Only approved leaves
            )
        ).options(
            selectinload(LeaveRequest.user)
        )
        
        result = await db.execute(stmt)
        leaves = result.scalars().all()
        
        processed = 0
        created = 0
        updated = 0
        
        for leave in leaves:
            try:
                # Check if already synced
                existing_event_query = select(GoogleCalendarEvent).where(
                    and_(
                        GoogleCalendarEvent.account_id == account.id,
                        GoogleCalendarEvent.source_type == 'leave_request',
                        GoogleCalendarEvent.source_id == leave.id
                    )
                )
                existing_result = await db.execute(existing_event_query)
                existing = existing_result.scalar_one_or_none()
                
                event_data = google_calendar_service.format_leave_request_event(
                    leave, leave.user, privacy_level
                )
                
                if existing:
                    # Update existing event
                    await google_calendar_service.update_event(
                        account.access_token,
                        existing.google_calendar_id,
                        existing.google_event_id,
                        event_data
                    )
                    existing.last_sync_at = datetime.now()
                    existing.sync_status = 'synced'
                    updated += 1
                else:
                    # Create new event
                    google_event = await google_calendar_service.create_event(
                        account.access_token,
                        account.sync_settings.calendar_id,
                        event_data
                    )
                    
                    new_event = GoogleCalendarEvent(
                        account_id=account.id,
                        google_event_id=google_event['id'],
                        google_calendar_id=account.sync_settings.calendar_id,
                        source_type='leave_request',
                        source_id=leave.id,
                        title=event_data['summary'],
                        description=event_data.get('description', ''),
                        start_time=datetime.combine(leave.start_date, datetime.min.time()),
                        end_time=datetime.combine(leave.end_date + timedelta(days=1), datetime.min.time()),
                        is_all_day=True,
                        google_updated_at=datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00')),
                        last_sync_at=datetime.now(),
                        sync_status='synced'
                    )
                    db.add(new_event)
                    created += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to sync leave {leave.id}: {e}")
        
        await db.commit()
        return {'processed': processed, 'created': created, 'updated': updated}
    
    async def sync_public_holidays(
        self, 
        db: AsyncSession, 
        account: GoogleCalendarAccount,
        start_date: datetime, 
        end_date: datetime,
        privacy_level: str
    ) -> dict:
        """Sync public holidays to Google Calendar"""
        stmt = select(PublicHoliday).where(
            and_(
                PublicHoliday.date >= start_date.date(),
                PublicHoliday.date <= end_date.date()
            )
        )
        
        result = await db.execute(stmt)
        holidays = result.scalars().all()
        
        processed = 0
        created = 0
        updated = 0
        
        for holiday in holidays:
            try:
                event_data = {
                    'summary': holiday.name,
                    'description': f"Public Holiday: {holiday.local_name}",
                    'start': {
                        'date': holiday.date.isoformat()
                    },
                    'end': {
                        'date': (holiday.date + timedelta(days=1)).isoformat()
                    },
                    'extendedProperties': {
                        'private': {
                            'source': 'chronos_worktime',
                            'source_type': 'public_holiday',
                            'source_id': str(holiday.id)
                        }
                    },
                    'colorId': '8',  # Gray for holidays
                    'transparency': 'opaque'
                }
                
                # Check if already synced
                existing_event_query = select(GoogleCalendarEvent).where(
                    and_(
                        GoogleCalendarEvent.account_id == account.id,
                        GoogleCalendarEvent.source_type == 'public_holiday',
                        GoogleCalendarEvent.source_id == holiday.id
                    )
                )
                existing_result = await db.execute(existing_event_query)
                existing = existing_result.scalar_one_or_none()
                
                if existing:
                    # Update existing event
                    await google_calendar_service.update_event(
                        account.access_token,
                        existing.google_calendar_id,
                        existing.google_event_id,
                        event_data
                    )
                    existing.last_sync_at = datetime.now()
                    existing.sync_status = 'synced'
                    updated += 1
                else:
                    # Create new event
                    google_event = await google_calendar_service.create_event(
                        account.access_token,
                        account.sync_settings.calendar_id,
                        event_data
                    )
                    
                    new_event = GoogleCalendarEvent(
                        account_id=account.id,
                        google_event_id=google_event['id'],
                        google_calendar_id=account.sync_settings.calendar_id,
                        source_type='public_holiday',
                        source_id=holiday.id,
                        title=event_data['summary'],
                        description=event_data.get('description', ''),
                        start_time=datetime.combine(holiday.date, datetime.min.time()),
                        end_time=datetime.combine(holiday.date + timedelta(days=1), datetime.min.time()),
                        is_all_day=True,
                        google_updated_at=datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00')),
                        last_sync_at=datetime.now(),
                        sync_status='synced'
                    )
                    db.add(new_event)
                    created += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to sync holiday {holiday.id}: {e}")
        
        await db.commit()
        return {'processed': processed, 'created': created, 'updated': updated}
    
    async def sync_from_google(
        self, 
        db: AsyncSession, 
        account: GoogleCalendarAccount,
        start_date: datetime, 
        end_date: datetime
    ) -> dict:
        """Sync events from Google Calendar to local system"""
        try:
            # Get events from Google Calendar
            google_events = await google_calendar_service.list_events(
                account.access_token,
                account.sync_settings.calendar_id,
                start_date,
                end_date
            )
            
            processed = 0
            updated = 0
            deleted = 0
            
            for google_event in google_events:
                # Check if it's a chronos event
                private_props = google_event.get('extendedProperties', {}).get('private', {})
                
                if private_props.get('source') == 'chronos_worktime':
                    # This is our own event, check for updates
                    existing_event_query = select(GoogleCalendarEvent).where(
                        and_(
                            GoogleCalendarEvent.account_id == account.id,
                            GoogleCalendarEvent.google_event_id == google_event['id']
                        )
                    )
                    existing_result = await db.execute(existing_event_query)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        # Check if Google event is newer
                        google_updated = datetime.fromisoformat(google_event['updated'].replace('Z', '+00:00'))
                        if google_updated > existing.last_sync_at:
                            # Update local record
                            existing.google_updated_at = google_event['updated']
                            existing.last_sync_at = datetime.now()
                            updated += 1
                    processed += 1
            
            # Find events that were deleted in Google
            local_events_query = select(GoogleCalendarEvent).where(
                and_(
                    GoogleCalendarEvent.account_id == account.id,
                    GoogleCalendarEvent.last_sync_at < datetime.now() - timedelta(days=1)
                )
            )
            local_events_result = await db.execute(local_events_query)
            local_events = local_events_result.scalars().all()
            
            for local_event in local_events:
                # Check if still exists in Google
                google_event_exists = False
                for google_event in google_events:
                    if google_event['id'] == local_event.google_event_id:
                        google_event_exists = True
                        break
                
                if not google_event_exists:
                    # Mark as deleted
                    local_event.sync_status = 'deleted'
                    deleted += 1
            
            await db.commit()
            return {'processed': processed, 'updated': updated, 'deleted': deleted}
            
        except Exception as e:
            logger.error(f"Failed to sync from Google for user {account.user_id}: {e}")
            return {'processed': 0, 'updated': 0, 'deleted': 0}


# Global sync job instance
google_sync_job = GoogleSyncJob()