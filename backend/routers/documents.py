from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import get_db
from backend import crud, schemas
from backend.auth import jwt_utils
from backend.database.models import User, UserDocument
from sqlalchemy import select
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
import uuid
import shutil
from datetime import datetime

from backend.auth.module_guard import require_module_dep

router = APIRouter(
    prefix="/documents", 
    tags=["documents"],
    dependencies=[Depends(require_module_dep("integrations"))]
)

# Setup fonts (re-using from export.py logic)
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    DEFAULT_FONT = 'DejaVuSans'
    BOLD_FONT = 'DejaVuSans-Bold'
except:
    DEFAULT_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'

@router.get("/generate/leave/{request_id}")
async def generate_leave_application(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(jwt_utils.get_current_user)
):
    from backend.database.models import LeaveRequest
    req = await db.get(LeaveRequest, request_id)
    if not req: raise HTTPException(status_code=404)
    
    user = await db.get(User, req.user_id)
    if current_user.role.name not in ["admin", "super_admin"] and current_user.id != user.id:
        raise HTTPException(status_code=403)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Application Template
    p.setFont(BOLD_FONT, 16)
    p.drawCentredString(width/2, height - 100, "МОЛБА ЗА ПОЛЗВАНЕ НА ОТПУСК")
    
    p.setFont(DEFAULT_FONT, 12)
    p.drawString(100, height - 150, f"До: Управителя на {user.company or 'Фирмата'}")
    p.drawString(100, height - 170, f"От: {user.first_name} {user.last_name}")
    p.drawString(100, height - 190, f"Длъжност: {user.job_title or 'Служител'}")
    
    text = f"Моля да ми бъде разрешено ползването на {req.leave_type} отпуск"
    p.drawString(100, height - 240, text)
    p.drawString(100, height - 260, f"за периода от {req.start_date} до {req.end_date} включително.")
    
    if req.reason:
        p.drawString(100, height - 290, f"Причина: {req.reason}")

    p.drawString(100, height - 350, f"Дата: {datetime.now().date()}")
    p.drawString(400, height - 350, "Подпис: .....................")
    
    p.setFont(BOLD_FONT, 10)
    p.drawString(100, height - 400, "РЕЗОЛЮЦИЯ НА РЪКОВОДИТЕЛЯ:")
    p.drawString(100, height - 420, "[ ] РАЗРЕШАВАМ   [ ] НЕ РАЗРЕШАВАМ")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=molba_otpusk_{request_id}.pdf"}
    )

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload/{user_id}")
async def upload_document(
    user_id: int,
    file_type: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(jwt_utils.get_current_user)
):
    # Only admin or self can upload
    if current_user.role.name not in ["admin", "super_admin"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = UserDocument(
        user_id=user_id,
        filename=file.filename,
        file_path=unique_filename, # Store only name
        file_type=file_type,
        uploaded_by=current_user.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename}

@router.get("/list/{user_id}")
async def list_documents(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(jwt_utils.get_current_user)
):
    if current_user.role.name not in ["admin", "super_admin"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    stmt = select(UserDocument).where(UserDocument.user_id == user_id).order_by(UserDocument.created_at.desc())
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return [{"id": d.id, "filename": d.filename, "file_type": d.file_type, "is_locked": d.is_locked, "created_at": d.created_at} for d in docs]

@router.post("/{doc_id}/toggle-lock")
async def toggle_document_lock(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(jwt_utils.get_current_user)
):
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can lock documents")

    doc = await db.get(UserDocument, doc_id)
    if not doc: raise HTTPException(status_code=404)
    
    doc.is_locked = not doc.is_locked
    await db.commit()
    return {"id": doc.id, "is_locked": doc.is_locked}

@router.get("/download/{doc_id}")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(jwt_utils.get_current_user)
):
    doc = await db.get(UserDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Admin/SuperAdmin check
    is_admin = current_user.role.name in ["admin", "super_admin"]

    # 2. Authorization & Lock Logic
    if not is_admin:
        # User can only see their own documents
        if current_user.id != doc.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # LOCKED check for regular users
        if doc.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Този документ е заключен от администратор и не може да бъде свалян."
            )

    # 3. Serve File
    file_path = os.path.join(UPLOAD_DIR, doc.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    return FileResponse(path=file_path, filename=doc.filename)

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(jwt_utils.get_current_user)
):
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can delete documents")

    doc = await db.get(UserDocument, doc_id)
    if doc:
        file_path = os.path.join(UPLOAD_DIR, doc.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        await db.delete(doc)
        await db.commit()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Not found")
