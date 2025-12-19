"""
Question Bank Manager for the AI Math Tutor system.
Manages questions, misconceptions, hints, and import/export functionality.
"""
import csv
import io
import json
import uuid
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from backend.models.question import Question, Misconception, Hint, question_knowledge_nodes
from backend.models.knowledge import KnowledgeNode


class QuestionCriteria:
    """Criteria for filtering questions."""
    
    def __init__(
        self,
        subject: Optional[str] = None,
        unit: Optional[str] = None,
        difficulty: Optional[int] = None,
        knowledge_nodes: Optional[List[str]] = None,
        exclude_ids: Optional[List[str]] = None,
        question_type: Optional[str] = None
    ):
        self.subject = subject
        self.unit = unit
        self.difficulty = difficulty
        self.knowledge_nodes = knowledge_nodes
        self.exclude_ids = exclude_ids or []
        self.question_type = question_type


class AnswerValidation:
    """Result of answer validation."""
    
    def __init__(
        self,
        is_correct: bool,
        correct_answer: str,
        student_answer: str,
        feedback: Optional[str] = None
    ):
        self.is_correct = is_correct
        self.correct_answer = correct_answer
        self.student_answer = student_answer
        self.feedback = feedback


class ImportResult:
    """Result of question import operation."""
    
    def __init__(
        self,
        success_count: int = 0,
        error_count: int = 0,
        errors: Optional[List[str]] = None
    ):
        self.success_count = success_count
        self.error_count = error_count
        self.errors = errors or []


class QuestionBankManager:
    """
    Manager class for question bank operations.
    Handles CRUD operations for questions, misconceptions, and hints.
    """

    def __init__(self, db: Session):
        """
        Initialize the Question Bank Manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db


    def filter_questions(self, criteria: QuestionCriteria) -> List[Question]:
        """
        Filter questions based on given criteria.
        
        Args:
            criteria: QuestionCriteria object with filter parameters
            
        Returns:
            List of Question objects matching the criteria
        """
        query = self.db.query(Question)
        
        if criteria.subject:
            query = query.filter(Question.subject == criteria.subject)
        
        if criteria.unit:
            query = query.filter(Question.unit == criteria.unit)
        
        if criteria.difficulty is not None:
            query = query.filter(Question.difficulty == criteria.difficulty)
        
        if criteria.question_type:
            query = query.filter(Question.type == criteria.question_type)
        
        if criteria.exclude_ids:
            query = query.filter(~Question.id.in_(criteria.exclude_ids))
        
        if criteria.knowledge_nodes:
            # Filter by knowledge nodes using the association table
            query = query.join(question_knowledge_nodes).filter(
                question_knowledge_nodes.c.node_id.in_(criteria.knowledge_nodes)
            ).distinct()
        
        return query.all()

    def get_question(self, question_id: str) -> Optional[Question]:
        """
        Get a question by ID.
        
        Args:
            question_id: The unique identifier of the question
            
        Returns:
            Question if found, None otherwise
        """
        return self.db.query(Question).filter(
            Question.id == question_id
        ).first()

    def get_similar_questions(
        self,
        question_id: str,
        count: int = 3
    ) -> List[Question]:
        """
        Get similar questions based on knowledge nodes and difficulty.
        
        Args:
            question_id: The ID of the reference question
            count: Maximum number of similar questions to return
            
        Returns:
            List of similar Question objects
        """
        question = self.get_question(question_id)
        if not question:
            return []
        
        # Get knowledge node IDs for the question
        node_ids = [node.id for node in question.knowledge_nodes]
        
        if not node_ids:
            # Fallback: find questions with same subject and unit
            return self.db.query(Question).filter(
                Question.id != question_id,
                Question.subject == question.subject,
                Question.unit == question.unit
            ).limit(count).all()
        
        # Find questions with overlapping knowledge nodes
        similar = self.db.query(Question).join(question_knowledge_nodes).filter(
            Question.id != question_id,
            question_knowledge_nodes.c.node_id.in_(node_ids)
        ).distinct().limit(count).all()
        
        return similar


    def add_question(self, question: Question) -> Question:
        """
        Add a new question to the bank.
        
        Args:
            question: The Question to add
            
        Returns:
            The added Question with generated ID if not provided
        """
        if not question.id:
            question.id = str(uuid.uuid4())
        
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def validate_answer(
        self,
        question_id: str,
        answer: str
    ) -> Optional[AnswerValidation]:
        """
        Validate a student's answer against the correct answer.
        
        Args:
            question_id: The ID of the question
            answer: The student's answer
            
        Returns:
            AnswerValidation result, or None if question not found
        """
        question = self.get_question(question_id)
        if not question:
            return None
        
        # Simple string comparison (can be enhanced for more complex validation)
        is_correct = self._normalize_answer(answer) == self._normalize_answer(
            question.standard_solution
        )
        
        feedback = None
        if not is_correct:
            # Check for common misconceptions
            for misconception in question.misconceptions:
                if self._matches_misconception(answer, misconception):
                    feedback = misconception.correction
                    break
        
        return AnswerValidation(
            is_correct=is_correct,
            correct_answer=question.standard_solution,
            student_answer=answer,
            feedback=feedback
        )

    def _normalize_answer(self, answer: str) -> str:
        """Normalize an answer for comparison."""
        return answer.strip().lower().replace(" ", "")

    def _matches_misconception(
        self,
        answer: str,
        misconception: Misconception
    ) -> bool:
        """Check if an answer matches a known misconception pattern."""
        # Simple check - can be enhanced with more sophisticated matching
        return misconception.description.lower() in answer.lower()

    def import_questions(
        self,
        data: Union[str, List[Dict[str, Any]]],
        format: str = 'JSON'
    ) -> ImportResult:
        """
        Import questions from JSON or CSV format.
        
        Args:
            data: JSON string, list of dicts, or CSV string
            format: 'JSON' or 'CSV'
            
        Returns:
            ImportResult with success/error counts
        """
        result = ImportResult()
        
        try:
            if format.upper() == 'JSON':
                questions_data = self._parse_json(data)
            elif format.upper() == 'CSV':
                questions_data = self._parse_csv(data)
            else:
                result.errors.append(f"Unsupported format: {format}")
                return result
            
            for q_data in questions_data:
                try:
                    question = self._create_question_from_dict(q_data)
                    self.add_question(question)
                    result.success_count += 1
                except Exception as e:
                    result.error_count += 1
                    result.errors.append(f"Error importing question: {str(e)}")
            
        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
        
        return result


    def export_questions(
        self,
        questions: Optional[List[Question]] = None,
        format: str = 'JSON'
    ) -> str:
        """
        Export questions to JSON or CSV format.
        
        Args:
            questions: List of questions to export (None = all questions)
            format: 'JSON' or 'CSV'
            
        Returns:
            Exported data as string
        """
        if questions is None:
            questions = self.db.query(Question).all()
        
        questions_data = [self._question_to_dict(q) for q in questions]
        
        if format.upper() == 'JSON':
            return json.dumps(questions_data, ensure_ascii=False, indent=2)
        elif format.upper() == 'CSV':
            return self._to_csv(questions_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _parse_json(
        self,
        data: Union[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Parse JSON data into list of dicts."""
        if isinstance(data, str):
            return json.loads(data)
        return data

    def _parse_csv(self, data: str) -> List[Dict[str, Any]]:
        """Parse CSV data into list of dicts."""
        reader = csv.DictReader(io.StringIO(data))
        questions = []
        for row in reader:
            # Convert difficulty to int
            if 'difficulty' in row:
                row['difficulty'] = int(row['difficulty'])
            # Parse knowledge_nodes as JSON array if present
            if 'knowledge_nodes' in row and row['knowledge_nodes']:
                try:
                    row['knowledge_nodes'] = json.loads(row['knowledge_nodes'])
                except json.JSONDecodeError:
                    row['knowledge_nodes'] = []
            questions.append(row)
        return questions

    def _to_csv(self, questions_data: List[Dict[str, Any]]) -> str:
        """Convert questions data to CSV string."""
        if not questions_data:
            return ""
        
        output = io.StringIO()
        fieldnames = ['id', 'content', 'type', 'subject', 'unit', 
                      'difficulty', 'standard_solution', 'knowledge_nodes']
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for q in questions_data:
            row = q.copy()
            # Convert knowledge_nodes list to JSON string
            if 'knowledge_nodes' in row and isinstance(row['knowledge_nodes'], list):
                row['knowledge_nodes'] = json.dumps(row['knowledge_nodes'])
            writer.writerow(row)
        
        return output.getvalue()

    def _create_question_from_dict(self, data: Dict[str, Any]) -> Question:
        """Create a Question object from a dictionary."""
        question = Question(
            id=data.get('id') or str(uuid.uuid4()),
            content=data['content'],
            type=data['type'],
            subject=data['subject'],
            unit=data['unit'],
            difficulty=data['difficulty'],
            standard_solution=data['standard_solution']
        )
        
        # Handle knowledge nodes if provided
        if 'knowledge_nodes' in data and data['knowledge_nodes']:
            node_ids = data['knowledge_nodes']
            if isinstance(node_ids, list):
                nodes = self.db.query(KnowledgeNode).filter(
                    KnowledgeNode.id.in_(node_ids)
                ).all()
                question.knowledge_nodes = nodes
        
        return question

    def _question_to_dict(self, question: Question) -> Dict[str, Any]:
        """Convert a Question object to a dictionary."""
        return {
            'id': question.id,
            'content': question.content,
            'type': question.type,
            'subject': question.subject,
            'unit': question.unit,
            'difficulty': question.difficulty,
            'standard_solution': question.standard_solution,
            'knowledge_nodes': [node.id for node in question.knowledge_nodes]
        }

    def add_misconception(
        self,
        question_id: str,
        misconception: Misconception
    ) -> Optional[Misconception]:
        """
        Add a misconception to a question.
        
        Args:
            question_id: The ID of the question
            misconception: The Misconception to add
            
        Returns:
            The added Misconception, or None if question not found
        """
        question = self.get_question(question_id)
        if not question:
            return None
        
        if not misconception.id:
            misconception.id = str(uuid.uuid4())
        
        misconception.question_id = question_id
        self.db.add(misconception)
        self.db.commit()
        self.db.refresh(misconception)
        return misconception

    def add_hint(
        self,
        question_id: str,
        hint: Hint
    ) -> Optional[Hint]:
        """
        Add a hint to a question.
        
        Args:
            question_id: The ID of the question
            hint: The Hint to add
            
        Returns:
            The added Hint, or None if question not found
        """
        question = self.get_question(question_id)
        if not question:
            return None
        
        if not hint.id:
            hint.id = str(uuid.uuid4())
        
        hint.question_id = question_id
        self.db.add(hint)
        self.db.commit()
        self.db.refresh(hint)
        return hint

    def link_question_to_knowledge_node(
        self,
        question_id: str,
        node_id: str
    ) -> bool:
        """
        Link a question to a knowledge node.
        
        Args:
            question_id: The ID of the question
            node_id: The ID of the knowledge node
            
        Returns:
            True if linked successfully, False otherwise
        """
        question = self.get_question(question_id)
        node = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.id == node_id
        ).first()
        
        if not question or not node:
            return False
        
        if node not in question.knowledge_nodes:
            question.knowledge_nodes.append(node)
            self.db.commit()
        
        return True
