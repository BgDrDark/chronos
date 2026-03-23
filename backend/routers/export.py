from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import get_db
from backend import crud
from backend.auth import jwt_utils
from backend.database.models import User, TimeLog, Payslip, WorkSchedule, Shift, Bonus, LeaveRequest, EmploymentContract, ContractAnnex, ContractTemplate, ContractTemplateVersion, ContractTemplateSection, Invoice, InvoiceItem, Company
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
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

import qrcode
from io import BytesIO

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
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/annex/{annex_id}/pdf")
async def export_annex_pdf(
    annex_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    """Генерира PDF на допълнително споразумение."""
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can export annexes")

    result = await db.execute(select(ContractAnnex).where(ContractAnnex.id == annex_id))
    annex = result.scalars().first()
    if not annex:
        raise HTTPException(status_code=404, detail="Annex not found")

    contract_result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == annex.contract_id)
    )
    contract = contract_result.scalars().first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()

    for style_name in styles.byName:
        style = styles[style_name]
        if 'Bold' in style_name or 'Title' in style_name or 'Heading' in style_name:
            style.fontName = BOLD_FONT
        else:
            style.fontName = DEFAULT_FONT

    if 'Italic' in styles:
        styles['Italic'].fontName = DEFAULT_FONT
    else:
        styles.add(styles['Normal'].clone('Italic'))
        styles['Italic'].fontName = DEFAULT_FONT

    elements.append(Paragraph("ДОПЪЛНИТЕЛНО СПОРАЗУМЕНИЕ", styles['Title']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Към трудов договор", styles['Normal']))
    elements.append(Spacer(1, 16))

    if contract.company:
        elements.append(Paragraph(f"<b>{contract.company.name}</b>", styles['Normal']))
        if contract.company.address:
            elements.append(Paragraph(f"Адрес: {contract.company.address}", styles['Normal']))
        if contract.company.mol_name:
            elements.append(Paragraph(f"Представляван от: {contract.company.mol_name}", styles['Normal']))
        elements.append(Spacer(1, 12))

    if contract.contract_number:
        elements.append(Paragraph(f"<b>Към Договор №:</b> {contract.contract_number}", styles['Normal']))
    if annex.annex_number:
        elements.append(Paragraph(f"<b>Споразумение №:</b> {annex.annex_number}", styles['Normal']))
    elements.append(Paragraph(f"<b>Дата на влизане в сила:</b> {annex.effective_date.strftime('%d.%m.%Y') if annex.effective_date else 'N/A'}", styles['Normal']))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>СТРАНИ ПО СПОРАЗУМЕНИЕТО</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))

    employee_name = contract.employee_name or (current_user.first_name + " " + current_user.last_name if contract.user_id == current_user.id else "N/A")
    employee_egn = contract.employee_egn or (current_user.egn if contract.user_id == current_user.id else "N/A")

    elements.append(Paragraph(f"<b>Работодател:</b> {contract.company.name if contract.company else 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"<b>Работник:</b> {employee_name}, ЕГН: {employee_egn}", styles['Normal']))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>ИЗМЕНЕНИЯ И ДОПЪЛНЕНИЯ</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))

    if annex.change_type:
        change_type_display = {
            'salary_increase': 'Повишение на основната месечна заплата',
            'salary_decrease': 'Намаление на основната месечна заплата',
            'position_change': 'Промяна на длъжността',
            'hours_change': 'Промяна на работното време',
            'other': 'Други изменения'
        }.get(annex.change_type, annex.change_type)
        elements.append(Paragraph(f"<b>Вид изменение:</b> {change_type_display}", styles['Normal']))

    if annex.change_description:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Описание:</b> {annex.change_description}", styles['Normal']))

    if annex.base_salary:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Нова основна месечна заплата:</b> {float(annex.base_salary):.2f} лв.", styles['Normal']))

    if annex.work_hours_per_week:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Ново работно време:</b> {annex.work_hours_per_week} часа седмично", styles['Normal']))

    if annex.night_work_rate:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Множител за нощен труд:</b> {annex.night_work_rate}", styles['Normal']))

    if annex.overtime_rate:
        elements.append(Paragraph(f"<b>Множител за извънреден труд:</b> {annex.overtime_rate}", styles['Normal']))

    if annex.holiday_rate:
        elements.append(Paragraph(f"<b>Множител за работа на официални празници:</b> {annex.holiday_rate}", styles['Normal']))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>ПОДПИСИ</b>", styles['Heading2']))
    elements.append(Spacer(1, 36))

    elements.append(Paragraph("_" * 40 + "            " + "_" * 40, styles['Normal']))
    elements.append(Paragraph("Работодател                                      Работник", styles['Normal']))
    elements.append(Spacer(1, 12))

    if annex.signed_at:
        elements.append(Paragraph(f"<i>Подписано на: {annex.signed_at.strftime('%d.%m.%Y %H:%M')}</i>", styles['Normal']))
    elif annex.status == 'signed':
        elements.append(Paragraph("<i>(Очаква подписване)</i>", styles['Normal']))

    doc.build(elements)

    buffer.seek(0)
    safe_filename = f"annex_{annex_id}.pdf"
    encoded_filename = quote(safe_filename)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
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


@router.get("/contract/{contract_id}/pdf")
async def export_contract_pdf(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    """
    Генерира PDF на трудов договор.
    """
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can export contracts")

    result = await db.execute(select(EmploymentContract).where(EmploymentContract.id == contract_id))
    contract = result.scalars().first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    company_result = await db.execute(select(User.company_rel).where(User.id == current_user.id))
    company = company_result.scalars().first()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()

    for style_name in styles.byName:
        style = styles[style_name]
        if 'Bold' in style_name or 'Title' in style_name or 'Heading' in style_name:
            style.fontName = BOLD_FONT
        else:
            style.fontName = DEFAULT_FONT

    if 'Italic' in styles:
        styles['Italic'].fontName = DEFAULT_FONT
    else:
        styles.add(styles['Normal'].clone('Italic'))
        styles['Italic'].fontName = DEFAULT_FONT

    contract_type_display = {
        'full_time': 'ТРУДОВ ДОГОВОР ЗА НЕОПРЕДЕЛЕНО РАБОТНО ВРЕМЕ',
        'part_time': 'ТРУДОВ ДОГОВОР ЗА ОПРЕДЕЛЕНО РАБОТНО ВРЕМЕ',
        'contractor': 'ГРАЖДАНСКИ ДОГОВОР',
        'internship': 'ДОГОВОР ЗА СТАЖ'
    }.get(contract.contract_type, 'ТРУДОВ ДОГОВОР')

    elements.append(Paragraph("ИМЕТО НА РАБОТОДАТЕЛЯ", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    if contract.company:
        elements.append(Paragraph(f"<b>{contract.company.name}</b>", styles['Heading2']))
        if contract.company.address:
            elements.append(Paragraph(f"Адрес: {contract.company.address}", styles['Normal']))
        if contract.company.mol_name:
            elements.append(Paragraph(f"Представляван от: {contract.company.mol_name}", styles['Normal']))
        if contract.company.eik:
            elements.append(Paragraph(f"ЕИК: {contract.company.eik}", styles['Normal']))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"<b>{contract_type_display}</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    if contract.contract_number:
        elements.append(Paragraph(f"<b>Договор №:</b> {contract.contract_number}", styles['Normal']))
    elements.append(Paragraph(f"<b>Дата на сключване:</b> {contract.start_date.strftime('%d.%m.%Y') if contract.start_date else 'N/A'}", styles['Normal']))
    if contract.end_date:
        elements.append(Paragraph(f"<b>Срок до:</b> {contract.end_date.strftime('%d.%m.%Y')}", styles['Normal']))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>РАБОТНИК</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))

    employee_name = contract.employee_name or (f"{current_user.first_name} {current_user.last_name}" if contract.user_id == current_user.id else "N/A")
    employee_egn = contract.employee_egn or (current_user.egn if contract.user_id == current_user.id else "N/A")

    elements.append(Paragraph(f"<b>Име:</b> {employee_name}", styles['Normal']))
    elements.append(Paragraph(f"<b>ЕГН:</b> {employee_egn}", styles['Normal']))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>УСЛОВИЯ НА ТРУД</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))

    work_hours_display = {40: 'Пълно работно време (40 часа седмично)', 20: 'Непълно работно време (20 часа седмично)'}.get(contract.work_hours_per_week or 40, f'{contract.work_hours_per_week} часа седмично')
    elements.append(Paragraph(f"<b>Работно време:</b> {work_hours_display}", styles['Normal']))

    if contract.base_salary:
        elements.append(Paragraph(f"<b>Основна заплата:</b> {contract.base_salary} лв.", styles['Normal']))

    if contract.probation_months and contract.probation_months > 0:
        elements.append(Paragraph(f"<b>Изпитателен срок:</b> {contract.probation_months} месеца", styles['Normal']))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>ПОДПИСИ</b>", styles['Heading2']))
    elements.append(Spacer(1, 36))

    elements.append(Paragraph("_" * 40 + "            " + "_" * 40, styles['Normal']))
    elements.append(Paragraph("Работодател                                      Работник", styles['Normal']))
    elements.append(Spacer(1, 12))

    if contract.signed_at:
        elements.append(Paragraph(f"<i>Подписан на: {contract.signed_at.strftime('%d.%m.%Y %H:%M')}</i>", styles['Normal']))

    doc.build(elements)

    buffer.seek(0)
    safe_filename = f"contract_{contract_id}.pdf"
    encoded_filename = quote(safe_filename)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/invoice/{invoice_id}/pdf")
async def export_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    """
    Генерира PDF на фактура.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        result = await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.supplier))
            .where(Invoice.id == invoice_id)
        )
        invoice = result.scalars().first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Нямате достъп до тази фактура")

        items_result = await db.execute(
            select(InvoiceItem)
            .options(selectinload(InvoiceItem.ingredient))
            .where(InvoiceItem.invoice_id == invoice_id)
        )
        items = items_result.scalars().all()

        company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
        company = company_result.scalars().first()
        
        logger.info(f"Generating PDF for invoice {invoice_id}: number={invoice.number}, items_count={len(items)}, total={invoice.total}, company={company.name if company else None}")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        for style_name in styles.byName:
            style = styles[style_name]
            if 'Bold' in style_name or 'Title' in style_name or 'Heading' in style_name:
                style.fontName = BOLD_FONT
            else:
                style.fontName = DEFAULT_FONT

        if 'Italic' in styles:
            styles['Italic'].fontName = DEFAULT_FONT
        else:
            styles.add(styles['Normal'].clone('Italic'))
            styles['Italic'].fontName = DEFAULT_FONT

        # Заглавна част - ФАКТУРА
        elements.append(Paragraph("<b>ФАКТУРА</b>", styles['Title']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>№ {invoice.number or invoice.id}</b>", styles['Normal']))
        elements.append(Paragraph(f"Дата: {invoice.date.strftime('%d.%m.%Y') if invoice.date else 'N/A'}", styles['Normal']))
        elements.append(Paragraph(f"<b>{invoice.griff or 'ОРИГИНАЛ'}</b>", styles['Normal']))

        elements.append(Spacer(1, 12))

        # ИЗДАТЕЛ и ПОЛУЧАТЕЛ
        if invoice.type == 'incoming':
            issuer_name = invoice.supplier.name if invoice.supplier else '-'
            issuer_address = getattr(invoice.supplier, 'address', '-') if invoice.supplier else '-'
            issuer_eik = getattr(invoice.supplier, 'eik', '-') if invoice.supplier else '-'
            issuer_vat = getattr(invoice.supplier, 'vat_number', '-') if invoice.supplier else '-'
            
            recipient_name = company.name if company else '-'
            recipient_address = company.address if company else '-'
            recipient_eik = company.eik if company else '-'
            recipient_vat = getattr(company, 'vat_number', '-') if company else '-'
        else:
            issuer_name = company.name if company else '-'
            issuer_address = company.address if company else '-'
            issuer_eik = company.eik if company else '-'
            issuer_vat = getattr(company, 'vat_number', '-') if company else '-'
            
            recipient_name = invoice.client_name or '-'
            recipient_address = invoice.client_address or '-'
            recipient_eik = invoice.client_eik or '-'
            recipient_vat = getattr(invoice, 'client_vat_number', '-') or '-'

        party_table_data = [
            ['<b>ИЗДАТЕЛ</b>', '<b>ПОЛУЧАТЕЛ</b>'],
            [issuer_name, recipient_name],
            [f'Адрес: {issuer_address}' if issuer_address != '-' else '-', f'Адрес: {recipient_address}' if recipient_address != '-' else '-'],
            [f'ЕИК: {issuer_eik}' if issuer_eik != '-' else '-', f'ЕИК: {recipient_eik}' if recipient_eik != '-' else '-'],
            [f'ИН по ЗДДС: {issuer_vat}' if issuer_vat != '-' else '-', f'ИН по ЗДДС: {recipient_vat}' if recipient_vat != '-' else '-'],
        ]
        
        party_table = Table([[Paragraph(cell, styles['Normal']) for cell in row] for row in party_table_data], 
                          colWidths=[250, 250])
        party_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(party_table)

        elements.append(Spacer(1, 12))

        # Таблица с артикули
        vat_rate = float(invoice.vat_rate) if invoice.vat_rate else 20
        
        table_data = [['№', 'Наименование', 'К-во', 'Ед.мярка', 'Цена без ДДС', 'Цена със ДДС', 'Партида', 'Годност', 'ДДС %', 'Сума']]
        
        for idx, item in enumerate(items, 1):
            item_name = item.name or (item.ingredient.name if item.ingredient else f"Артикул {item.id}")
            unit_price = float(item.unit_price) if item.unit_price else 0
            unit_price_vat = float(item.unit_price_with_vat) if item.unit_price_with_vat else None
            batch_num = item.batch_number or ''
            expiry = item.expiration_date.strftime('%d.%m.%Y') if item.expiration_date else ''
            item_total = float(item.total) if item.total else 0
            
            table_data.append([
                str(idx),
                item_name[:35],
                f"{float(item.quantity):.3f}" if item.quantity else '',
                item.unit or 'бр.',
                f"{unit_price:.2f}" if unit_price else '',
                f"{unit_price_vat:.2f}" if unit_price_vat else '',
                batch_num,
                expiry,
                f"{vat_rate:.0f}%",
                f"{item_total:.2f}" if item_total else ''
            ])

        # Крайни суми
        subtotal = float(invoice.subtotal) if invoice.subtotal else 0
        vat_amount = float(invoice.vat_amount) if invoice.vat_amount else 0
        total_amount = float(invoice.total) if invoice.total else 0
        
        table_data.append(['', '', '', '', '', '', '', '', 'Сума:', f"{subtotal:.2f}"])
        table_data.append(['', '', '', '', '', '', '', '', f'ДДС {vat_rate:.0f}%:', f"{vat_amount:.2f}"])
        table_data.append(['', '', '', '', '', '', '', '', '<b>ОБЩО:</b>', f"<b>{total_amount:.2f}</b>"])

        items_table = Table(table_data, colWidths=[20, 130, 45, 45, 60, 60, 55, 55, 35, 55])
        
        # Стил за таблицата с артикули
        table_style = [
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEBELOW', (0, -3), (-1, -3), 1, colors.black),
            ('FONTNAME', (8, -2), (8, -1), BOLD_FONT),
            ('FONTNAME', (9, -2), (9, -1), BOLD_FONT),
            ('FONTSIZE', (8, -2), (9, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        
        # Подчертай последните 3 реда
        for i in range(1, 4):
            row_idx = -i
            table_style.append(('BACKGROUND', (8, row_idx), (9, row_idx), colors.Color(0.95, 0.95, 0.95)))
        
        items_table.setStyle(TableStyle(table_style))
        elements.append(items_table)

        elements.append(Spacer(1, 16))

        # Дати и плащане
        if invoice.payment_method:
            elements.append(Paragraph(f"<b>Начин на плащане:</b> {invoice.payment_method}", styles['Normal']))
        if invoice.due_date:
            elements.append(Paragraph(f"<b>Срок на плащане:</b> {invoice.due_date.strftime('%d.%m.%Y')}", styles['Normal']))
        if getattr(invoice, 'payment_date', None):
            elements.append(Paragraph(f"<b>Дата на плащане:</b> {invoice.payment_date.strftime('%d.%m.%Y')}", styles['Normal']))
        if invoice.notes:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(f"<b>Бележки:</b> {invoice.notes}", styles['Normal']))

        elements.append(Spacer(1, 20))

        # QR код
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(f"BULSTAT:{issuer_eik};INV:{invoice.number};DATE:{invoice.date.strftime('%Y%m%d') if invoice.date else ''};SUM:{total_amount:.2f}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            qr_image = Image(qr_buffer, width=60, height=60)
            elements.append(qr_image)
            elements.append(Paragraph(f"QR код: {invoice.number}", styles['Normal']))
        except Exception as qr_error:
            logger.warning(f"Failed to generate QR code: {qr_error}")

        # Подписи
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("_" * 60 + "                    " + "_" * 40, styles['Normal']))
        elements.append(Paragraph("За издателя                              За получателя", styles['Normal']))

        doc.build(elements)

        buffer.seek(0)
        safe_filename = f"invoice_{invoice.number or invoice_id}.pdf"
        encoded_filename = quote(safe_filename)

        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {invoice_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Грешка при генериране на PDF: {str(e)}")
