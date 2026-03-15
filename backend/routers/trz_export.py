from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.database import get_db
from backend.database.models import (
    User, Company, EmploymentContract, ContractAnnex, ContractTemplate, 
    ContractTemplateVersion, ContractTemplateSection,
    AnnexTemplate, AnnexTemplateVersion, AnnexTemplateSection
)
from backend.auth import jwt_utils
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import datetime

router = APIRouter(
    prefix="/export",
    tags=["trz-export"],
)

try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    DEFAULT_FONT = 'DejaVuSans'
    BOLD_FONT = 'DejaVuSans-Bold'
except Exception:
    DEFAULT_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'


def get_company_header(company: Company) -> str:
    header = f"<b>{company.name}</b><br/>"
    if company.eik:
        header += f"ЕИК: {company.eik}<br/>"
    if company.address:
        header += f"Адрес: {company.address}<br/>"
    return header


@router.get("/contract/{contract_id}/pdf")
async def export_contract_pdf(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(EmploymentContract).where(EmploymentContract.id == contract_id))
    contract = result.scalars().first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    user_result = await db.execute(select(User).where(User.id == contract.user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    company_result = await db.execute(select(Company).where(Company.id == contract.company_id))
    company = company_result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    sections = []
    if contract.template_id:
        version_result = await db.execute(
            select(ContractTemplateVersion).where(
                ContractTemplateVersion.template_id == contract.template_id,
                ContractTemplateVersion.is_current == True
            )
        )
        version = version_result.scalar_one_or_none()
        if version:
            sections_result = await db.execute(
                select(ContractTemplateSection).where(
                    ContractTemplateSection.version_id == version.id
                ).order_by(ContractTemplateSection.order_index)
            )
            sections = sections_result.scalars().all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()
    
    for style_name in styles.byName:
        style = styles[style_name]
        if hasattr(style, 'fontName'):
            style.fontName = DEFAULT_FONT
        if hasattr(style, 'headingFontName'):
            style.headingFontName = BOLD_FONT

    title_style = styles['Title']
    title_style.fontName = BOLD_FONT
    title_style.fontSize = 16
    
    heading_style = styles['Heading2']
    heading_style.fontName = BOLD_FONT
    heading_style.fontSize = 12

    normal_style = styles['Normal']
    normal_style.fontName = DEFAULT_FONT
    normal_style.fontSize = 10
    normal_style.leading = 14

    elements.append(Paragraph(get_company_header(company), normal_style))
    elements.append(Spacer(1, 20))

    contract_type_label = {
        "full_time": "ТРУДОВ ДОГОВОР - ПЪЛНО РАБОТНО ВРЕМЕ",
        "part_time": "ТРУДОВ ДОГОВОР - НЕПЪЛНО РАБОТНО ВРЕМЕ",
        "contractor": "ГРАЖДАНСКИ ДОГОВОР",
        "internship": "ДОГОВОР ЗА СТАЖ"
    }.get(contract.contract_type, "ТРУДОВ ДОГОВОР")

    elements.append(Paragraph(contract_type_label, title_style))
    elements.append(Spacer(1, 10))

    if contract.start_date:
        elements.append(Paragraph(f"Дата на сключване: {contract.start_date.strftime('%d.%m.%Y')}", normal_style))
    if contract.end_date:
        elements.append(Paragraph(f"Срок на договора: до {contract.end_date.strftime('%d.%m.%Y')}", normal_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>СТРАНИ ПО ДОГОВОРА:</b>", heading_style))
    elements.append(Paragraph(f"<b>РАБОТОДАТЕЛ:</b> {company.name}", normal_style))
    if company.eik:
        elements.append(Paragraph(f"ЕИК: {company.eik}", normal_style))
    if company.mol_name:
        elements.append(Paragraph(f"МОЛ: {company.mol_name}", normal_style))
    elements.append(Spacer(1, 10))
    
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    elements.append(Paragraph(f"<b>РАБОТНИК:</b> {full_name}", normal_style))
    if user.egn:
        elements.append(Paragraph(f"ЕГН: {user.egn}", normal_style))
    if user.address:
        elements.append(Paragraph(f"Адрес: {user.address}", normal_style))
    if user.iban:
        elements.append(Paragraph(f"IBAN: {user.iban}", normal_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>УСЛОВИЯ НА ДОГОВОРА:</b>", heading_style))
    elements.append(Paragraph(f"Вид договор: {contract_type_label.split(' - ')[-1]}", normal_style))
    elements.append(Paragraph(f"Работни часове: {contract.work_hours_per_week or 40} часа седмично", normal_style))
    elements.append(Paragraph(f"Пробен период: {contract.probation_months or 0} месеца", normal_style))
    
    if contract.base_salary:
        elements.append(Paragraph(f"Основна заплата: {float(contract.base_salary):.2f} лв.", normal_style))
    
    elements.append(Paragraph(f"Начин на изчисляване: {'Брутно' if contract.salary_calculation_type == 'gross' else 'Нетно'}", normal_style))
    elements.append(Paragraph(f"Ден за плащане: {contract.payment_day or 25}-то число на месеца", normal_style))
    
    if contract.night_work_rate:
        elements.append(Paragraph(f"Надбавка нощен труд: {float(contract.night_work_rate) * 100:.0f}%", normal_style))
    if contract.overtime_rate:
        elements.append(Paragraph(f"Множител извънреден труд: {float(contract.overtime_rate):.1f}", normal_style))
    if contract.holiday_rate:
        elements.append(Paragraph(f"Множител празничен труд: {float(contract.holiday_rate):.1f}", normal_style))
    
    if contract.work_class:
        elements.append(Paragraph(f"Трудов клас: {contract.work_class}", normal_style))
    
    elements.append(Spacer(1, 15))

    if sections:
        elements.append(Paragraph("<b>ДОПЪЛНИТЕЛНИ КЛАУЗИ:</b>", heading_style))
        for section in sections:
            if section.title and section.content:
                elements.append(Paragraph(f"<b>{section.title}</b>", heading_style))
                elements.append(Paragraph(section.content, normal_style))
                elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>ПОДПИСИ:</b>", heading_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("_______________________", normal_style))
    elements.append(Paragraph("За Работодателя", normal_style))
    if company.mol_name:
        elements.append(Paragraph(company.mol_name, normal_style))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("_______________________", normal_style))
    elements.append(Paragraph("Работник", normal_style))
    elements.append(Paragraph(full_name, normal_style))

    doc.build(elements)
    buffer.seek(0)

    filename = f"contract_{contract_id}_{datetime.date.today()}.pdf"
    from fastapi.responses import Response
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/annex/{annex_id}/pdf")
async def export_annex_pdf(
    annex_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(jwt_utils.get_current_user)
):
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(ContractAnnex).where(ContractAnnex.id == annex_id))
    annex = result.scalars().first()
    if not annex:
        raise HTTPException(status_code=404, detail="Annex not found")

    contract_result = await db.execute(select(EmploymentContract).where(EmploymentContract.id == annex.contract_id))
    contract = contract_result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    user_result = await db.execute(select(User).where(User.id == contract.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    company_result = await db.execute(select(Company).where(Company.id == contract.company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    sections = []
    if annex.template_id:
        version_result = await db.execute(
            select(AnnexTemplateVersion).where(
                AnnexTemplateVersion.template_id == annex.template_id,
                AnnexTemplateVersion.is_current == True
            )
        )
        version = version_result.scalar_one_or_none()
        if version:
            sections_result = await db.execute(
                select(AnnexTemplateSection).where(
                    AnnexTemplateSection.version_id == version.id
                ).order_by(AnnexTemplateSection.order_index)
            )
            sections = sections_result.scalars().all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()
    
    for style_name in styles.byName:
        style = styles[style_name]
        if hasattr(style, 'fontName'):
            style.fontName = DEFAULT_FONT
        if hasattr(style, 'headingFontName'):
            style.headingFontName = BOLD_FONT

    title_style = styles['Title']
    title_style.fontName = BOLD_FONT
    title_style.fontSize = 16
    
    heading_style = styles['Heading2']
    heading_style.fontName = BOLD_FONT
    heading_style.fontSize = 12

    normal_style = styles['Normal']
    normal_style.fontName = DEFAULT_FONT
    normal_style.fontSize = 10
    normal_style.leading = 14

    elements.append(Paragraph(get_company_header(company), normal_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("ДОПЪЛНИТЕЛНО СПОРАЗУМЕНИЕ", title_style))
    
    annex_number = annex.annex_number or str(annex.id)
    elements.append(Paragraph(f"№ {annex_number}/{annex.effective_date.year}", normal_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"към Трудов договор № {contract.id}/{contract.start_date.year if contract.start_date else ''}", normal_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Днес: {datetime.date.today().strftime('%d.%m.%Y')} г.", normal_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>СТРАНИ:</b>", heading_style))
    elements.append(Paragraph(f"<b>РАБОТОДАТЕЛ:</b> {company.name}", normal_style))
    if company.eik:
        elements.append(Paragraph(f"ЕИК: {company.eik}", normal_style))
    elements.append(Spacer(1, 10))
    
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    elements.append(Paragraph(f"<b>РАБОТНИК:</b> {full_name}", normal_style))
    if user.egn:
        elements.append(Paragraph(f"ЕГН: {user.egn}", normal_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>ПРЕДМЕТ НА СПОРАЗУМЕНИЕТО:</b>", heading_style))
    elements.append(Paragraph("С настоящето споразумение се променят следните условия от трудовия договор:", normal_style))
    elements.append(Spacer(1, 10))

    if annex.change_type:
        change_type_label = {
            "salary": "Основна заплата",
            "position": "Длъжност",
            "hours": "Работно време",
            "rate": "Надбавки",
            "other": "Други условия"
        }.get(annex.change_type, annex.change_type)
        elements.append(Paragraph(f"<b>Вид промяна:</b> {change_type_label}", normal_style))

    if annex.base_salary:
        elements.append(Paragraph(f"Нова основна заплата: {float(annex.base_salary):.2f} лв.", normal_style))
    if annex.work_hours_per_week:
        elements.append(Paragraph(f"Нови работни часове: {annex.work_hours_per_week} часа седмично", normal_style))
    if annex.night_work_rate:
        elements.append(Paragraph(f"Надбавка нощен труд: {float(annex.night_work_rate) * 100:.0f}%", normal_style))
    if annex.overtime_rate:
        elements.append(Paragraph(f"Множител извънреден труд: {float(annex.overtime_rate):.1f}", normal_style))
    if annex.holiday_rate:
        elements.append(Paragraph(f"Множител празничен труд: {float(annex.holiday_rate):.1f}", normal_style))
    
    if annex.change_description:
        elements.append(Paragraph(f"<br/>{annex.change_description}", normal_style))
    
    elements.append(Spacer(1, 15))

    if sections:
        for section in sections:
            if section.title and section.content:
                elements.append(Paragraph(f"<b>{section.title}</b>", heading_style))
                elements.append(Paragraph(section.content, normal_style))
                elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Влиза в сила от:</b> {annex.effective_date.strftime('%d.%m.%Y')} г.", normal_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>ПОДПИСИ:</b>", heading_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("_______________________", normal_style))
    elements.append(Paragraph("За Работодателя", normal_style))
    if company.mol_name:
        elements.append(Paragraph(company.mol_name, normal_style))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("_______________________", normal_style))
    elements.append(Paragraph("Работник", normal_style))
    elements.append(Paragraph(full_name, normal_style))

    if annex.signed_by_employer:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"Подписано от работодател: {annex.signed_by_employer_at.strftime('%d.%m.%Y %H:%M') if annex.signed_by_employer_at else ''}", normal_style))
    if annex.signed_by_employee:
        elements.append(Paragraph(f"Подписано от работник: {annex.signed_by_employee_at.strftime('%d.%m.%Y %H:%M') if annex.signed_by_employee_at else ''}", normal_style))

    doc.build(elements)
    buffer.seek(0)

    filename = f"annex_{annex_id}_{datetime.date.today()}.pdf"
    from fastapi.responses import Response
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
