import httpx
import json
import datetime
import asyncio
from typing import Optional, List, Dict, Any
from datetime import date, datetime as dt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_

from backend.database.models import (
    User, WorkSchedule, TimeLog, LeaveRequest, PublicHoliday, 
    GoogleCalendarAccount, GoogleCalendarSyncSettings, GoogleCalendarEvent, GoogleSyncLog
)
from backend.config import settings


class GoogleCalendarService:
    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        self.redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:3000/auth/google/callback')
        self.base_url = "https://www.googleapis.com/calendar/v3"
        self.auth_uri = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_uri = "https://oauth2.googleapis.com/token"
        
        self.SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
    
    def is_configured(self) -> bool:
        """Check if Google Calendar is configured"""
        return all([self.client_id, self.client_secret])
    
    async def get_auth_url(self, user_id: int, state: str = None) -> str:
        """Generate OAuth 2.0 authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.SCOPES),
            'response_type': 'code',
            'access_type': 'offline',  # For refresh token
            'prompt': 'consent',  # Force consent to get refresh token
            'state': state or f"user_{user_id}"
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_uri}?{param_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_uri, data=data)
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_uri, data=data)
            response.raise_for_status()
            return response.json()
    
    async def get_user_calendar_info(self, access_token: str) -> Dict[str, Any]:
        """Get user's primary calendar information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/users/me/calendarList/primary", headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def create_event(self, access_token: str, calendar_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Google Calendar"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/calendars/{calendar_id}/events",
                headers=headers,
                json=event_data
            )
            response.raise_for_status()
            return response.json()
    
    async def update_event(self, access_token: str, calendar_id: str, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing event in Google Calendar"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/calendars/{calendar_id}/events/{event_id}",
                headers=headers,
                json=event_data
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_event(self, access_token: str, calendar_id: str, event_id: str) -> bool:
        """Delete event from Google Calendar"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/calendars/{calendar_id}/events/{event_id}",
                headers=headers
            )
            return response.status_code == 204
    
    async def list_events(self, access_token: str, calendar_id: str, 
                         start_min: datetime.datetime, start_max: datetime.datetime) -> List[Dict[str, Any]]:
        """List events from Google Calendar within date range"""
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'timeMin': start_min.isoformat(),
            'timeMax': start_max.isoformat(),
            'singleEvents': 'true',
            'orderBy': 'startTime'
        }
        
        all_events = []
        page_token = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                if page_token:
                    params['pageToken'] = page_token
                
                response = await client.get(
                    f"{self.base_url}/calendars/{calendar_id}/events",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                all_events.extend(data.get('items', []))
                
                page_token = data.get('nextPageToken')
                if not page_token:
                    break
        
        return all_events
    
    def format_work_schedule_event(self, schedule: WorkSchedule, user: User, 
                                 privacy_level: str = 'title_only') -> Dict[str, Any]:
        """Convert WorkSchedule to Google Calendar event format"""
        title = f"Work: {schedule.shift.name}"
        description = f"Shift: {schedule.shift.name}\n"
        description += f"Time: {schedule.shift.start_time} - {schedule.shift.end_time}\n"
        description += f"Location: Company Premises"
        
        if privacy_level == 'busy_only':
            title = "Busy"
            description = ""
        elif privacy_level == 'title_only':
            description = f"Shift: {schedule.shift.name}"
        
        start_datetime = datetime.datetime.combine(schedule.date, schedule.shift.start_time)
        end_datetime = datetime.datetime.combine(schedule.date, schedule.shift.end_time)
        
        return {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': getattr(user, 'timezone', 'Europe/Sofia')
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': getattr(user, 'timezone', 'Europe/Sofia')
            },
            'extendedProperties': {
                'private': {
                    'source': 'chronos_worktime',
                    'source_type': 'work_schedule',
                    'source_id': str(schedule.id),
                    'shift_type': schedule.shift.shift_type
                }
            },
            'colorId': self._get_color_for_shift_type(schedule.shift.shift_type),
            'transparency': 'opaque'  # Show as busy
        }
    
    def format_time_log_event(self, timelog: TimeLog, user: User,
                            privacy_level: str = 'title_only') -> Dict[str, Any]:
        """Convert TimeLog to Google Calendar event format"""
        title = "Work Hours" if not timelog.is_manual else "Work Hours (Manual)"
        
        if privacy_level == 'busy_only':
            title = "Busy"
        
        description = ""
        if privacy_level in ['title_only', 'full']:
            description = f"Type: {timelog.type}"
            if timelog.is_manual:
                description += " (Manual Entry)"
            if timelog.break_duration_minutes > 0:
                description += f"\nBreak: {timelog.break_duration_minutes} minutes"
            if timelog.latitude and timelog.longitude:
                description += f"\nLocation: {timelog.latitude}, {timelog.longitude}"
        
        return {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': timelog.start_time.isoformat(),
                'timeZone': getattr(user, 'timezone', 'Europe/Sofia')
            },
            'end': {
                'dateTime': timelog.end_time.isoformat() if timelog.end_time else None,
                'timeZone': getattr(user, 'timezone', 'Europe/Sofia')
            },
            'extendedProperties': {
                'private': {
                    'source': 'chronos_worktime',
                    'source_type': 'time_log',
                    'source_id': str(timelog.id),
                    'is_manual': str(timelog.is_manual),
                    'log_type': timelog.type
                }
            },
            'colorId': '4' if timelog.is_manual else '2',  # Red for manual, green for automatic
            'transparency': 'opaque'
        }
    
    def format_leave_request_event(self, leave: LeaveRequest, user: User,
                                 privacy_level: str = 'title_only') -> Dict[str, Any]:
        """Convert LeaveRequest to Google Calendar event"""
        title = f"{leave.leave_type.replace('_', ' ').title()}"
        
        if privacy_level == 'busy_only':
            title = "Out of Office"
        
        description = ""
        if privacy_level in ['title_only', 'full']:
            description = f"Type: {leave.leave_type.replace('_', ' ').title()}"
            if leave.reason:
                description += f"\nReason: {leave.reason}"
            if leave.status == 'pending':
                description += "\nStatus: Pending Approval"
        
        return {
            'summary': title,
            'description': description,
            'start': {
                'date': leave.start_date.isoformat()
            },
            'end': {
                'date': (leave.end_date + datetime.timedelta(days=1)).isoformat()  # Google Calendar exclusive end
            },
            'extendedProperties': {
                'private': {
                    'source': 'chronos_worktime',
                    'source_type': 'leave_request',
                    'source_id': str(leave.id),
                    'leave_type': leave.leave_type,
                    'status': leave.status
                }
            },
            'colorId': self._get_color_for_leave_type(leave.leave_type),
            'transparency': 'opaque'
        }
    
    def _get_color_for_shift_type(self, shift_type: str) -> str:
        """Map shift types to Google Calendar color IDs"""
        color_map = {
            'regular': '2',      # Green
            'sick_leave': '4',   # Red
            'paid_leave': '5',   # Yellow
            'unpaid_leave': '6', # Orange
            'day_off': '8'       # Gray
        }
        return color_map.get(shift_type, '1')  # Blue default
    
    def _get_color_for_leave_type(self, leave_type: str) -> str:
        """Map leave types to Google Calendar color IDs"""
        color_map = {
            'sick_leave': '4',    # Red
            'paid_leave': '5',     # Yellow
            'unpaid_leave': '6',   # Orange
            'day_off': '8'         # Gray
        }
        return color_map.get(leave_type, '7')  # Purple default
    
    async def batch_create_events(self, access_token: str, calendar_id: str, 
                               events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple events in batches to avoid rate limits"""
        results = []
        batch_size = 10  # Google Calendar API limit
        
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            batch_results = []
            
            for event in batch:
                try:
                    result = await self.create_event(access_token, calendar_id, event)
                    batch_results.append(result)
                except Exception as e:
                    batch_results.append({'error': str(e)})
            
            results.extend(batch_results)
            
            # Rate limiting: wait between batches
            if i + batch_size < len(events):
                await asyncio.sleep(1)
        
        return results


# Singleton instance
google_calendar_service = GoogleCalendarService()