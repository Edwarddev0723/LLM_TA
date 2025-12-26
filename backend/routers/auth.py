"""
Authentication router for the AI Math Tutor system.
Handles user registration, login, and profile management.
"""
import os
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel, EmailStr

from backend.models import get_db, User, UserRole, VerificationStatus

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Upload directory for ID documents
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ===== Pydantic Models =====

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str
    full_name: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    phone: Optional[str] = None
    student_name: Optional[str] = None
    relationship: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    verification_status: str
    created_at: datetime
    grade: Optional[str] = None
    class_name: Optional[str] = None
    phone: Optional[str] = None
    student_name: Optional[str] = None
    relationship: Optional[str] = None

    class Config:
        from_attributes = True


# ===== Helper Functions =====

def hash_password(password: str) -> str:
    """Simple password hashing using SHA256 with salt."""
    # In production, use bcrypt or argon2
    salt = "ai_math_tutor_salt"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def get_current_user_id(user_id: Optional[str] = Header(None, alias="user-id")) -> Optional[int]:
    """Get current user ID from header."""
    if user_id:
        try:
            return int(user_id)
        except ValueError:
            return None
    return None


# ===== Routes =====

@router.post("/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    full_name: str = Form(..., alias="fullName"),
    id_document: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db)
):
    """Register a new user."""
    # Validate role
    allowed_roles = ["student", "teacher", "parent"]
    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="無效的角色選擇")
    
    # Check if teacher needs ID document
    if role == "teacher" and not id_document:
        raise HTTPException(status_code=400, detail="老師必須上傳教師證明文件")
    
    # Check if email exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="郵箱已存在")
    
    # Handle file upload for teachers
    id_document_path = None
    if role == "teacher" and id_document:
        # Save file
        file_ext = os.path.splitext(id_document.filename)[1]
        file_name = f"idDocument-{datetime.now().timestamp()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as f:
            content = await id_document.read()
            f.write(content)
        
        id_document_path = f"uploads/{file_name}"
    
    # Create user
    user_role = UserRole(role)
    verification = VerificationStatus.PENDING if role == "teacher" else VerificationStatus.APPROVED
    
    new_user = User(
        email=email,
        password_hash=hash_password(password),
        role=user_role,
        full_name=full_name,
        id_document_path=id_document_path,
        verification_status=verification
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    message = (
        "註冊成功！請等待管理員審核您的教師證明文件。" 
        if role == "teacher" 
        else "註冊成功！您可以立即登入使用系統。"
    )
    
    return {
        "message": message,
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.value,
            "verification_status": new_user.verification_status.value
        }
    }


@router.post("/login")
async def login(request: UserLoginRequest, db: DBSession = Depends(get_db)):
    """Login user."""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="電子郵件或密碼錯誤")
    
    # Check verification status
    if user.verification_status != VerificationStatus.APPROVED:
        raise HTTPException(status_code=403, detail="帳戶尚未通過驗證，請等待管理員審核")
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="電子郵件或密碼錯誤")
    
    return {
        "message": "登入成功",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }


@router.get("/me")
async def get_current_user(
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get current user information."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role.value,
            "verification_status": user.verification_status.value,
            "created_at": user.created_at,
            "grade": user.grade,
            "class": user.class_name,
            "phone": user.phone,
            "studentName": user.student_name,
            "relationship": user.relationship_type
        }
    }


@router.put("/me")
async def update_current_user(
    request: UserUpdateRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Update current user information."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # Update fields
    if request.name is not None:
        user.full_name = request.name
    if request.grade is not None:
        user.grade = request.grade
    if request.class_name is not None:
        user.class_name = request.class_name
    if request.phone is not None:
        user.phone = request.phone
    if request.student_name is not None:
        user.student_name = request.student_name
    if request.relationship is not None:
        user.relationship_type = request.relationship
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "用戶資訊已更新",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role.value,
            "verification_status": user.verification_status.value,
            "created_at": user.created_at,
            "grade": user.grade,
            "class": user.class_name,
            "phone": user.phone,
            "studentName": user.student_name,
            "relationship": user.relationship_type
        }
    }
