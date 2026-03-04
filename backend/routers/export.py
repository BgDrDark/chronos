from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import get_db
from backend import crud
from backend.auth import jwt_utils
from backend.database.models import User, TimeLog, Payslip, WorkSchedule, Shift, Bonus, LeaveRequest
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import datetime
from urllib.parse import quote
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from backend.services.payroll_calculator import PayrollCalculator

from backend.auth.module_guard import require_module_dep

router = APIRouter(
    prefix="/export", 
    tags=["export"],
    dependencies=[Depends(require_module_dep("salaries"))]
)

# Register Fonts for Cyrillic support
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    DEFAULT_FONT = 'DejaVuSans'
    BOLD_FONT = 'DejaVuSans-Bold'
except Exception as e:
    print(f"Warning: Could not register Cyrillic fonts: {e}")
    DEFAULT_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'

@router.get("/payroll/xlsx")
async def export_payroll_xlsx(
    start_date: datetime.date,
    end_date: datetime.date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    """
    Exports a comprehensive payroll report for ALL active users in the given period to Excel.
    """
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can export full payroll data")

    # 1. Fetch all active users
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()

    # 2. Setup Excel Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Ведомост"

    # Header Row
    headers = [
        "Служител", "Имейл", "Длъжност", "Редовни часове", "Извънредни часове", 
        "Болнични (дни)", "Отпуск (дни)", "Сума Редовни", "Сума Извънредни", 
        "Бонуси", "Бруто", "Осигуровки", "ДДФЛ", "НЕТО ЗА ПОЛУЧАВАНЕ", "Валута"
    ]
    ws.append(headers)

    # Style Header
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    header_font = Font(bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # 3. Calculate data for each user
    calculator = PayrollCalculator(db)
    # Convert dates to datetime for calculator
    start_dt = datetime.datetime.combine(start_date, datetime.time.min)
    end_dt = datetime.datetime.combine(end_date, datetime.time.max)

    for employee in users:
        try:
            res = await calculator.calculate(employee.id, start_dt, end_dt)
            
            # Get currency
            payroll_config = await crud.get_payroll_config(db, employee.id)
            currency = payroll_config.currency if hasattr(payroll_config, 'currency') else "EUR"
            
            # Aggregated totals
            gross = res["regular_amount"] + res["overtime_amount"] + res["bonus_amount"]
            
            ws.append([
                f"{employee.first_name} {employee.last_name}",
                employee.email,
                employee.job_title or "-",
                res["total_regular_hours"],
                res["total_overtime_hours"],
                res["sick_days"],
                res["leave_days"],
                res["regular_amount"],
                res["overtime_amount"],
                res["bonus_amount"],
                round(gross, 2),
                res["insurance_amount"],
                res["tax_amount"],
                res["total_amount"],
                currency
            ])
        except Exception as e:
            # Skip or log error for specific user to not break full export
            ws.append([f"{employee.first_name} {employee.last_name}", employee.email, "ГРЕШКА ПРИ ИЗЧИСЛЕНИЕ", str(e)])

    # Auto-adjust column width
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    # 4. Stream response
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"payroll_{start_date}_to_{end_date}.xlsx"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/payslip/{payslip_id}/pdf")
async def export_payslip_pdf(
    payslip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    # 1. Fetch Payslip
    result = await db.execute(select(Payslip).where(Payslip.id == payslip_id))
    payslip = result.scalars().first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    # 2. Permissions Check
    if current_user.role.name not in ["admin", "super_admin"] and current_user.id != payslip.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 3. Fetch User & Data
    user_res = await db.execute(select(User).where(User.id == payslip.user_id))
    employee = user_res.scalars().first()

    # Fetch Logs
    logs_res = await db.execute(
        select(TimeLog)
        .where(TimeLog.user_id == payslip.user_id)
        .where(TimeLog.start_time >= payslip.period_start)
        .where(TimeLog.start_time <= payslip.period_end)
        .order_by(TimeLog.start_time.asc())
    )
    logs = logs_res.scalars().all()

    # Fetch Bonuses
    bonus_res = await db.execute(
        select(Bonus)
        .where(Bonus.user_id == payslip.user_id)
        .where(Bonus.date >= payslip.period_start.date())
        .where(Bonus.date <= payslip.period_end.date())
    )
    bonuses = bonus_res.scalars().all()

    # Fetch Leaves
    leave_res = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.user_id == payslip.user_id)
        .where(LeaveRequest.status == "approved")
        .where(or_(
            and_(LeaveRequest.start_date >= payslip.period_start.date(), LeaveRequest.start_date <= payslip.period_end.date()),
            and_(LeaveRequest.end_date >= payslip.period_start.date(), LeaveRequest.end_date <= payslip.period_end.date())
        ))
    )
    leaves = leave_res.scalars().all()

    # Fetch Schedules
    sched_res = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.user_id == payslip.user_id)
        .where(WorkSchedule.date >= payslip.period_start.date())
        .where(WorkSchedule.date <= payslip.period_end.date())
        .options(selectinload(WorkSchedule.shift))
    )
    schedules_data = {s.date: s.shift for s in sched_res.scalars().all() if s.shift}

    # 4. Fetch Currency
    payroll_config = await crud.get_payroll_config(db, payslip.user_id)
    currency = payroll_config.currency if hasattr(payroll_config, 'currency') else "EUR"

    # 5. Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Update ALL styles to use Cyrillic-compatible font
    for style_name in styles.byName:
        style = styles[style_name]
        if 'Bold' in style_name or 'Title' in style_name or 'Heading' in style_name:
            style.fontName = BOLD_FONT
        else:
            style.fontName = DEFAULT_FONT
    
    # Standard stylesheet already has 'Italic', just update its font
    if 'Italic' in styles:
        styles['Italic'].fontName = DEFAULT_FONT
    else:
        # Fallback in case it's missing in some environments
        styles.add(styles['Normal'].clone('Italic'))
        styles['Italic'].fontName = DEFAULT_FONT

    # Title
    elements.append(Paragraph(f"ФИШ ЗА ЗАПЛАТА / ДЕТАЙЛЕН ОТЧЕТ", styles['Title']))
    elements.append(Spacer(1, 12))

    # Info
    elements.append(Paragraph(f"<b>Служител:</b> {employee.first_name} {employee.last_name} ({employee.email})", styles['Normal']))
    elements.append(Paragraph(f"<b>Период:</b> {payslip.period_start.date()} до {payslip.period_end.date()}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # --- TABLE DATA PREPARATION ---
    # Merge logs and leaves into a chronological list of events
    events = []
    
    for log in logs:
        events.append({
            "date": log.start_time.date(),
            "type": "log",
            "obj": log
        })
    
    # Expand leaves into days
    from datetime import timedelta
    for leave in leaves:
        curr = leave.start_date
        while curr <= leave.end_date:
            if curr >= payslip.period_start.date() and curr <= payslip.period_end.date():
                if curr.weekday() < 5: 
                    events.append({
                        "date": curr,
                        "type": "leave",
                        "obj": leave
                    })
            curr += timedelta(days=1)
            
    # Sort events
    events.sort(key=lambda x: (x["date"], x["obj"].start_time if x["type"] == "log" else datetime.time.min))

    # Table Header
    data = [["Дата", "Смяна", "Тип", "Вход", "Изход", "Почивка", "Извънр.", "Общо"]]
    
    for event in events:
        date = event["date"]
        shift_obj = schedules_data.get(date)
        shift_name = shift_obj.name if shift_obj else "-"
        
        if event["type"] == "log":
            log = event["obj"]
            entry_type = "Ръчен" if log.is_manual else "Авт."
            
            in_time = log.start_time.strftime("%H:%M")
            out_time = log.end_time.strftime("%H:%M") if log.end_time else "Активен"
            
            duration = datetime.timedelta()
            ot_seconds = 0
            
            if log.end_time:
                duration = log.end_time - log.start_time
                if log.break_duration_minutes:
                    duration -= datetime.timedelta(minutes=log.break_duration_minutes)
                
                net_duration_seconds = duration.total_seconds()
                
                if shift_obj and shift_obj.shift_type == "regular":
                    s_start = datetime.datetime.combine(date, shift_obj.start_time)
                    s_end = datetime.datetime.combine(date, shift_obj.end_time)
                    if s_end < s_start: s_end += timedelta(days=1)
                    
                    overlap_start = max(log.start_time, s_start)
                    overlap_end = min(log.end_time, s_end)
                    
                    overlap_seconds = 0
                    if overlap_end > overlap_start:
                        overlap_seconds = (overlap_end - overlap_start).total_seconds()
                    
                    reg_seconds = max(0, overlap_seconds - (log.break_duration_minutes * 60))
                    ot_seconds = max(0, net_duration_seconds - reg_seconds)
                else:
                    ot_seconds = net_duration_seconds

            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            dur_str = f"{int(hours)}ч {int(minutes)}м"
            
            ot_h, ot_rem = divmod(ot_seconds, 3600)
            ot_m, _ = divmod(ot_rem, 60)
            ot_str = f"{int(ot_h)}ч {int(ot_m)}м" if ot_seconds > 0 else "-"
            
            data.append([
                date.strftime("%Y-%m-%d"),
                shift_name,
                entry_type,
                in_time,
                out_time,
                f"{log.break_duration_minutes}м",
                ot_str,
                dur_str
            ])
            
        elif event["type"] == "leave":
            leave = event["obj"]
            leave_name = "Платен" if leave.leave_type == "paid_leave" else ("Болничен" if leave.leave_type == "sick_leave" else "Неплатен")
            data.append([
                date.strftime("%Y-%m-%d"),
                shift_name,
                leave_name,
                "-", "-", "-", "-", "8ч 00м"
            ])

    # Style Table
    t = Table(data, colWidths=[65, 75, 55, 45, 45, 50, 55, 55])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # --- SUMMARY SECTION ---
    elements.append(Paragraph(f"<b>ОБОБЩЕНИЕ</b>", styles['Heading2']))
    
    # Calc Leave Days
    paid_days = sum(1 for e in events if e["type"] == "leave" and e["obj"].leave_type == "paid_leave")
    sick_days = sum(1 for e in events if e["type"] == "leave" and e["obj"].leave_type == "sick_leave")
    
    elements.append(Paragraph(f"<b>Редовни часове:</b> {payslip.total_regular_hours} ч.", styles['Normal']))
    elements.append(Paragraph(f"<b>Извънредни часове:</b> {payslip.total_overtime_hours} ч.", styles['Normal']))
    elements.append(Paragraph(f"<b>Използван платен отпуск:</b> {paid_days} дни", styles['Normal']))
    elements.append(Paragraph(f"<b>Болнични дни:</b> {sick_days} дни", styles['Normal']))
    
    total_bonus = sum(b.amount for b in bonuses)
    if total_bonus > 0:
        elements.append(Paragraph(f"<b>Бонуси:</b> {total_bonus:.2f} {currency}", styles['Normal']))
        for b in bonuses:
             elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;- {b.date}: {b.amount:.2f} ({b.description or 'N/A'})", styles['Italic']))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>СУМА ЗА ПОЛУЧАВАНЕ:</b> {payslip.total_amount} {currency}", styles['Heading2']))
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"Генерирано на: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Italic']))

    doc.build(elements)
    
    buffer.seek(0)
    import re
    ascii_last_name = re.sub(r'[^\x00-\x7F]+', '', employee.last_name) or "employee"
    safe_filename = f"report_{ascii_last_name}_{payslip_id}.pdf"
    full_filename = f"report_{employee.last_name}_{payslip_id}.pdf"
    encoded_filename = quote(full_filename)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
        }
    )
