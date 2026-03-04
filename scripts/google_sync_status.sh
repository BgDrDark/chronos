#!/bin/bash
# Google Calendar Sync Status Script
# This script checks the status of Google Calendar synchronization

echo "🗓️ Google Calendar Sync Status Check"
echo "=================================="

# Check if Google Calendar is configured
echo "📋 Configuration Status:"
echo "• GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:-Not Set}"
echo "• GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET:-Not Set}"
echo "• GOOGLE_SYNC_ENABLED: ${GOOGLE_SYNC_ENABLED:-Not Set}"
echo ""

# Check database connection
echo "🗄️ Database Connection:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    'Google Calendar Accounts' as table_name,
    COUNT(*) as count,
    MAX(created_at) as last_created
FROM google_calendar_accounts 
UNION ALL
SELECT 
    'Google Calendar Events' as table_name,
    COUNT(*) as count,
    MAX(created_at) as last_created
FROM google_calendar_events
UNION ALL
SELECT 
    'Google Sync Logs' as table_name,
    COUNT(*) as count,
    MAX(created_at) as last_created
FROM google_sync_log
" 2>/dev/null || echo "Database connection failed"

echo ""
echo "📊 Recent Sync Activity:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    sync_type,
    status,
    events_processed,
    events_created,
    events_updated,
    events_deleted,
    started_at,
    completed_at,
    CASE 
        WHEN completed_at IS NULL THEN 'Running'
        ELSE EXTRACT(EPOCH FROM (completed_at - started_at))::text || 's'
    END as duration
FROM google_sync_log 
ORDER BY started_at DESC 
LIMIT 5
" 2>/dev/null || echo "Could not fetch sync logs"

echo ""
echo "🔧 Active Accounts:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    u.email,
    u.first_name,
    u.last_name,
    gca.is_active,
    gca.google_user_id,
    gca.created_at,
    gca.token_expires_at,
    CASE 
        WHEN gca.token_expires_at > NOW() THEN 'Valid'
        ELSE 'Expired'
    END as token_status
FROM google_calendar_accounts gca
JOIN users u ON gca.user_id = u.id
WHERE gca.is_active = true
ORDER BY gca.created_at DESC
" 2>/dev/null || echo "Could not fetch active accounts"

echo ""
echo "📈 Sync Settings:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    u.email,
    gcs.sync_work_schedules,
    gcs.sync_time_logs,
    gcs.sync_leave_requests,
    gcs.sync_public_holidays,
    gcs.sync_direction,
    gcs.sync_frequency_minutes,
    gcs.privacy_level,
    gcs.default_event_visibility,
    gcs.timezone
FROM google_calendar_sync_settings gcs
JOIN google_calendar_accounts gca ON gcs.account_id = gca.id
JOIN users u ON gca.user_id = u.id
WHERE gca.is_active = true
ORDER BY u.email
" 2>/dev/null || echo "Could not fetch sync settings"

echo ""
echo "🎯 Recommendations:"
echo "• If GOOGLE_CLIENT_ID/SECRET are not set, configure them in .env file"
echo "• If token_status shows 'Expired', users need to re-authenticate"
echo "• Check sync logs for any errors or failed sync attempts"
echo "• Monitor sync frequency - too frequent may cause rate limiting"
echo "• Review privacy settings for sensitive calendar data"

echo ""
echo "🔍 Health Check Complete!"
echo "=================================="