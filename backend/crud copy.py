from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from backend.config import settings
from backend.database.models import User, Role, TimeLog, Payroll, Payslip, Shift, WorkSchedule, GlobalSetting, LeaveRequest, LeaveBalance, sofia_now, AuthKey, UserSession, AuditLog, ShiftSwapRequest, ScheduleTemplate, ScheduleTemplateItem, PushSubscription
# ... (rest of imports)

# --- Push Notifications ---

async def ensure_vapid_keys(db: AsyncSession):
    pub = await get_global_setting(db, "vapid_public_key")
    priv = await get_global_setting(db, "vapid_private_key")
    
    if not pub or not priv:
        from pywebpush import vapid_errors
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        
        # Generate new VAPID keys
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        
        # We need raw bytes for VAPID (uncompressed)
        # For simplicity, pywebpush has a utility or we use cryptography
        # Actually pywebpush doesn't have a direct generator in 2.2.0, but we can use openssl or cryptography
        # Here's a quick way:
        import base64
        
        # This is a bit complex to do manually with cryptography to match VAPID spec (uncompressed EC)
        # So we'll use a simpler placeholder or a known working method if possible.
        # But for now, let's assume we want real keys.
        
        # Generate via command line if needed or use a library. 
        # I'll use a helper logic.
        print("VAPID keys missing. Generating...")
        # (Skip complex key gen for a moment, use a hardcoded ones for testing OR real generation)
        # Let's generate real ones.
        return None # Will handle in a script for safety

async def subscribe_user_to_push(db: AsyncSession, user_id: int, sub_data: dict):
    # sub_data is expected to have endpoint, p256dh, auth
    endpoint = sub_data.get("endpoint")
    keys = sub_data.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")
    
    if not endpoint or not p256dh or not auth:
        raise ValueError("Invalid subscription data")
        
    # Remove existing for this endpoint if any
    await db.execute(delete(PushSubscription).where(PushSubscription.endpoint == endpoint))
    
    new_sub = PushSubscription(
        user_id=user_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth
    )
    db.add(new_sub)
    await db.commit()
    return new_sub

async def send_push_to_user(db: AsyncSession, user_id: int, title: str, body: str, icon: str = "/pwa-192x192.png", url: str = "/"):
    from pywebpush import webpush, WebPushException
    import json
    
    # Get VAPID Keys
    vapid_private = await get_global_setting(db, "vapid_private_key")
    vapid_email = await get_global_setting(db, "mail_from") or "admin@chronos.local"
    
    if not vapid_private:
        print("Push failed: No VAPID private key")
        return
        
    # Get subscriptions
    stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
    res = await db.execute(stmt)
    subs = res.scalars().all()
    
    payload = {
        "notification": {
            "title": title,
            "body": body,
            "icon": icon,
            "data": { "url": url }
        }
    }
    
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                }, # type: ignore
                data=json.dumps(payload),
                vapid_private_key=vapid_private,
                vapid_claims={"sub": f"mailto:{vapid_email}"}
            )
        except WebPushException as ex:
            print(f"Push failed for {sub.endpoint}: {ex}")
            # If gone, delete
            if "410" in str(ex) or "404" in str(ex):
                await db.delete(sub)
                await db.commit()

# --- Schedule Templates ---

async def create_schedule_template(db: AsyncSession, name: str, description: Optional[str] = None, items: List[dict] = []):
    template = ScheduleTemplate(name=name, description=description)
    db.add(template)
    await db.flush() # Get template ID
    
    for item in items:
        tmpl_item = ScheduleTemplateItem(
            template_id=template.id,
            day_index=item["day_index"],
            shift_id=item.get("shift_id")
        )
        db.add(tmpl_item)
    
    await db.commit()
    await db.refresh(template)
    return template

async def get_schedule_templates(db: AsyncSession):
    stmt = select(ScheduleTemplate).options(selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift))
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_schedule_template(db: AsyncSession, template_id: int):
    stmt = select(ScheduleTemplate).where(ScheduleTemplate.id == template_id).options(
        selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift)
    )
    res = await db.execute(stmt)
    return res.scalars().first()

async def delete_schedule_template(db: AsyncSession, template_id: int):
    tmpl = await db.get(ScheduleTemplate, template_id)
    if tmpl:
        await db.delete(tmpl)
        await db.commit()
        return True
    return False

async def apply_schedule_template(
    db: AsyncSession, 
    template_id: int, 
    user_id: int, 
    start_date: date, 
    end_date: date,
    admin_id: int
):
    template = await get_schedule_template(db, template_id)
    if not template or not template.items:
        raise ValueError("Шаблонът не съществува или е празен.")
    
    # Sort items by day_index to be sure
    sorted_items = sorted(template.items, key=lambda x: x.day_index)
    rotation_length = len(sorted_items)
    
    current_date = start_date
    days_processed = 0
    
    while current_date <= end_date:
        # Determine which item in the rotation to use
        item_index = days_processed % rotation_length
        target_item = sorted_items[item_index]
        
        # Find existing schedule or create new
        stmt = select(WorkSchedule).where(WorkSchedule.user_id == user_id, WorkSchedule.date == current_date)
        res = await db.execute(stmt)
        existing = res.scalars().first()
        
        if target_item.shift_id:
            if existing:
                existing.shift_id = target_item.shift_id
            else:
                new_sched = WorkSchedule(user_id=user_id, date=current_date, shift_id=target_item.shift_id)
                db.add(new_sched)
        else:
            # If template says null (Day Off), we might want to delete existing shift
            if existing:
                await db.delete(existing)
        
        current_date += timedelta(days=1)
        days_processed += 1

    await log_audit_action(
        db, admin_id, "APPLY_SCHEDULE_TEMPLATE",
        target_type="User", target_id=user_id,
        details=f"Applied template '{template.name}' from {start_date} to {end_date}"
    )
    
    await db.commit()
    return True

# --- Shift Swapping ---

async def create_swap_request(
    db: AsyncSession, 
    requestor_id: int, 
    requestor_schedule_id: int, 
    target_user_id: int, 
    target_schedule_id: int
):
    # Verify schedules exist and belong to correct users
    req_sched = await db.get(WorkSchedule, requestor_schedule_id)
    tar_sched = await db.get(WorkSchedule, target_schedule_id)
    
    if not req_sched or req_sched.user_id != requestor_id:
        raise ValueError("Вашата избрана смяна е невалидна.")
    if not tar_sched or tar_sched.user_id != target_user_id:
        raise ValueError("Избраната смяна на колегата е невалидна.")
    
    # Check for existing pending request for these schedules
    stmt = select(ShiftSwapRequest).where(
        ShiftSwapRequest.requestor_schedule_id == requestor_schedule_id,
        ShiftSwapRequest.status == "pending"
    )
    res = await db.execute(stmt)
    if res.scalars().first():
        raise ValueError("Вече има активна заявка за тази смяна.")

    swap = ShiftSwapRequest(
        requestor_id=requestor_id,
        requestor_schedule_id=requestor_schedule_id,
        target_user_id=target_user_id,
        target_schedule_id=target_schedule_id,
        status="pending"
    )
    db.add(swap)
    await db.commit()
    await db.refresh(swap)
    
    # Notify target user
    await create_notification(db, target_user_id, f"Колега иска да размени смяна с Вас за дата {req_sched.date}.")
    await send_push_to_user(db, target_user_id, "Размяна на смени", f"Колега иска да размени смяна с Вас за {req_sched.date}.")
    
    return swap

async def get_swap_request(db: AsyncSession, swap_id: int):
    

    
    if new_status == "approved":
        # PERFORM THE REAL SWAP
        req_sched = swap.requestor_schedule
        tar_sched = swap.target_schedule
        
        # Swap shift IDs
        old_req_shift_id = req_sched.shift_id
        req_sched.shift_id = tar_sched.shift_id
        tar_sched.shift_id = old_req_shift_id
        
        db.add(req_sched)
        db.add(tar_sched)
        
        await log_audit_action(
            db, admin_user_id, "APPROVE_SHIFT_SWAP", 
            target_type="ShiftSwapRequest", target_id=swap_id,
            details=f"Swapped {swap.requestor.email} and {swap.target_user.email} shifts for {req_sched.date} and {tar_sched.date}"
        )
        
        # Notify both
        await create_notification(db, swap.requestor_id, f"Размяната на смени за {req_sched.date} беше ОДОБРЕНА от администратор.")
        await create_notification(db, swap.target_user_id, f"Размяната на смени за {tar_sched.date} беше ОДОБРЕНА от администратор.")
        
        await send_push_to_user(db, swap.requestor_id, "Размяната е одобрена", f"Размяната за {req_sched.date} беше одобрена.")
        await send_push_to_user(db, swap.target_user_id, "Размяната е одобрена", f"Размяната за {tar_sched.date} беше одобрена.")

    elif new_status == "accepted":
        # Notify Admin
        await notify_admins(db, f"Нова размяна на смени чака одобрение: {swap.requestor.email} <-> {swap.target_user.email}")
        await create_notification(db, swap.requestor_id, f"Колегата ПРИЕ вашата покана за размяна. Чака се одобрение от администратор.")
        await send_push_to_user(db, swap.requestor_id, "Поканата е приета", "Колегата прие вашата размяна. Чака се одобрение.")

    elif new_status == "rejected":
        await create_notification(db, swap.requestor_id, f"Колегата ОТКАЗА вашата покана за размяна.")
        await send_push_to_user(db, swap.requestor_id, "Поканата е отказана", "Колегата отказа вашата покана за размяна.")

    await db.commit()
    await db.refresh(swap)
    return swap

async def get_my_swap_requests(db: AsyncSession, user_id: int):
    # Both outgoing and incoming
    stmt = select(ShiftSwapRequest).where(
        or_(
            ShiftSwapRequest.requestor_id == user_id,
            ShiftSwapRequest.target_user_id == user_id
        )
    ).order_by(ShiftSwapRequest.created_at.desc()).options(
        selectinload(ShiftSwapRequest.requestor),
        selectinload(ShiftSwapRequest.target_user),
        selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
        selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_all_pending_swaps(db: AsyncSession):
    # Only those accepted by users but not yet approved by admin
    stmt = select(ShiftSwapRequest).where(ShiftSwapRequest.status == "accepted").options(
        selectinload(ShiftSwapRequest.requestor),
        selectinload(ShiftSwapRequest.target_user),
        selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
        selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
from backend.schemas import UserCreate, UserUpdate, RoleCreate
from backend.auth.security import hash_password

async def log_audit_action(
    db: AsyncSession, 
    user_id: Optional[int], 
    action: str, 
    target_type: Optional[str] = None, 
    target_id: Optional[int] = None, 
    details: Optional[str] = None
):
    """Creates an entry in the audit log."""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(log_entry)
    return log_entry

async def get_shift_by_id(db: AsyncSession, shift_id: int):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    return result.scalars().first()

async def get_shifts(db: AsyncSession):
    result = await db.execute(select(Shift))
    return result.scalars().all()

async def create_shift(db: AsyncSession, name: str, start_time: datetime.time, end_time: datetime.time, tolerance_minutes: int = 15, break_duration_minutes: int = 0, pay_multiplier: float = 1.0):
    db_shift = Shift(
        name=name, 
        start_time=start_time, 
        end_time=end_time,
        tolerance_minutes=tolerance_minutes,
        break_duration_minutes=break_duration_minutes,
        pay_multiplier=pay_multiplier
    )
    db.add(db_shift)
    await db.commit()
    await db.refresh(db_shift)
    return db_shift

async def update_shift(db: AsyncSession, shift_id: int, name: str = None, start_time: datetime.time = None, end_time: datetime.time = None, tolerance_minutes: int = None, break_duration_minutes: int = None, pay_multiplier: float = None):
    db_shift = await get_shift_by_id(db, shift_id)
    if not db_shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    
    if name: db_shift.name = name
    if start_time: db_shift.start_time = start_time
    if end_time: db_shift.end_time = end_time
    if tolerance_minutes is not None: db_shift.tolerance_minutes = tolerance_minutes
    if break_duration_minutes is not None: db_shift.break_duration_minutes = break_duration_minutes
    if pay_multiplier is not None: db_shift.pay_multiplier = pay_multiplier
    
    await db.commit()
    await db.refresh(db_shift)
    return db_shift

async def delete_shift(db: AsyncSession, shift_id: int, admin_user_id: Optional[int] = None):
    db_shift = await get_shift_by_id(db, shift_id)
    if not db_shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    
    shift_name = db_shift.name
    await db.delete(db_shift)
    
    await log_audit_action(
        db, admin_user_id, "DELETE_SHIFT", 
        target_type="Shift", target_id=shift_id,
        details=f"Name: {shift_name}"
    )
    
    await db.commit()
    return True

async def delete_schedule(db: AsyncSession, schedule_id: int):
    result = await db.execute(select(WorkSchedule).where(WorkSchedule.id == schedule_id))
    db_schedule = result.scalars().first()
    if not db_schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    
    await db.delete(db_schedule)
    await db.commit()
    return True

async def get_schedules_by_period(db: AsyncSession, start_date: datetime.date, end_date: datetime.date):
    result = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.date >= start_date)
        .where(WorkSchedule.date <= end_date)
        .options(selectinload(WorkSchedule.shift), selectinload(WorkSchedule.user))
    )
    return result.scalars().all()

async def get_user_schedules(db: AsyncSession, user_id: int, start_date: datetime.date, end_date: datetime.date):
    result = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.user_id == user_id)
        .where(WorkSchedule.date >= start_date)
        .where(WorkSchedule.date <= end_date)
        .options(selectinload(WorkSchedule.shift))
    )
    return result.scalars().all()

async def get_shift_by_name(db: AsyncSession, name: str):
    result = await db.execute(select(Shift).where(Shift.name == name))
    return result.scalars().first()

async def get_shift_by_type(db: AsyncSession, shift_type: str):
    result = await db.execute(select(Shift).where(Shift.shift_type == shift_type))
    return result.scalars().first()

async def create_notification(db: AsyncSession, user_id: int, message: str):
    from backend.database.models import Notification
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    return notification

async def get_admins(db: AsyncSession):
    result = await db.execute(select(User).join(Role).where(Role.name == "admin"))
    return result.scalars().all()

async def notify_admins(db: AsyncSession, message: str):
    admins = await get_admins(db)
    for admin in admins:
        await create_notification(db, admin.id, message)

async def create_or_update_schedule(db: AsyncSession, user_id: int, shift_id: int, date: datetime.date):
    result = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.user_id == user_id)
        .where(WorkSchedule.date == date)
    )
    db_schedule = result.scalars().first()
    
    shift = await get_shift_by_id(db, shift_id)
    user = await get_user_by_id(db, user_id)
    shift_name = shift.name if shift else "Unknown Shift"
    user_name = f"{user.first_name} {user.last_name}" if user and user.first_name else f"User {user_id}"
    
    if db_schedule:
        db_schedule.shift_id = shift_id
        action = "актуализиран"
    else:
        db_schedule = WorkSchedule(user_id=user_id, shift_id=shift_id, date=date)
        db.add(db_schedule)
        action = "назначен"
    
    await notify_admins(db, f"Графикът е {action} за {user_name} на {date}: {shift_name}")

    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule


async def create_bulk_schedules(
    db: AsyncSession, 
    user_ids: list[int], 
    shift_id: int, 
    start_date: datetime.date, 
    end_date: datetime.date,
    days_of_week: list[int] # 0=Mon, 6=Sun
):
    from datetime import timedelta
    
    shift = await get_shift_by_id(db, shift_id)
    shift_name = shift.name if shift else "Неизвестна смяна"
    
    schedules = []
    current_date = start_date
    count = 0
    while current_date <= end_date:
        if current_date.weekday() in days_of_week:
            for user_id in user_ids:
                result = await db.execute(
                    select(WorkSchedule)
                    .where(WorkSchedule.user_id == user_id)
                    .where(WorkSchedule.date == current_date)
                )
                db_schedule = result.scalars().first()
                
                if db_schedule:
                    db_schedule.shift_id = shift_id
                else:
                    db_schedule = WorkSchedule(user_id=user_id, shift_id=shift_id, date=current_date)
                    db.add(db_schedule)
                schedules.append(db_schedule)
                count += 1
        
        current_date += timedelta(days=1)
    
    await notify_admins(db, f"Групово назначаване на график: {shift_name} за {len(user_ids)} служители от {start_date} до {end_date} ({count} смени създадени/актуализирани).")

    await db.commit()
    return True

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.email == email)
    )
    return result.scalars().first()

async def get_user_by_qr_token(db: AsyncSession, qr_token: str):
    result = await db.execute(
        select(User).where(User.qr_token == qr_token)
    )
    return result.scalars().first()

async def regenerate_user_qr_token(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")
    
    import uuid
    user.qr_token = str(uuid.uuid4())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user.qr_token

async def create_user(db: AsyncSession, user: UserCreate, role_name: str = "user"):
    hashed_password = hash_password(user.password)
    
    role = await get_role_by_name(db, role_name)
    if not role:
        if role_name == "user":
            role = await create_role(db, RoleCreate(name="user", description="Standard user role"))
        else:
            raise ValueError(f"Role '{role_name}' does not exist.")

    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        role_id=role.id,
        first_name=user.first_name,
        last_name=user.last_name,
        # Legacy fields
        job_title=user.job_title,
        department=user.department,
        company=user.company,
        # New fields
        company_id=user.company_id,
        department_id=user.department_id,
        position_id=user.position_id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user_in: UserUpdate):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = hash_password(update_data["password"])
        del update_data["password"] # Remove plain password

    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_last_login(db: AsyncSession, user_id: int):
    db_user = await get_user_by_id(db, user_id)
    if db_user:
        db_user.last_login = sofia_now()
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: int, admin_user_id: Optional[int] = None):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    email = db_user.email
    await db.delete(db_user)
    
    await log_audit_action(
        db, admin_user_id, "DELETE_USER", 
        target_type="User", target_id=user_id,
        details=f"Email: {email}"
    )
    
    await db.commit()
    return {"message": "User deleted successfully"}


async def get_role_by_name(db: AsyncSession, role_name: str):
    result = await db.execute(
        select(Role).where(Role.name == role_name)
    )
    return result.scalars().first()

async def create_role(db: AsyncSession, role: RoleCreate):
    db_role = Role(name=role.name, description=role.description)
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100, search: Optional[str] = None, sort_by: str = "id", sort_order: str = "asc"):
    stmt = select(User).options(selectinload(User.role)).join(Role)
    
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(search_filter),
                User.first_name.ilike(search_filter),
                User.last_name.ilike(search_filter),
                User.job_title.ilike(search_filter),
                User.department.ilike(search_filter),
                User.company.ilike(search_filter),
                Role.name.ilike(search_filter)
            )
        )
    
    # Sorting
    attr = getattr(User, sort_by, User.id)
    if sort_order == "desc":
        stmt = stmt.order_by(desc(attr))
    else:
        stmt = stmt.order_by(asc(attr))
        
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def count_users(db: AsyncSession, search: Optional[str] = None):
    stmt = select(func.count(User.id)).join(Role)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(search_filter),
                User.first_name.ilike(search_filter),
                User.last_name.ilike(search_filter),
                User.job_title.ilike(search_filter),
                User.department.ilike(search_filter),
                User.company.ilike(search_filter),
                Role.name.ilike(search_filter)
            )
        )
    result = await db.execute(stmt)
    return result.scalar()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    return result.scalars().first()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Role).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_role_by_id(db: AsyncSession, role_id: int):
    result = await db.execute(
        select(Role).where(Role.id == role_id)
    )
    return result.scalars().first()


async def get_timelogs_by_user_and_period(db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime):
    result = await db.execute(
        select(TimeLog)
        .where(TimeLog.user_id == user_id)
        .where(TimeLog.start_time >= start_date)
        .where(TimeLog.start_time <= end_date)
    )
    return result.scalars().all()


async def get_global_payroll_config(db: AsyncSession):
    # Retrieve individual settings or return defaults
    hourly_rate = await get_global_setting(db, "global_hourly_rate")
    monthly_salary = await get_global_setting(db, "global_monthly_salary")
    overtime_multiplier = await get_global_setting(db, "global_overtime_multiplier")
    standard_hours_per_day = await get_global_setting(db, "global_standard_hours_per_day")
    currency = await get_global_setting(db, "global_currency")
    annual_leave_days = await get_global_setting(db, "global_annual_leave_days")
    
    # Deductions
    tax_percent = await get_global_setting(db, "global_tax_percent")
    health_insurance_percent = await get_global_setting(db, "global_health_insurance_percent")
    has_tax_deduction = await get_global_setting(db, "global_has_tax_deduction")
    has_health_insurance = await get_global_setting(db, "global_has_health_insurance")

    from types import SimpleNamespace
    return SimpleNamespace(
        hourly_rate=float(hourly_rate) if hourly_rate else 0.0,
        monthly_salary=float(monthly_salary) if monthly_salary else 0.0,
        overtime_multiplier=float(overtime_multiplier) if overtime_multiplier else 1,
        standard_hours_per_day=int(standard_hours_per_day) if standard_hours_per_day else 8,
        currency=currency or "EUR",
        annual_leave_days=int(annual_leave_days) if annual_leave_days else 20,
        
        tax_percent=float(tax_percent) if tax_percent else 10.00,
        health_insurance_percent=float(health_insurance_percent) if health_insurance_percent else 13.78,
        has_tax_deduction=(has_tax_deduction == "True") if has_tax_deduction is not None else True,
        has_health_insurance=(has_health_insurance == "True") if has_health_insurance is not None else True
    )

async def update_global_payroll_config(
    db: AsyncSession, 
    hourly_rate: float, 
    overtime_multiplier: float, 
    standard_hours_per_day: int, 
    monthly_salary: float,
    currency: str,
    annual_leave_days: int,
    tax_percent: float,
    health_insurance_percent: float,
    has_tax_deduction: bool,
    has_health_insurance: bool,
    admin_user_id: Optional[int] = None
):
    await set_global_setting(db, "global_hourly_rate", str(hourly_rate))
    await set_global_setting(db, "global_monthly_salary", str(monthly_salary))
    await set_global_setting(db, "global_overtime_multiplier", str(overtime_multiplier))
    await set_global_setting(db, "global_standard_hours_per_day", str(standard_hours_per_day))
    await set_global_setting(db, "global_currency", currency)
    await set_global_setting(db, "global_annual_leave_days", str(annual_leave_days))
    
    await set_global_setting(db, "global_tax_percent", str(tax_percent))
    await set_global_setting(db, "global_health_insurance_percent", str(health_insurance_percent))
    await set_global_setting(db, "global_has_tax_deduction", str(has_tax_deduction))
    await set_global_setting(db, "global_has_health_insurance", str(has_health_insurance))
    
    await log_audit_action(
        db, admin_user_id, "UPDATE_GLOBAL_PAYROLL", 
        details=f"Rate: {hourly_rate}, Salary: {monthly_salary}, Currency: {currency}"
    )
    
    return await get_global_payroll_config(db)

async def get_payroll_config(db: AsyncSession, user_id: int):
    # 1. Try to get individual config
    result = await db.execute(
        select(Payroll).where(Payroll.user_id == user_id)
    )
    config = result.scalars().first()
    if config:
        return config

    # 2. Fallback to Position config
    user = await get_user_by_id(db, user_id)
    if user and user.position_id:
        pos_result = await db.execute(
            select(Payroll).where(Payroll.position_id == user.position_id)
        )
        pos_config = pos_result.scalars().first()
        if pos_config:
            return pos_config
            
    # 3. Global Fallback
    return await get_global_payroll_config(db)


async def create_payslip(db: AsyncSession, payslip_data: dict):
    db_payslip = Payslip(**payslip_data)
    db.add(db_payslip)
    await db.commit()
    await db.refresh(db_payslip)
    return db_payslip

async def update_payroll_config(
    db: AsyncSession, 
    user_id: int, 
    hourly_rate: float, 
    overtime_multiplier: float = 1.5, 
    standard_hours_per_day: int = 8, 
    monthly_salary: float = None,
    currency: str = "EUR",
    annual_leave_days: int = 20,
    tax_percent: float = 10.0,
    health_insurance_percent: float = 13.78,
    has_tax_deduction: bool = True,
    has_health_insurance: bool = True,
    admin_user_id: Optional[int] = None
):
    # This updates specific USER config
    stmt = select(Payroll).where(Payroll.user_id == user_id)
    result = await db.execute(stmt)
    config = result.scalars().first()
    
    if config:
        config.hourly_rate = hourly_rate
        config.monthly_salary = monthly_salary
        config.overtime_multiplier = overtime_multiplier
        config.standard_hours_per_day = standard_hours_per_day
        config.currency = currency
        config.annual_leave_days = annual_leave_days
        
        config.tax_percent = tax_percent
        config.health_insurance_percent = health_insurance_percent
        config.has_tax_deduction = has_tax_deduction
        config.has_health_insurance = has_health_insurance
        
        db.add(config)
    else:
        config = Payroll(
            user_id=user_id,
            hourly_rate=hourly_rate,
            monthly_salary=monthly_salary,
            overtime_multiplier=overtime_multiplier,
            standard_hours_per_day=standard_hours_per_day,
            currency=currency,
            annual_leave_days=annual_leave_days,
            tax_percent=tax_percent,
            health_insurance_percent=health_insurance_percent,
            has_tax_deduction=has_tax_deduction,
            has_health_insurance=has_health_insurance
        )
        db.add(config)
    
    await log_audit_action(
        db, admin_user_id, "UPDATE_USER_PAYROLL", 
        target_type="User", target_id=user_id,
        details=f"Rate: {hourly_rate}, Salary: {monthly_salary}, Currency: {currency}"
    )
    
    await db.commit()
    await db.refresh(config)
    return config

async def update_position_payroll_config(
    db: AsyncSession, 
    position_id: int, 
    hourly_rate: float, 
    overtime_multiplier: float = 1.5, 
    standard_hours_per_day: int = 8, 
    monthly_salary: float = None,
    currency: str = "EUR",
    annual_leave_days: int = 20,
    tax_percent: float = 10.0,
    health_insurance_percent: float = 13.78,
    has_tax_deduction: bool = True,
    has_health_insurance: bool = True,
    admin_user_id: Optional[int] = None
):
    stmt = select(Payroll).where(Payroll.position_id == position_id)
    result = await db.execute(stmt)
    config = result.scalars().first()
    
    if config:
        config.hourly_rate = hourly_rate
        config.monthly_salary = monthly_salary
        config.overtime_multiplier = overtime_multiplier
        config.standard_hours_per_day = standard_hours_per_day
        config.currency = currency
        config.annual_leave_days = annual_leave_days
        
        config.tax_percent = tax_percent
        config.health_insurance_percent = health_insurance_percent
        config.has_tax_deduction = has_tax_deduction
        config.has_health_insurance = has_health_insurance
        
        db.add(config)
    else:
        config = Payroll(
            position_id=position_id,
            hourly_rate=hourly_rate,
            monthly_salary=monthly_salary,
            overtime_multiplier=overtime_multiplier,
            standard_hours_per_day=standard_hours_per_day,
            currency=currency,
            annual_leave_days=annual_leave_days,
            tax_percent=tax_percent,
            health_insurance_percent=health_insurance_percent,
            has_tax_deduction=has_tax_deduction,
            has_health_insurance=has_health_insurance
        )
        db.add(config)
    
    await log_audit_action(
        db, admin_user_id, "UPDATE_POSITION_PAYROLL", 
        target_type="Position", target_id=position_id,
        details=f"Rate: {hourly_rate}, Salary: {monthly_salary}, Currency: {currency}"
    )
    
    await db.commit()
    await db.refresh(config)
    return config


async def get_active_time_log(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(TimeLog)
        .where(TimeLog.user_id == user_id)
        .where(TimeLog.end_time == None)
    )
    return result.scalars().first()


import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

async def start_time_log(db: AsyncSession, user_id: int, latitude: float = None, longitude: float = None, custom_time: datetime = None):
    from datetime import timedelta, datetime
    
    # 1. Check for active log
    active_log = await get_active_time_log(db, user_id)
    if active_log:
        raise ValueError("Вече имате активно отчитане на времето.")

    # 1.1 Check Geolocation (if configured and enabled) - Skip if custom_time provided (Admin override)
    if not custom_time:
        entry_enabled = await get_global_setting(db, "geofencing_entry_enabled")
        
        if entry_enabled == "True":
            office_lat = await get_global_setting(db, "office_latitude")
            office_lon = await get_global_setting(db, "office_longitude")
            office_rad = await get_global_setting(db, "office_radius")

            if office_lat and office_lon and office_rad:
                if latitude is None or longitude is None:
                    raise ValueError("Изисква се местоположение за стартиране на смяна (Geofencing е активиран).")
                
                dist = calculate_distance(latitude, longitude, float(office_lat), float(office_lon))
                if dist > float(office_rad):
                    raise ValueError(f"Вие сте извън офис зоната! Разстояние: {int(dist)}м (Допустимо: {office_rad}м)")
    
    if custom_time:
        sofia_tz = ZoneInfo(settings.TIMEZONE)
        if custom_time.tzinfo is None:
             custom_time = custom_time.replace(tzinfo=sofia_tz)
        else:
             custom_time = custom_time.astimezone(sofia_tz)
        now_local = custom_time.replace(tzinfo=None)
    else:
        now_local = sofia_now()
    today = now_local.date()
    
    # 2. Get Shifts and Current Schedule
    all_shifts = await get_shifts(db)
    
    sched_result = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.user_id == user_id, WorkSchedule.date == today)
        .options(selectinload(WorkSchedule.shift))
    )
    current_schedule = sched_result.scalars().first()
    
    target_shift = None
    snapped_start_time = now_local
    
    # Helper to check match
    def is_matching_shift(time_now: datetime, shift: Shift) -> bool:
        shift_start_dt = datetime.combine(today, shift.start_time)
        tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
        diff_mins = abs((time_now - shift_start_dt).total_seconds()) / 60.0
        return diff_mins <= tolerance

    # 3. Logic: Check assigned shift first, then others
    matched_shift = None
    
    # A) Check assigned shift
    if current_schedule and current_schedule.shift:
        if is_matching_shift(now_local, current_schedule.shift):
            matched_shift = current_schedule.shift
    
    # B) If no match with assigned, check all others (Auto-Rotation)
    if not matched_shift:
        best_diff = float('inf')
        for shift in all_shifts:
            shift_start_dt = datetime.combine(today, shift.start_time)
            diff_mins = abs((now_local - shift_start_dt).total_seconds()) / 60.0
            tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
            
            if diff_mins <= tolerance:
                if diff_mins < best_diff:
                    best_diff = diff_mins
                    matched_shift = shift

        # If found a better shift, update schedule!
        if matched_shift:
            if current_schedule:
                # Update existing schedule
                if current_schedule.shift_id != matched_shift.id:
                    current_schedule.shift_id = matched_shift.id
                    db.add(current_schedule)
            else:
                # Create new schedule
                new_schedule = WorkSchedule(user_id=user_id, shift_id=matched_shift.id, date=today)
                db.add(new_schedule)

    # 4. Snap time if matched
    if matched_shift:
        shift_start_dt = datetime.combine(today, matched_shift.start_time)
        snapped_start_time = shift_start_dt

    db_log = TimeLog(user_id=user_id, start_time=snapped_start_time, latitude=latitude, longitude=longitude)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def end_time_log(db: AsyncSession, user_id: int, latitude: float = None, longitude: float = None, custom_time: datetime = None):
    from datetime import timedelta, datetime
    
    active_log = await get_active_time_log(db, user_id)
    if not active_log:
        raise ValueError("Не е намерено активно отчитане на времето за прекратяване.")

    # Geolocation Check for Exit - Skip if custom_time provided
    if not custom_time:
        exit_enabled = await get_global_setting(db, "geofencing_exit_enabled")
        if exit_enabled == "True":
            office_lat = await get_global_setting(db, "office_latitude")
            office_lon = await get_global_setting(db, "office_longitude")
            office_rad = await get_global_setting(db, "office_radius")

            if office_lat and office_lon and office_rad:
                if latitude is None or longitude is None:
                    raise ValueError("Изисква се местоположение за приключване на смяна (Geofencing Exit е активиран).")
                
                dist = calculate_distance(latitude, longitude, float(office_lat), float(office_lon))
                if dist > float(office_rad):
                    raise ValueError(f"Трябва да сте в офис зоната за да приключите! Разстояние: {int(dist)}м")
    
    if custom_time:
        sofia_tz = ZoneInfo(settings.TIMEZONE)
        if custom_time.tzinfo is None:
             custom_time = custom_time.replace(tzinfo=sofia_tz)
        else:
             custom_time = custom_time.astimezone(sofia_tz)
        now_local = custom_time.replace(tzinfo=None)
    else:
        now_local = sofia_now()
    log_date = active_log.start_time.date()
    
    # Get schedule to apply tolerance
    sched_result = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.user_id == user_id, WorkSchedule.date == log_date)
        .options(selectinload(WorkSchedule.shift))
    )
    schedule = sched_result.scalars().first()
    
    final_end_time = now_local
    
    if schedule and schedule.shift:
        s = schedule.shift
        shift_end_dt = datetime.combine(log_date, s.end_time)
        
        # Handle overnight shifts (end time < start time)
        if s.end_time < s.start_time:
            shift_end_dt += timedelta(days=1)
            
        tolerance = s.tolerance_minutes if s.tolerance_minutes is not None else 15
        diff_mins = abs((now_local - shift_end_dt).total_seconds()) / 60.0
        
        # Snap if within tolerance
        if diff_mins <= tolerance:
             final_end_time = shift_end_dt
    
    active_log.end_time = final_end_time
    db.add(active_log)
    await db.commit()
    await db.refresh(active_log)
    return active_log


async def create_manual_time_log(db: AsyncSession, user_id: int, start_time: datetime, end_time: datetime, break_duration_minutes: int = 0):
    # Convert to naive UTC if aware
    sofia_tz = ZoneInfo(settings.TIMEZONE)
    if start_time.tzinfo is not None:
        start_time = start_time.astimezone(sofia_tz).replace(tzinfo=None)
    if end_time.tzinfo is not None:
        end_time = end_time.astimezone(sofia_tz).replace(tzinfo=None)

    if start_time >= end_time:
        raise ValueError("Началният час трябва да бъде преди крайния час.")

    # Check for overlaps
    stmt = select(TimeLog).where(
        TimeLog.user_id == user_id,
        TimeLog.start_time < end_time,
        or_(
            TimeLog.end_time == None,
            TimeLog.end_time > start_time
        )
    )
    result = await db.execute(stmt)
    overlapping_logs = result.scalars().all()
    
    if overlapping_logs:
        conflict = overlapping_logs[0]
        c_start = conflict.start_time.strftime("%Y-%m-%d %H:%M")
        c_end = conflict.end_time.strftime("%Y-%m-%d %H:%M") if conflict.end_time else "Активен"
        raise ValueError(f"Записът се застъпва със съществуващ такъв: {c_start} - {c_end}")


    # Auto-detect shift and create schedule if missing
    log_date = start_time.date()
    
    # Check if schedule exists
    sched_result = await db.execute(
        select(WorkSchedule).where(WorkSchedule.user_id == user_id, WorkSchedule.date == log_date)
    )
    existing_schedule = sched_result.scalars().first()

    if not existing_schedule:
        # Try to find a matching shift based on start time
        shift_result = await db.execute(select(Shift))
        all_shifts = shift_result.scalars().all()
        
        best_shift = None
        min_diff = float('inf')
        
        for shift in all_shifts:
            shift_start_dt = datetime.combine(log_date, shift.start_time)
            # Compare minutes difference
            diff_mins = abs((start_time - shift_start_dt).total_seconds()) / 60.0
            tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
            
            if diff_mins <= tolerance:
                if diff_mins < min_diff:
                    min_diff = diff_mins
                    best_shift = shift
        
        if best_shift:
            new_schedule = WorkSchedule(user_id=user_id, shift_id=best_shift.id, date=log_date)
            db.add(new_schedule)

    db_log = TimeLog(user_id=user_id, start_time=start_time, end_time=end_time, is_manual=True, break_duration_minutes=break_duration_minutes)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log

async def delete_time_log(db: AsyncSession, log_id: int):
    result = await db.execute(delete(TimeLog).where(TimeLog.id == log_id).returning(TimeLog.id))
    deleted = result.scalars().first()
    await db.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time log not found or already deleted")
    return True

# --- Leave Management ---

async def create_leave_request(
    db: AsyncSession, 
    user_id: int, 
    start_date: datetime.date, 
    end_date: datetime.date, 
    leave_type: str, 
    reason: str = None
):
    if start_date > end_date:
        raise ValueError("Началната дата не може да бъде след крайната дата.")
        
    req = LeaveRequest(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        reason=reason,
        status="pending"
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    
    user = await get_user_by_id(db, user_id)
    name = f"{user.first_name} {user.last_name}" if user.first_name else user.email
    await notify_admins(db, f"Нова заявка за отпуск ({leave_type}) от {name}: {start_date} до {end_date}")
    
    return req

async def get_leave_requests(db: AsyncSession, user_id: int = None, status: str = None):
    stmt = select(LeaveRequest).options(selectinload(LeaveRequest.user)).order_by(LeaveRequest.created_at.desc())
    if user_id:
        stmt = stmt.where(LeaveRequest.user_id == user_id)
    if status:
        stmt = stmt.where(LeaveRequest.status == status)
        
    result = await db.execute(stmt)
    return result.scalars().all()

def calculate_working_days_count(start_date: datetime.date, end_date: datetime.date) -> int:
    from datetime import timedelta
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count

async def get_leave_balance(db: AsyncSession, user_id: int, year: int):
    # 1. Get Payroll config to find annual_leave_days
    payroll_stmt = select(Payroll).where(Payroll.user_id == user_id)
    payroll_res = await db.execute(payroll_stmt)
    payroll = payroll_res.scalars().first()
    
    configured_days = payroll.annual_leave_days if payroll and payroll.annual_leave_days is not None else 20

    stmt = select(LeaveBalance).where(LeaveBalance.user_id == user_id, LeaveBalance.year == year)
    result = await db.execute(stmt)
    balance = result.scalars().first()
    
    if not balance:
        balance = LeaveBalance(user_id=user_id, year=year, total_days=configured_days, used_days=0)
        db.add(balance)
        await db.commit()
        await db.refresh(balance)
    else:
        # Sync total_days if different (and payroll exists/is configured)
        # We only sync if the payroll setting is explicit or we want to enforce the default
        if balance.total_days != configured_days:
            balance.total_days = configured_days
            db.add(balance)
            await db.commit()
            await db.refresh(balance)
        
    return balance

async def update_leave_request_status(db: AsyncSession, request_id: int, status: str, admin_comment: str = None, admin_user_id: Optional[int] = None):
    stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await db.execute(stmt)
    req = result.scalars().first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Can only update pending requests")

    req.status = status
    req.admin_comment = admin_comment
    
    await log_audit_action(
        db, admin_user_id, "APPROVE_REJECT_LEAVE", 
        target_type="LeaveRequest", target_id=request_id,
        details=f"Status: {status}, Comment: {admin_comment}"
    )
    
    from datetime import timedelta
    
    # Calculate working days
    working_days = calculate_working_days_count(req.start_date, req.end_date)
    
    days_in_period = []
    current_date = req.start_date
    while current_date <= req.end_date:
        if current_date.weekday() < 5: # Mon-Fri
            days_in_period.append(current_date)
        current_date += timedelta(days=1)

    if status == "approved":
        # 1. Check balance if paid leave
        if req.leave_type == "paid_leave":
            balance = await get_leave_balance(db, req.user_id, req.start_date.year)
            if balance.used_days + working_days > balance.total_days:
                raise HTTPException(status_code=400, detail=f"Недостатъчен баланс за отпуск. Заявени: {working_days}, Оставащи: {balance.total_days - balance.used_days}")
            
            balance.used_days += working_days
            db.add(balance)

        # 2. Update Schedule
        target_shift = await get_shift_by_type(db, req.leave_type)
        
        if target_shift:
            for day in days_in_period:
                sched_stmt = select(WorkSchedule).where(WorkSchedule.user_id == req.user_id, WorkSchedule.date == day)
                sched_res = await db.execute(sched_stmt)
                schedule = sched_res.scalars().first()
                
                if schedule:
                    schedule.shift_id = target_shift.id
                    db.add(schedule)
                else:
                    schedule = WorkSchedule(user_id=req.user_id, shift_id=target_shift.id, date=day)
                    db.add(schedule)
    
    elif status == "rejected":
        # If it was somehow already scheduled or we want to ensure it's NOT there:
        # (Usually status only moves pending -> approved/rejected, so no rollback needed here)
        pass

    await db.commit()
    await db.refresh(req)
    
    # Notify User
    status_bg = "ОДОБРЕНА" if status == "approved" else "ОТХВЪРЛЕНА"
    await create_notification(db, req.user_id, f"Вашата заявка за отпуск за периода {req.start_date} - {req.end_date} беше {status_bg}.")
    await send_push_to_user(db, req.user_id, "Статус на отпуска", f"Заявката Ви за {req.start_date} беше {status_bg}.")
    
    return req

async def cancel_leave_request(db: AsyncSession, request_id: int, current_user_id: int, is_admin: bool = False):
    from datetime import timedelta
    # Fetch request
    stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await db.execute(stmt)
    req = result.scalars().first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if req.user_id != current_user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this request")

    today = sofia_now().date()

    if req.status == "approved":
        # RESTRICTION: Only Admin can cancel approved requests
        if not is_admin:
            raise HTTPException(status_code=403, detail="Само администратор може да прекратява вече одобрен отпуск.")

        if today > req.end_date:
             raise HTTPException(status_code=400, detail="Не може да прекратите отминал отпуск.")

        # Logic: Terminate Early or Cancel Future
        if today >= req.start_date:
            # EARLY TERMINATION (Shorten)
            new_end_date = today 
            
            # Calculate refund (days from tomorrow to end)
            refund_start = new_end_date + timedelta(days=1)
            days_to_refund = 0
            if refund_start <= req.end_date:
                 days_to_refund = calculate_working_days_count(refund_start, req.end_date)
            
            if req.leave_type == "paid_leave" and days_to_refund > 0:
                balance = await get_leave_balance(db, req.user_id, req.start_date.year)
                balance.used_days = max(0, balance.used_days - days_to_refund)
                db.add(balance)

            # Clear shifts from refund_start onwards
            curr = refund_start
            while curr <= req.end_date:
                sched_stmt = select(WorkSchedule).where(WorkSchedule.user_id == req.user_id, WorkSchedule.date == curr)
                sched_res = await db.execute(sched_stmt)
                schedule = sched_res.scalars().first()
                if schedule: await db.delete(schedule)
                curr += timedelta(days=1)
            
            req.end_date = new_end_date
            req.admin_comment = (req.admin_comment or "") + f" [Прекратен на {today}]"
            # Status remains 'approved'
            
        else:
            # FUTURE CANCELLATION (Full)
            if req.leave_type == "paid_leave":
                days_to_refund = calculate_working_days_count(req.start_date, req.end_date)
                balance = await get_leave_balance(db, req.user_id, req.start_date.year)
                balance.used_days = max(0, balance.used_days - days_to_refund)
                db.add(balance)
            
            # Clear all shifts
            curr = req.start_date
            while curr <= req.end_date:
                sched_stmt = select(WorkSchedule).where(WorkSchedule.user_id == req.user_id, WorkSchedule.date == curr)
                sched_res = await db.execute(sched_stmt)
                schedule = sched_res.scalars().first()
                if schedule: await db.delete(schedule)
                curr += timedelta(days=1)
            
            req.status = "cancelled"
            req.admin_comment = (req.admin_comment or "") + " [Отменен от администратор]"

    elif req.status == "pending":
         req.status = "cancelled"
         
    elif req.status == "rejected" or req.status == "cancelled":
        raise HTTPException(status_code=400, detail="Request is already cancelled/rejected")

    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req

async def update_leave_request(
    db: AsyncSession, 
    request_id: int, 
    current_user_id: int,
    is_admin: bool = False,
    start_date: datetime.date = None, 
    end_date: datetime.date = None,
    leave_type: str = None,
    reason: str = None
):
    stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await db.execute(stmt)
    req = result.scalars().first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if req.user_id != current_user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this request")

    # RESTRICTION: Only Admin can edit approved requests
    if req.status == "approved" and not is_admin:
        raise HTTPException(status_code=403, detail="Само администратор може да редактира вече одобрен отпуск.")

    if req.status == "rejected" or req.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot edit cancelled requests")

    # If pending, just update
    if req.status == "pending":
        if start_date: req.start_date = start_date
        if end_date: req.end_date = end_date
        if leave_type: req.leave_type = leave_type
        if reason: req.reason = reason
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    # If approved, we need to handle balance and schedule
    if req.status == "approved":
        # 1. Revert Old (Refund balance, clear schedule)
        
        old_days = 0
        if req.leave_type == "paid_leave":
            old_days = calculate_working_days_count(req.start_date, req.end_date)
            balance = await get_leave_balance(db, req.user_id, req.start_date.year)
            balance.used_days = max(0, balance.used_days - old_days)
            db.add(balance)
            
        # Clear old schedule
        from datetime import timedelta
        curr = req.start_date
        while curr <= req.end_date:
            sched_stmt = select(WorkSchedule).where(WorkSchedule.user_id == req.user_id, WorkSchedule.date == curr)
            sched_res = await db.execute(sched_stmt)
            schedule = sched_res.scalars().first()
            if schedule: await db.delete(schedule)
            curr += timedelta(days=1)
            
        # 2. Apply New
        new_start = start_date if start_date else req.start_date
        new_end = end_date if end_date else req.end_date
        new_type = leave_type if leave_type else req.leave_type
        
        # Check validation
        if new_start > new_end:
             raise HTTPException(status_code=400, detail="Start date after end date")

        new_days = 0
        if new_type == "paid_leave":
            new_days = calculate_working_days_count(new_start, new_end)
            balance = await get_leave_balance(db, req.user_id, new_start.year)
            if balance.used_days + new_days > balance.total_days:
                 raise HTTPException(status_code=400, detail="Insufficient leave balance for update")
            balance.used_days += new_days
            db.add(balance)

        # Update Request
        req.start_date = new_start
        req.end_date = new_end
        req.leave_type = new_type
        if reason: req.reason = reason
        
        # Update Schedule (Create new shifts)
        target_shift = await get_shift_by_type(db, new_type)
        if target_shift:
            curr = new_start
            while curr <= new_end:
                if curr.weekday() < 5:
                    new_sched = WorkSchedule(user_id=req.user_id, shift_id=target_shift.id, date=curr)
                    db.add(new_sched)
                curr += timedelta(days=1)

        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

async def update_leave_balance(db: AsyncSession, user_id: int, year: int, total_days: int = None, used_days: int = None):
    balance = await get_leave_balance(db, user_id, year)
    if total_days is not None:
        balance.total_days = total_days
    if used_days is not None:
        balance.used_days = used_days
        
    db.add(balance)
    await db.commit()
    await db.refresh(balance)
    return balance

# --- Organization Structure CRUD ---

from backend.database.models import Company, Department, Position

async def get_companies(db: AsyncSession):
    result = await db.execute(select(Company))
    return result.scalars().all()

async def create_company(db: AsyncSession, name: str):
    company = Company(name=name)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

async def get_departments(db: AsyncSession, company_id: Optional[int] = None):
    query = select(Department)
    if company_id:
        query = query.where(Department.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().all()

async def create_department(db: AsyncSession, name: str, company_id: Optional[int] = None):
    dept = Department(name=name, company_id=company_id)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

async def get_positions(db: AsyncSession, department_id: Optional[int] = None):
    query = select(Position)
    if department_id:
        query = query.where(Position.department_id == department_id)
    result = await db.execute(query)
    return result.scalars().all()

async def create_position(db: AsyncSession, title: str, department_id: Optional[int] = None):
    pos = Position(title=title, department_id=department_id)
    db.add(pos)
    await db.commit()
    await db.refresh(pos)
    return pos

# --- Global Settings ---

async def get_global_setting(db: AsyncSession, key: str):
    result = await db.execute(select(GlobalSetting).where(GlobalSetting.key == key))
    setting = result.scalars().first()
    return setting.value if setting else None

async def set_global_setting(db: AsyncSession, key: str, value: str):
    result = await db.execute(select(GlobalSetting).where(GlobalSetting.key == key))
    setting = result.scalars().first()
    
    if setting:
        setting.value = value
    else:
        setting = GlobalSetting(key=key, value=value)
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    return setting

async def is_smtp_configured(db: AsyncSession) -> bool:
    server = await get_global_setting(db, "smtp_server")
    port = await get_global_setting(db, "smtp_port")
    sender = await get_global_setting(db, "sender_email")
    # If any of these are missing, SMTP is not considered configured
    return bool(server and port and sender)

# --- Bonus & Monthly Config ---

async def create_bonus(db: AsyncSession, user_id: int, amount: float, date: datetime.date, description: str = None):
    from backend.database.models import Bonus
    bonus = Bonus(user_id=user_id, amount=amount, date=date, description=description)
    db.add(bonus)
    await db.commit()
    await db.refresh(bonus)
    return bonus

async def delete_bonus(db: AsyncSession, bonus_id: int):
    from backend.database.models import Bonus
    result = await db.execute(select(Bonus).where(Bonus.id == bonus_id))
    bonus = result.scalars().first()
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    
    await db.delete(bonus)
    await db.commit()
    return True

async def set_monthly_work_days(db: AsyncSession, year: int, month: int, days_count: int):
    from backend.database.models import MonthlyWorkDays
    # Check if exists
    result = await db.execute(
        select(MonthlyWorkDays)
        .where(MonthlyWorkDays.year == year)
        .where(MonthlyWorkDays.month == month)
    )
    obj = result.scalars().first()
    
    if obj:
        obj.days_count = days_count
    else:
        obj = MonthlyWorkDays(year=year, month=month, days_count=days_count)
        db.add(obj)
    
    await db.commit()
    await db.refresh(obj)
    return obj

async def get_monthly_work_days(db: AsyncSession, year: int, month: int):
    from backend.database.models import MonthlyWorkDays
    result = await db.execute(
        select(MonthlyWorkDays)
        .where(MonthlyWorkDays.year == year)
        .where(MonthlyWorkDays.month == month)
    )
    return result.scalars().first()

# --- Auth Key Management ---

import secrets
import uuid

async def get_active_auth_key(db: AsyncSession) -> AuthKey:
    result = await db.execute(
        select(AuthKey).where(AuthKey.state == "active").order_by(AuthKey.created_at.desc())
    )
    key = result.scalars().first()
    if not key:
        # Generate initial key if none exists
        key = await rotate_auth_key(db)
    return key

async def get_auth_key_by_kid(db: AsyncSession, kid: str) -> Optional[AuthKey]:
    result = await db.execute(select(AuthKey).where(AuthKey.kid == kid))
    return result.scalars().first()

async def rotate_auth_key(db: AsyncSession) -> AuthKey:
    from sqlalchemy import update
    # Mark old active keys as legacy
    await db.execute(
        update(AuthKey).where(AuthKey.state == "active").values(state="legacy")
    )
    
    # Create new active key
    new_key = AuthKey(
        kid=str(uuid.uuid4()),
        secret=secrets.token_urlsafe(64),
        algorithm="HS256",
        state="active"
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    return new_key

async def cleanup_old_auth_keys(db: AsyncSession, retention_days: int = 90):
    """Delete legacy keys older than retention_days."""
    from datetime import timedelta
    cutoff_date = sofia_now() - timedelta(days=retention_days)
    
    await db.execute(
        delete(AuthKey)
        .where(AuthKey.state == "legacy")
        .where(AuthKey.created_at < cutoff_date)
    )
    await db.commit()
    return True

# --- User Session Management ---

async def create_user_session(
    db: AsyncSession, 
    user_id: int, 
    refresh_token_jti: str, 
    expires_at: datetime,
    ip_address: str = None,
    user_agent: str = None
):
    session = UserSession(
        user_id=user_id,
        refresh_token_jti=refresh_token_jti,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def get_user_session_by_jti(db: AsyncSession, jti: str) -> Optional[UserSession]:
    result = await db.execute(
        select(UserSession).where(UserSession.refresh_token_jti == jti)
    )
    return result.scalars().first()

async def invalidate_user_session(db: AsyncSession, jti: str):
    session = await get_user_session_by_jti(db, jti)
    if session:
        session.is_active = False
        db.add(session)
        await db.commit()
    return True

async def invalidate_session_by_id(db: AsyncSession, session_id: int):
    stmt = select(UserSession).where(UserSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalars().first()
    if session:
        session.is_active = False
        db.add(session)
        await db.commit()
        return True
    return False

async def get_active_sessions(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(UserSession).where(UserSession.is_active == True).order_by(UserSession.last_used_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def invalidate_all_user_sessions(db: AsyncSession, user_id: int):
    from sqlalchemy import update
    await db.execute(
        update(UserSession).where(UserSession.user_id == user_id).values(is_active=False)
    )
    await db.commit()
    return True

# --- Login Security ---

async def increment_login_attempts(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        # Get Config (Default: 5 attempts, 15 min lock)
        max_attempts_str = await get_global_setting(db, "security_max_login_attempts")
        max_attempts = int(max_attempts_str) if max_attempts_str else 5
        
        lockout_mins_str = await get_global_setting(db, "security_lockout_minutes")
        lockout_mins = int(lockout_mins_str) if lockout_mins_str else 15

        # Lockout logic
        if user.failed_login_attempts >= max_attempts:
             from datetime import timedelta
             user.locked_until = sofia_now() + timedelta(minutes=lockout_mins)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

async def reset_login_attempts(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user:
        if user.failed_login_attempts != 0 or user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.add(user)
            await db.commit()
    return user

