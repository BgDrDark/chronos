import strawberry
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from strawberry.types import Info

from backend.modules.behavioral_analysis.models import BehavioralSystemHealth
from backend.modules.behavioral_analysis.graphql.types import BehavioralSystemHealthType
from backend.exceptions import PermissionDeniedException
from backend.database.models import User


@strawberry.type
class SystemHealthQuery:
    @strawberry.field
    async def behavioral_system_health(self, info: Info, company_id: Optional[int] = None) -> Optional[BehavioralSystemHealthType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]
        
        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view system health")
            
        cid = company_id or current_user.company_id
        
        result = await db.execute(
            select(BehavioralSystemHealth).where(BehavioralSystemHealth.company_id == cid)
        )
        health = result.scalar_one_or_none()
        
        if not health:
            return None
            
        return BehavioralSystemHealthType(
            id=health.id,
            company_id=health.company_id,
            lastComputationAt=health.last_computation_at,
            lastComputationStatus=health.last_computation_status,
            lastComputationDurationSeconds=health.last_computation_duration_seconds,
            employeesProcessed=health.employees_processed,
            employeesFailed=health.employees_failed,
            circuitBreakerOpen=health.circuit_breaker_open,
            circuitBreakerFailureCount=health.circuit_breaker_failure_count,
            lastSuccessfulProfileDate=health.last_successful_profile_date,
            triggeredAlertsToday=health.triggered_alerts_today,
            lastBiasCheck=health.last_bias_check,
        )
