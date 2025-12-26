"""
Teacher router for the AI Math Tutor system.
Handles class management and question import.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from pydantic import BaseModel

from backend.models import get_db, User, Class, ClassStudent, Subject, Unit, QuestionV2, Difficulty

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# ===== Pydantic Models =====

class CreateClassRequest(BaseModel):
    class_name: str
    description: Optional[str] = None


class QuestionImportItem(BaseModel):
    question_text: str
    answer_text: str
    solution_text: Optional[str] = None
    difficulty: Optional[str] = None


class ImportQuestionsRequest(BaseModel):
    unit_id: int
    difficulty: Optional[str] = "medium"
    questions: List[QuestionImportItem]


# ===== Helper Functions =====

def get_current_user_id(user_id: Optional[str] = Header(None, alias="user-id")) -> Optional[int]:
    """Get current user ID from header."""
    if user_id:
        try:
            return int(user_id)
        except ValueError:
            return None
    return None


# ===== Routes =====

@router.get("/classes")
async def get_teacher_classes(
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get all classes for a teacher."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    # Query classes with student count
    classes = db.query(
        Class,
        func.count(ClassStudent.id).label("student_count")
    ).outerjoin(
        ClassStudent, Class.id == ClassStudent.class_id
    ).filter(
        Class.teacher_id == user_id
    ).group_by(
        Class.id
    ).order_by(
        Class.created_at.desc()
    ).all()
    
    result = []
    for class_, student_count in classes:
        result.append({
            "id": class_.id,
            "class_name": class_.class_name,
            "description": class_.description,
            "created_at": class_.created_at,
            "updated_at": class_.updated_at,
            "studentCount": student_count
        })
    
    return {"classes": result}


@router.post("/classes")
async def create_class(
    request: CreateClassRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Create a new class."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    if not request.class_name:
        raise HTTPException(status_code=400, detail="班級名稱是必填的")
    
    new_class = Class(
        class_name=request.class_name,
        description=request.description,
        teacher_id=user_id
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return {
        "message": "班級建立成功",
        "classId": new_class.id
    }


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: int,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Delete a class."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    # Verify ownership
    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_ or class_.teacher_id != user_id:
        raise HTTPException(status_code=403, detail="無權限刪除此班級")
    
    db.delete(class_)
    db.commit()
    
    return {"message": "班級已刪除"}


@router.get("/classes/{class_id}/students")
async def get_class_students(
    class_id: int,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get all students in a class."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    # Verify ownership
    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_ or class_.teacher_id != user_id:
        raise HTTPException(status_code=403, detail="無權限訪問此班級")
    
    # Get students
    students = db.query(
        User, ClassStudent.joined_at
    ).join(
        ClassStudent, User.id == ClassStudent.student_id
    ).filter(
        ClassStudent.class_id == class_id
    ).order_by(
        ClassStudent.joined_at.desc()
    ).all()
    
    result = []
    for student, joined_at in students:
        result.append({
            "id": student.id,
            "email": student.email,
            "full_name": student.full_name,
            "role": student.role.value,
            "joined_at": joined_at
        })
    
    return {"students": result}


@router.delete("/classes/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: int,
    student_id: int,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Remove a student from a class."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    # Verify ownership
    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_ or class_.teacher_id != user_id:
        raise HTTPException(status_code=403, detail="無權限修改此班級")
    
    # Remove student
    db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id,
        ClassStudent.student_id == student_id
    ).delete()
    
    db.commit()
    
    return {"message": "學生已移除"}


@router.post("/questions/import")
async def import_questions(
    request: ImportQuestionsRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Import questions to a unit."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    if not request.questions:
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    # Verify unit exists
    unit = db.query(Unit).filter(Unit.id == request.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="單元不存在")
    
    imported_count = 0
    
    for q in request.questions:
        if q.question_text and q.answer_text:
            # Determine difficulty
            diff_str = q.difficulty or request.difficulty or "medium"
            try:
                difficulty = Difficulty(diff_str)
            except ValueError:
                difficulty = Difficulty.MEDIUM
            
            new_question = QuestionV2(
                unit_id=request.unit_id,
                question_text=q.question_text,
                answer_text=q.answer_text,
                solution_text=q.solution_text,
                difficulty=difficulty
            )
            
            db.add(new_question)
            imported_count += 1
    
    db.commit()
    
    return {
        "message": f"成功匯入 {imported_count} 條題目",
        "imported_count": imported_count
    }
