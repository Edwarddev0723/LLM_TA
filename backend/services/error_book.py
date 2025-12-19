"""
Error Book Manager for the AI Math Tutor system.
Manages error records, auto-tagging, and repair tracking.
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.models.error_book import ErrorRecord
from backend.models.question import Question


class ErrorCriteria:
    """Criteria for filtering error records."""
    
    def __init__(
        self,
        error_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        unit: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        repaired_status: Optional[bool] = None
    ):
        self.error_type = error_type
        self.tags = tags
        self.unit = unit
        self.date_from = date_from
        self.date_to = date_to
        self.repaired_status = repaired_status


class ErrorStatistics:
    """Statistics about error records."""
    
    def __init__(
        self,
        total_errors: int = 0,
        repaired_count: int = 0,
        errors_by_type: Optional[Dict[str, int]] = None,
        errors_by_unit: Optional[Dict[str, int]] = None,
        most_frequent_misconceptions: Optional[List[str]] = None
    ):
        self.total_errors = total_errors
        self.repaired_count = repaired_count
        self.errors_by_type = errors_by_type or {}
        self.errors_by_unit = errors_by_unit or {}
        self.most_frequent_misconceptions = most_frequent_misconceptions or []


class ErrorBookManager:
    """
    Manager class for error book operations.
    Handles CRUD operations for error records with auto-tagging.
    """

    # Error type keywords for auto-detection
    CALCULATION_KEYWORDS = [
        '計算', '運算', '加', '減', '乘', '除', '數字', '答案',
        'calculation', 'compute', 'arithmetic'
    ]
    
    CONCEPT_KEYWORDS = [
        '概念', '定義', '公式', '原理', '定理', '理解',
        'concept', 'definition', 'formula', 'theorem'
    ]
    
    CARELESS_KEYWORDS = [
        '粗心', '抄錯', '看錯', '漏', '忘記', '符號',
        'careless', 'typo', 'missed', 'forgot'
    ]

    def __init__(self, db: Session):
        """
        Initialize the Error Book Manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def add_error(
        self,
        student_id: str,
        question_id: str,
        student_answer: str,
        correct_answer: str,
        error_type: Optional[str] = None,
        error_tags: Optional[List[str]] = None
    ) -> ErrorRecord:
        """
        Add a new error record with auto-tagging.
        
        Args:
            student_id: The student's ID
            question_id: The question's ID
            student_answer: The student's incorrect answer
            correct_answer: The correct answer
            error_type: Optional error type (auto-detected if not provided)
            error_tags: Optional tags (auto-generated if not provided)
            
        Returns:
            The created ErrorRecord
        """
        # Auto-detect error type if not provided
        if error_type is None:
            error_type = self._detect_error_type(
                student_answer, correct_answer, question_id
            )
        
        # Auto-generate tags if not provided
        if error_tags is None:
            error_tags = self._generate_error_tags(
                student_answer, correct_answer, error_type, question_id
            )
        
        error_record = ErrorRecord(
            id=str(uuid.uuid4()),
            student_id=student_id,
            question_id=question_id,
            student_answer=student_answer,
            correct_answer=correct_answer,
            error_type=error_type,
            error_tags=json.dumps(error_tags, ensure_ascii=False),
            timestamp=datetime.utcnow(),
            repaired=False
        )
        
        self.db.add(error_record)
        self.db.commit()
        self.db.refresh(error_record)
        return error_record

    def get_errors(
        self,
        student_id: str,
        criteria: Optional[ErrorCriteria] = None
    ) -> List[ErrorRecord]:
        """
        Get error records for a student with optional filtering.
        
        Args:
            student_id: The student's ID
            criteria: Optional filtering criteria
            
        Returns:
            List of ErrorRecord objects matching the criteria
        """
        query = self.db.query(ErrorRecord).filter(
            ErrorRecord.student_id == student_id
        )
        
        if criteria:
            if criteria.error_type:
                query = query.filter(ErrorRecord.error_type == criteria.error_type)
            
            if criteria.repaired_status is not None:
                query = query.filter(ErrorRecord.repaired == criteria.repaired_status)
            
            if criteria.date_from:
                query = query.filter(ErrorRecord.timestamp >= criteria.date_from)
            
            if criteria.date_to:
                query = query.filter(ErrorRecord.timestamp <= criteria.date_to)
            
            if criteria.unit:
                # Join with Question to filter by unit
                query = query.join(Question).filter(Question.unit == criteria.unit)
            
            if criteria.tags:
                # Filter by tags (check if any tag is in the error_tags JSON)
                for tag in criteria.tags:
                    query = query.filter(ErrorRecord.error_tags.contains(tag))
        
        return query.order_by(ErrorRecord.timestamp.desc()).all()

    def get_error_by_id(self, error_id: str) -> Optional[ErrorRecord]:
        """
        Get an error record by ID.
        
        Args:
            error_id: The error record's ID
            
        Returns:
            ErrorRecord if found, None otherwise
        """
        return self.db.query(ErrorRecord).filter(
            ErrorRecord.id == error_id
        ).first()

    def mark_as_repaired(self, error_id: str) -> Optional[ErrorRecord]:
        """
        Mark an error record as repaired.
        
        Args:
            error_id: The error record's ID
            
        Returns:
            Updated ErrorRecord if found, None otherwise
        """
        error_record = self.get_error_by_id(error_id)
        if error_record is None:
            return None
        
        error_record.repaired = True
        error_record.repaired_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(error_record)
        return error_record

    def get_error_statistics(self, student_id: str) -> ErrorStatistics:
        """
        Get error statistics for a student.
        
        Args:
            student_id: The student's ID
            
        Returns:
            ErrorStatistics object with aggregated data
        """
        errors = self.db.query(ErrorRecord).filter(
            ErrorRecord.student_id == student_id
        ).all()
        
        total_errors = len(errors)
        repaired_count = sum(1 for e in errors if e.repaired)
        
        # Count by error type
        errors_by_type: Dict[str, int] = {}
        for error in errors:
            errors_by_type[error.error_type] = errors_by_type.get(
                error.error_type, 0
            ) + 1
        
        # Count by unit (requires joining with Question)
        errors_by_unit: Dict[str, int] = {}
        for error in errors:
            question = self.db.query(Question).filter(
                Question.id == error.question_id
            ).first()
            if question:
                errors_by_unit[question.unit] = errors_by_unit.get(
                    question.unit, 0
                ) + 1
        
        # Find most frequent tags/misconceptions
        tag_counts: Dict[str, int] = {}
        for error in errors:
            if error.error_tags:
                try:
                    tags = json.loads(error.error_tags)
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except json.JSONDecodeError:
                    pass
        
        # Sort tags by frequency and get top 5
        sorted_tags = sorted(
            tag_counts.items(), key=lambda x: x[1], reverse=True
        )
        most_frequent = [tag for tag, _ in sorted_tags[:5]]
        
        return ErrorStatistics(
            total_errors=total_errors,
            repaired_count=repaired_count,
            errors_by_type=errors_by_type,
            errors_by_unit=errors_by_unit,
            most_frequent_misconceptions=most_frequent
        )

    def _detect_error_type(
        self,
        student_answer: str,
        correct_answer: str,
        question_id: str
    ) -> str:
        """
        Auto-detect the error type based on the answers and question.
        
        Args:
            student_answer: The student's incorrect answer
            correct_answer: The correct answer
            question_id: The question's ID
            
        Returns:
            Error type string: 'CALCULATION', 'CONCEPT', or 'CARELESS'
        """
        # Get the question for context
        question = self.db.query(Question).filter(
            Question.id == question_id
        ).first()
        
        # Check for careless errors (small differences)
        if self._is_careless_error(student_answer, correct_answer):
            return 'CARELESS'
        
        # Check question type for hints
        if question:
            if question.type in ['CALCULATION', 'FILL_BLANK']:
                # Likely a calculation error for numeric questions
                if self._has_numeric_difference(student_answer, correct_answer):
                    return 'CALCULATION'
            elif question.type in ['PROOF', 'MULTIPLE_CHOICE']:
                # Likely a concept error for proof/theory questions
                return 'CONCEPT'
        
        # Default to calculation error
        return 'CALCULATION'

    def _is_careless_error(
        self,
        student_answer: str,
        correct_answer: str
    ) -> bool:
        """
        Check if the error appears to be a careless mistake.
        
        Args:
            student_answer: The student's answer
            correct_answer: The correct answer
            
        Returns:
            True if likely a careless error
        """
        # Normalize answers
        s_norm = student_answer.strip().lower()
        c_norm = correct_answer.strip().lower()
        
        # Check for single character difference
        if len(s_norm) == len(c_norm):
            diff_count = sum(1 for a, b in zip(s_norm, c_norm) if a != b)
            if diff_count == 1:
                return True
        
        # Check for sign error (e.g., -5 vs 5)
        if s_norm.replace('-', '') == c_norm.replace('-', ''):
            return True
        
        # Check for transposition (e.g., 12 vs 21)
        if len(s_norm) == len(c_norm) == 2:
            if s_norm[0] == c_norm[1] and s_norm[1] == c_norm[0]:
                return True
        
        return False

    def _has_numeric_difference(
        self,
        student_answer: str,
        correct_answer: str
    ) -> bool:
        """
        Check if there's a numeric difference between answers.
        
        Args:
            student_answer: The student's answer
            correct_answer: The correct answer
            
        Returns:
            True if both answers are numeric and different
        """
        try:
            # Try to extract numbers from answers
            s_num = float(''.join(
                c for c in student_answer if c.isdigit() or c in '.-'
            ) or '0')
            c_num = float(''.join(
                c for c in correct_answer if c.isdigit() or c in '.-'
            ) or '0')
            return s_num != c_num
        except ValueError:
            return False

    def _generate_error_tags(
        self,
        student_answer: str,
        correct_answer: str,
        error_type: str,
        question_id: str
    ) -> List[str]:
        """
        Auto-generate error tags based on the error analysis.
        
        Args:
            student_answer: The student's incorrect answer
            correct_answer: The correct answer
            error_type: The detected error type
            question_id: The question's ID
            
        Returns:
            List of error tags
        """
        tags = []
        
        # Add error type as a tag
        type_tag_map = {
            'CALCULATION': '計算錯誤',
            'CONCEPT': '觀念錯誤',
            'CARELESS': '粗心錯誤'
        }
        tags.append(type_tag_map.get(error_type, error_type))
        
        # Get question for additional context
        question = self.db.query(Question).filter(
            Question.id == question_id
        ).first()
        
        if question:
            # Add unit as a tag
            tags.append(question.unit)
            
            # Check for specific error patterns
            if self._is_sign_error(student_answer, correct_answer):
                tags.append('符號錯誤')
            
            if self._is_order_error(student_answer, correct_answer):
                tags.append('順序錯誤')
            
            # Check misconceptions from the question
            for misconception in question.misconceptions:
                if self._matches_misconception_pattern(
                    student_answer, misconception.description
                ):
                    tags.append(misconception.description)
        
        return list(set(tags))  # Remove duplicates

    def _is_sign_error(
        self,
        student_answer: str,
        correct_answer: str
    ) -> bool:
        """Check if the error is a sign error."""
        s_clean = student_answer.replace(' ', '')
        c_clean = correct_answer.replace(' ', '')
        
        # Check if one has negative and other doesn't
        if s_clean.startswith('-') != c_clean.startswith('-'):
            if s_clean.lstrip('-') == c_clean.lstrip('-'):
                return True
        
        return False

    def _is_order_error(
        self,
        student_answer: str,
        correct_answer: str
    ) -> bool:
        """Check if the error is an order/transposition error."""
        s_clean = ''.join(sorted(student_answer.replace(' ', '')))
        c_clean = ''.join(sorted(correct_answer.replace(' ', '')))
        return s_clean == c_clean and student_answer != correct_answer

    def _matches_misconception_pattern(
        self,
        student_answer: str,
        misconception_desc: str
    ) -> bool:
        """Check if the student's answer matches a misconception pattern."""
        # Simple keyword matching
        keywords = misconception_desc.lower().split()
        answer_lower = student_answer.lower()
        return any(kw in answer_lower for kw in keywords if len(kw) > 2)
