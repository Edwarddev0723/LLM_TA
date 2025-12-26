"""
Practice Mode API routes for the AI Math Tutor system.
Provides question bank, practice sessions, and AI evaluation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import random
import json

from backend.models.database import get_db
from backend.services.llm_client import OllamaClient, LLMConfig

router = APIRouter(prefix="/api/practice", tags=["practice"])

# Initialize LLM client
llm_config = LLMConfig(
    model="gpt-oss:20b",
    timeout_seconds=120.0,
    enable_fallback=True
)
llm_client = OllamaClient(llm_config)


# ============ Question Bank Data ============

MATH_QUESTION_BANK = {
    "arithmetic": {
        "name": "算術",
        "questions": {
            1: [  # Easy
                {"q": "計算：15 + 27 = ?", "options": ["42", "41", "43", "40"], "answer": "A", "explanation": "15 + 27 = 42"},
                {"q": "計算：48 - 19 = ?", "options": ["29", "28", "30", "27"], "answer": "A", "explanation": "48 - 19 = 29"},
                {"q": "計算：6 × 7 = ?", "options": ["42", "48", "36", "49"], "answer": "A", "explanation": "6 × 7 = 42"},
                {"q": "計算：56 ÷ 8 = ?", "options": ["7", "8", "6", "9"], "answer": "A", "explanation": "56 ÷ 8 = 7"},
                {"q": "計算：(-3) + 8 = ?", "options": ["5", "-5", "11", "-11"], "answer": "A", "explanation": "(-3) + 8 = 5"},
            ],
            2: [
                {"q": "計算：(-12) × (-4) = ?", "options": ["48", "-48", "16", "-16"], "answer": "A", "explanation": "負負得正，(-12) × (-4) = 48"},
                {"q": "計算：24 ÷ (-6) = ?", "options": ["-4", "4", "-18", "18"], "answer": "A", "explanation": "正除以負得負，24 ÷ (-6) = -4"},
                {"q": "計算：|-15| + |7| = ?", "options": ["22", "8", "-22", "-8"], "answer": "A", "explanation": "|-15| = 15, |7| = 7, 15 + 7 = 22"},
            ],
            3: [
                {"q": "計算：2³ × 3² = ?", "options": ["72", "36", "54", "48"], "answer": "A", "explanation": "2³ = 8, 3² = 9, 8 × 9 = 72"},
                {"q": "計算：√144 + √81 = ?", "options": ["21", "15", "18", "24"], "answer": "A", "explanation": "√144 = 12, √81 = 9, 12 + 9 = 21"},
                {"q": "計算：5! ÷ 3! = ?", "options": ["20", "60", "10", "30"], "answer": "A", "explanation": "5! = 120, 3! = 6, 120 ÷ 6 = 20"},
            ],
            4: [
                {"q": "計算：log₁₀(1000) = ?", "options": ["3", "2", "4", "10"], "answer": "A", "explanation": "10³ = 1000，所以 log₁₀(1000) = 3"},
                {"q": "計算：2⁻³ = ?", "options": ["1/8", "8", "-8", "-1/8"], "answer": "A", "explanation": "2⁻³ = 1/2³ = 1/8"},
            ],
            5: [
                {"q": "計算：∛(-27) + ⁴√16 = ?", "options": ["-1", "1", "-5", "5"], "answer": "A", "explanation": "∛(-27) = -3, ⁴√16 = 2, -3 + 2 = -1"},
            ]
        }
    },
    "algebra": {
        "name": "代數",
        "questions": {
            1: [
                {"q": "解方程式：x + 5 = 12，x = ?", "options": ["7", "17", "5", "-7"], "answer": "A", "explanation": "x = 12 - 5 = 7"},
                {"q": "解方程式：2x = 14，x = ?", "options": ["7", "28", "12", "16"], "answer": "A", "explanation": "x = 14 ÷ 2 = 7"},
                {"q": "解方程式：x - 8 = 3，x = ?", "options": ["11", "5", "-5", "-11"], "answer": "A", "explanation": "x = 3 + 8 = 11"},
            ],
            2: [
                {"q": "解方程式：3x + 7 = 22，x = ?", "options": ["5", "15", "7", "3"], "answer": "A", "explanation": "3x = 22 - 7 = 15, x = 5"},
                {"q": "解方程式：2x - 5 = x + 3，x = ?", "options": ["8", "2", "-2", "-8"], "answer": "A", "explanation": "2x - x = 3 + 5, x = 8"},
                {"q": "化簡：3(x + 2) - 2x = ?", "options": ["x + 6", "5x + 6", "x + 2", "5x + 2"], "answer": "A", "explanation": "3x + 6 - 2x = x + 6"},
            ],
            3: [
                {"q": "解方程式：x² = 49，x = ?", "options": ["±7", "7", "-7", "49"], "answer": "A", "explanation": "x = ±√49 = ±7"},
                {"q": "因式分解：x² - 9 = ?", "options": ["(x+3)(x-3)", "(x+9)(x-1)", "(x-3)²", "(x+3)²"], "answer": "A", "explanation": "差平方公式：x² - 9 = (x+3)(x-3)"},
                {"q": "解方程式：x² - 5x + 6 = 0，x = ?", "options": ["2 或 3", "1 或 6", "-2 或 -3", "2 或 -3"], "answer": "A", "explanation": "(x-2)(x-3) = 0, x = 2 或 3"},
            ],
            4: [
                {"q": "解方程式：x² + 4x - 5 = 0，x = ?", "options": ["1 或 -5", "-1 或 5", "1 或 5", "-1 或 -5"], "answer": "A", "explanation": "(x+5)(x-1) = 0, x = 1 或 -5"},
                {"q": "若 f(x) = 2x² - 3x + 1，則 f(2) = ?", "options": ["3", "5", "7", "1"], "answer": "A", "explanation": "f(2) = 2(4) - 3(2) + 1 = 8 - 6 + 1 = 3"},
            ],
            5: [
                {"q": "解聯立方程式：2x + y = 7, x - y = 2，則 x = ?", "options": ["3", "4", "2", "1"], "answer": "A", "explanation": "相加得 3x = 9, x = 3"},
                {"q": "若 x² - 6x + k = 0 有重根，則 k = ?", "options": ["9", "6", "3", "12"], "answer": "A", "explanation": "判別式 = 0, 36 - 4k = 0, k = 9"},
            ]
        }
    },

    "geometry": {
        "name": "幾何",
        "questions": {
            1: [
                {"q": "三角形內角和為多少度？", "options": ["180°", "360°", "90°", "270°"], "answer": "A", "explanation": "三角形內角和恆為 180°"},
                {"q": "正方形有幾條對角線？", "options": ["2", "4", "1", "3"], "answer": "A", "explanation": "正方形有 2 條對角線"},
                {"q": "圓的直徑是半徑的幾倍？", "options": ["2", "3", "4", "1"], "answer": "A", "explanation": "直徑 = 2 × 半徑"},
            ],
            2: [
                {"q": "計算三角形面積：底 = 8cm，高 = 6cm", "options": ["24 cm²", "48 cm²", "14 cm²", "28 cm²"], "answer": "A", "explanation": "面積 = (1/2) × 8 × 6 = 24 cm²"},
                {"q": "計算長方形周長：長 = 10cm，寬 = 5cm", "options": ["30 cm", "50 cm", "15 cm", "25 cm"], "answer": "A", "explanation": "周長 = 2 × (10 + 5) = 30 cm"},
                {"q": "正六邊形的內角和為多少度？", "options": ["720°", "540°", "360°", "900°"], "answer": "A", "explanation": "內角和 = (6-2) × 180° = 720°"},
            ],
            3: [
                {"q": "計算圓面積：半徑 = 7cm（π ≈ 3.14）", "options": ["153.86 cm²", "43.96 cm²", "21.98 cm²", "307.72 cm²"], "answer": "A", "explanation": "面積 = π × 7² ≈ 3.14 × 49 ≈ 153.86 cm²"},
                {"q": "直角三角形兩股為 3 和 4，斜邊為？", "options": ["5", "7", "6", "8"], "answer": "A", "explanation": "畢氏定理：√(3² + 4²) = √25 = 5"},
                {"q": "等腰三角形底角為 50°，頂角為？", "options": ["80°", "50°", "100°", "60°"], "answer": "A", "explanation": "頂角 = 180° - 50° - 50° = 80°"},
            ],
            4: [
                {"q": "計算圓柱體積：半徑 = 3cm，高 = 10cm（π ≈ 3.14）", "options": ["282.6 cm³", "94.2 cm³", "188.4 cm³", "141.3 cm³"], "answer": "A", "explanation": "體積 = π × 3² × 10 ≈ 282.6 cm³"},
                {"q": "兩平行線被截線所截，同位角的關係是？", "options": ["相等", "互補", "互餘", "不確定"], "answer": "A", "explanation": "平行線的同位角相等"},
            ],
            5: [
                {"q": "計算球體積：半徑 = 6cm（π ≈ 3.14）", "options": ["904.32 cm³", "452.16 cm³", "113.04 cm³", "1808.64 cm³"], "answer": "A", "explanation": "體積 = (4/3) × π × 6³ ≈ 904.32 cm³"},
                {"q": "正四面體有幾個面、幾條邊、幾個頂點？", "options": ["4面6邊4頂點", "4面4邊4頂點", "6面8邊4頂點", "4面8邊6頂點"], "answer": "A", "explanation": "正四面體：4個三角形面、6條邊、4個頂點"},
            ]
        }
    },
    "probability": {
        "name": "機率統計",
        "questions": {
            1: [
                {"q": "擲一枚公正硬幣，出現正面的機率是？", "options": ["1/2", "1/4", "1/3", "1"], "answer": "A", "explanation": "正面或反面各佔一半，機率 = 1/2"},
                {"q": "擲一顆骰子，出現偶數的機率是？", "options": ["1/2", "1/3", "1/6", "2/3"], "answer": "A", "explanation": "偶數有 2,4,6 共 3 個，機率 = 3/6 = 1/2"},
            ],
            2: [
                {"q": "從 1-10 中隨機抽一數，抽到質數的機率是？", "options": ["2/5", "1/2", "3/10", "1/5"], "answer": "A", "explanation": "質數有 2,3,5,7 共 4 個，機率 = 4/10 = 2/5"},
                {"q": "數據 2,4,6,8,10 的平均數是？", "options": ["6", "5", "7", "8"], "answer": "A", "explanation": "平均數 = (2+4+6+8+10)/5 = 30/5 = 6"},
            ],
            3: [
                {"q": "數據 3,5,7,9,11 的中位數是？", "options": ["7", "5", "9", "6"], "answer": "A", "explanation": "排序後中間的數是 7"},
                {"q": "同時擲兩顆骰子，點數和為 7 的機率是？", "options": ["1/6", "1/12", "1/9", "1/36"], "answer": "A", "explanation": "和為7的組合有6種，總共36種，機率 = 6/36 = 1/6"},
            ],
            4: [
                {"q": "數據 2,3,3,4,5,5,5,6 的眾數是？", "options": ["5", "3", "4", "2"], "answer": "A", "explanation": "5 出現 3 次最多，是眾數"},
                {"q": "標準差越大表示數據？", "options": ["越分散", "越集中", "越大", "越小"], "answer": "A", "explanation": "標準差衡量數據的離散程度"},
            ],
            5: [
                {"q": "從 52 張撲克牌抽一張，抽到紅心 A 的機率是？", "options": ["1/52", "1/13", "1/4", "4/52"], "answer": "A", "explanation": "紅心 A 只有 1 張，機率 = 1/52"},
            ]
        }
    },

    "functions": {
        "name": "函數",
        "questions": {
            1: [
                {"q": "若 f(x) = x + 3，則 f(2) = ?", "options": ["5", "6", "3", "2"], "answer": "A", "explanation": "f(2) = 2 + 3 = 5"},
                {"q": "y = 2x 是什麼類型的函數？", "options": ["一次函數", "二次函數", "常數函數", "反比例函數"], "answer": "A", "explanation": "y = 2x 是一次函數（線性函數）"},
            ],
            2: [
                {"q": "一次函數 y = 3x - 2 的斜率是？", "options": ["3", "-2", "2", "-3"], "answer": "A", "explanation": "y = mx + b 中，m = 3 是斜率"},
                {"q": "若 f(x) = x²，則 f(-3) = ?", "options": ["9", "-9", "6", "-6"], "answer": "A", "explanation": "f(-3) = (-3)² = 9"},
            ],
            3: [
                {"q": "二次函數 y = x² - 4x + 3 的頂點 x 座標是？", "options": ["2", "4", "-2", "3"], "answer": "A", "explanation": "頂點 x = -b/(2a) = 4/2 = 2"},
                {"q": "函數 y = 1/x 的圖形是？", "options": ["雙曲線", "拋物線", "直線", "圓"], "answer": "A", "explanation": "y = 1/x 是反比例函數，圖形為雙曲線"},
            ],
            4: [
                {"q": "y = x² - 6x + 5 的最小值是？", "options": ["-4", "5", "0", "-5"], "answer": "A", "explanation": "頂點 y = -(36-20)/4 = -4"},
                {"q": "若 f(x) = 2x + 1，g(x) = x²，則 f(g(2)) = ?", "options": ["9", "5", "10", "8"], "answer": "A", "explanation": "g(2) = 4, f(4) = 2(4) + 1 = 9"},
            ],
            5: [
                {"q": "函數 f(x) = |x - 2| + 1 的最小值是？", "options": ["1", "2", "0", "3"], "answer": "A", "explanation": "當 x = 2 時，|x-2| = 0，最小值 = 0 + 1 = 1"},
            ]
        }
    },
    "sequences": {
        "name": "數列",
        "questions": {
            1: [
                {"q": "等差數列 2, 5, 8, 11, ... 的公差是？", "options": ["3", "2", "5", "4"], "answer": "A", "explanation": "公差 = 5 - 2 = 3"},
                {"q": "等比數列 2, 6, 18, 54, ... 的公比是？", "options": ["3", "2", "4", "6"], "answer": "A", "explanation": "公比 = 6 ÷ 2 = 3"},
            ],
            2: [
                {"q": "等差數列首項 3，公差 4，第 5 項是？", "options": ["19", "15", "23", "11"], "answer": "A", "explanation": "a₅ = 3 + (5-1)×4 = 3 + 16 = 19"},
                {"q": "等比數列首項 2，公比 3，第 4 項是？", "options": ["54", "18", "162", "6"], "answer": "A", "explanation": "a₄ = 2 × 3³ = 2 × 27 = 54"},
            ],
            3: [
                {"q": "等差數列 1, 4, 7, 10, ... 前 10 項和是？", "options": ["145", "100", "130", "160"], "answer": "A", "explanation": "S₁₀ = 10×(1+28)/2 = 10×29/2 = 145"},
                {"q": "數列 1, 1, 2, 3, 5, 8, ... 的下一項是？", "options": ["13", "11", "14", "12"], "answer": "A", "explanation": "費波那契數列：5 + 8 = 13"},
            ],
            4: [
                {"q": "等比數列首項 1，公比 2，前 6 項和是？", "options": ["63", "64", "31", "32"], "answer": "A", "explanation": "S₆ = 1×(2⁶-1)/(2-1) = 63"},
                {"q": "等差數列第 3 項是 7，第 7 項是 19，公差是？", "options": ["3", "4", "2", "5"], "answer": "A", "explanation": "d = (19-7)/(7-3) = 12/4 = 3"},
            ],
            5: [
                {"q": "無窮等比級數 1 + 1/2 + 1/4 + 1/8 + ... 的和是？", "options": ["2", "1", "∞", "1.5"], "answer": "A", "explanation": "S = a/(1-r) = 1/(1-0.5) = 2"},
            ]
        }
    }
}

GRADE_LEVELS = {
    "elementary": "國小",
    "junior": "國中",
    "senior": "高中"
}

TOPICS = list(MATH_QUESTION_BANK.keys())


# ============ Request/Response Models ============

class PracticeConfig(BaseModel):
    """Configuration for starting a practice session."""
    grade: str = Field(default="junior", description="Grade level: elementary, junior, senior")
    topics: List[str] = Field(default=["algebra", "geometry"], description="Topics to include")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level 1-5")
    topic_weights: Optional[Dict[str, float]] = Field(default=None, description="Topic weights (e.g., {'algebra': 0.6, 'geometry': 0.4})")
    question_count: int = Field(default=10, ge=1, le=20, description="Number of questions")


class QuestionItem(BaseModel):
    """A single question in the practice session."""
    id: int
    question: str
    options: List[str]
    topic: str
    topic_name: str
    difficulty: int


class PracticeSessionResponse(BaseModel):
    """Response when starting a practice session."""
    session_id: str
    questions: List[QuestionItem]
    config: PracticeConfig


class AnswerSubmission(BaseModel):
    """Submission for a single answer."""
    question_id: int
    selected_option: str  # A, B, C, D
    reasoning: Optional[str] = Field(default=None, description="Student's reasoning/explanation")


class QuestionResult(BaseModel):
    """Result for a single question."""
    question_id: int
    is_correct: bool
    correct_answer: str
    selected_answer: str
    explanation: str
    reasoning_score: Optional[int] = None  # 0-100
    reasoning_feedback: Optional[str] = None
    ai_solution: Optional[str] = None


class PracticeSubmission(BaseModel):
    """Full practice session submission."""
    session_id: str
    answers: List[AnswerSubmission]


class PracticeResultResponse(BaseModel):
    """Final results for a practice session."""
    session_id: str
    total_questions: int
    correct_count: int
    score: float  # Percentage
    results: List[QuestionResult]
    overall_feedback: str
    topic_breakdown: Dict[str, Dict[str, Any]]
    time_spent_seconds: Optional[int] = None


# ============ In-memory session storage ============
practice_sessions: Dict[str, Dict[str, Any]] = {}


# ============ Helper Functions ============

def generate_questions(config: PracticeConfig) -> List[Dict[str, Any]]:
    """Generate questions based on configuration."""
    questions = []
    question_id = 1
    
    # Calculate how many questions per topic
    if config.topic_weights:
        weights = config.topic_weights
    else:
        # Equal distribution
        weights = {t: 1.0 / len(config.topics) for t in config.topics}
    
    # Normalize weights
    total_weight = sum(weights.get(t, 0) for t in config.topics)
    if total_weight == 0:
        total_weight = 1
    
    topic_counts = {}
    remaining = config.question_count
    
    for i, topic in enumerate(config.topics):
        if i == len(config.topics) - 1:
            # Last topic gets remaining questions
            topic_counts[topic] = remaining
        else:
            count = round(config.question_count * weights.get(topic, 0) / total_weight)
            topic_counts[topic] = min(count, remaining)
            remaining -= topic_counts[topic]
    
    # Generate questions for each topic
    for topic, count in topic_counts.items():
        if topic not in MATH_QUESTION_BANK:
            continue
        
        topic_data = MATH_QUESTION_BANK[topic]
        topic_questions = topic_data["questions"]
        
        # Get questions at or near the requested difficulty
        available = []
        for diff in [config.difficulty, config.difficulty - 1, config.difficulty + 1, 
                     config.difficulty - 2, config.difficulty + 2]:
            if 1 <= diff <= 5 and diff in topic_questions:
                available.extend([
                    {**q, "difficulty": diff, "topic": topic, "topic_name": topic_data["name"]}
                    for q in topic_questions[diff]
                ])
        
        # Randomly select questions
        if available:
            selected = random.sample(available, min(count, len(available)))
            for q in selected:
                questions.append({
                    "id": question_id,
                    "question": q["q"],
                    "options": q["options"],
                    "answer": q["answer"],
                    "explanation": q["explanation"],
                    "topic": q["topic"],
                    "topic_name": q["topic_name"],
                    "difficulty": q["difficulty"]
                })
                question_id += 1
    
    # Shuffle questions
    random.shuffle(questions)
    
    # Re-assign IDs after shuffle
    for i, q in enumerate(questions):
        q["id"] = i + 1
    
    return questions


async def evaluate_reasoning(question: str, correct_answer: str, student_reasoning: str) -> Dict[str, Any]:
    """Use LLM to evaluate student's reasoning."""
    system_prompt = """你是一位數學老師，負責評估學生的解題邏輯。
請根據以下標準評分（0-100分）：
- 邏輯正確性（40分）：解題步驟是否正確
- 完整性（30分）：是否涵蓋所有必要步驟
- 清晰度（30分）：表達是否清楚

請用繁體中文回答，格式如下：
分數：[0-100]
評語：[簡短評語，50字以內]"""

    prompt = f"""題目：{question}
正確答案：{correct_answer}
學生的解題邏輯：{student_reasoning}

請評估學生的解題邏輯。"""

    try:
        response = await llm_client.generate_async(prompt, system=system_prompt)
        text = response.text
        
        # Parse score from response
        score = 60  # Default score
        feedback = text
        
        if "分數：" in text or "分數:" in text:
            try:
                score_line = [l for l in text.split("\n") if "分數" in l][0]
                score_str = ''.join(c for c in score_line if c.isdigit())
                if score_str:
                    score = min(100, max(0, int(score_str)))
            except:
                pass
        
        if "評語：" in text or "評語:" in text:
            try:
                feedback = text.split("評語")[1].strip(":： \n")
            except:
                pass
        
        return {"score": score, "feedback": feedback}
    except Exception as e:
        return {"score": 50, "feedback": f"評估時發生錯誤：{str(e)}"}


async def generate_ai_solution(question: str, correct_answer: str, explanation: str) -> str:
    """Generate AI solution for a question."""
    system_prompt = """你是一位數學老師，請用簡潔清晰的方式解釋這道題目的解法。
使用繁體中文，回答控制在100字以內。"""

    prompt = f"""題目：{question}
正確答案：{correct_answer}
參考解釋：{explanation}

請提供詳細的解題步驟。"""

    try:
        response = await llm_client.generate_async(prompt, system=system_prompt)
        return response.text
    except Exception as e:
        return explanation  # Fallback to basic explanation


# ============ API Endpoints ============

@router.get("/topics")
async def get_available_topics():
    """Get list of available topics."""
    return {
        "topics": [
            {"id": topic, "name": data["name"]}
            for topic, data in MATH_QUESTION_BANK.items()
        ],
        "grades": [
            {"id": grade, "name": name}
            for grade, name in GRADE_LEVELS.items()
        ],
        "difficulties": [
            {"level": i, "name": ["非常簡單", "簡單", "中等", "困難", "非常困難"][i-1]}
            for i in range(1, 6)
        ]
    }


@router.post("/start", response_model=PracticeSessionResponse)
async def start_practice_session(config: PracticeConfig):
    """Start a new practice session with generated questions."""
    # Generate session ID
    session_id = f"practice-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
    
    # Generate questions
    questions = generate_questions(config)
    
    if not questions:
        raise HTTPException(status_code=400, detail="無法生成題目，請檢查設定")
    
    # Store session
    practice_sessions[session_id] = {
        "config": config.model_dump(),
        "questions": questions,
        "started_at": datetime.now(),
        "answers": {}
    }
    
    # Return questions without answers
    return PracticeSessionResponse(
        session_id=session_id,
        questions=[
            QuestionItem(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                topic=q["topic"],
                topic_name=q["topic_name"],
                difficulty=q["difficulty"]
            )
            for q in questions
        ],
        config=config
    )


class SingleAnswerCheck(BaseModel):
    """Request to check a single answer."""
    session_id: str
    question_id: int
    selected_option: str


class SingleAnswerResult(BaseModel):
    """Result for a single answer check."""
    is_correct: bool
    correct_answer: str
    explanation: str


@router.post("/check-answer", response_model=SingleAnswerResult)
async def check_single_answer(check: SingleAnswerCheck):
    """Check a single answer and return the correct answer (for immediate feedback)."""
    if check.session_id not in practice_sessions:
        raise HTTPException(status_code=404, detail="練習會話不存在")
    
    session = practice_sessions[check.session_id]
    questions = session["questions"]
    
    # Find the question
    question = None
    for q in questions:
        if q["id"] == check.question_id:
            question = q
            break
    
    if not question:
        raise HTTPException(status_code=404, detail="題目不存在")
    
    is_correct = check.selected_option.upper() == question["answer"]
    
    return SingleAnswerResult(
        is_correct=is_correct,
        correct_answer=question["answer"],
        explanation=question["explanation"]
    )


@router.post("/submit", response_model=PracticeResultResponse)
async def submit_practice(submission: PracticeSubmission):
    """Submit answers and get results with AI evaluation."""
    session_id = submission.session_id
    
    if session_id not in practice_sessions:
        raise HTTPException(status_code=404, detail="練習會話不存在")
    
    session = practice_sessions[session_id]
    questions = session["questions"]
    
    # Build question lookup
    question_map = {q["id"]: q for q in questions}
    
    results = []
    correct_count = 0
    topic_stats = {}
    
    for answer in submission.answers:
        q = question_map.get(answer.question_id)
        if not q:
            continue
        
        is_correct = answer.selected_option.upper() == q["answer"]
        if is_correct:
            correct_count += 1
        
        # Track topic stats
        topic = q["topic"]
        if topic not in topic_stats:
            topic_stats[topic] = {"correct": 0, "total": 0, "name": q["topic_name"]}
        topic_stats[topic]["total"] += 1
        if is_correct:
            topic_stats[topic]["correct"] += 1
        
        # Evaluate reasoning if provided
        reasoning_score = None
        reasoning_feedback = None
        ai_solution = None
        
        if answer.reasoning and answer.reasoning.strip():
            eval_result = await evaluate_reasoning(
                q["question"],
                q["options"][ord(q["answer"]) - ord("A")],
                answer.reasoning
            )
            reasoning_score = eval_result["score"]
            reasoning_feedback = eval_result["feedback"]
        else:
            # Generate AI solution if no reasoning provided
            ai_solution = await generate_ai_solution(
                q["question"],
                q["options"][ord(q["answer"]) - ord("A")],
                q["explanation"]
            )
        
        results.append(QuestionResult(
            question_id=answer.question_id,
            is_correct=is_correct,
            correct_answer=q["answer"],
            selected_answer=answer.selected_option.upper(),
            explanation=q["explanation"],
            reasoning_score=reasoning_score,
            reasoning_feedback=reasoning_feedback,
            ai_solution=ai_solution
        ))
    
    # Calculate score
    total = len(submission.answers)
    score = (correct_count / total * 100) if total > 0 else 0
    
    # Calculate time spent
    time_spent = None
    if "started_at" in session:
        time_spent = int((datetime.now() - session["started_at"]).total_seconds())
    
    # Generate overall feedback
    if score >= 90:
        overall_feedback = "太棒了！你的表現非常優秀，繼續保持！"
    elif score >= 70:
        overall_feedback = "做得不錯！還有一些小地方可以加強。"
    elif score >= 50:
        overall_feedback = "還可以再努力一點，建議複習錯題並多練習。"
    else:
        overall_feedback = "需要加強基礎概念，建議從簡單的題目開始練習。"
    
    # Add topic-specific feedback
    for topic, stats in topic_stats.items():
        rate = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        stats["accuracy"] = round(rate, 1)
    
    # Clean up session
    del practice_sessions[session_id]
    
    return PracticeResultResponse(
        session_id=session_id,
        total_questions=total,
        correct_count=correct_count,
        score=round(score, 1),
        results=results,
        overall_feedback=overall_feedback,
        topic_breakdown=topic_stats,
        time_spent_seconds=time_spent
    )


@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """Get current session status."""
    if session_id not in practice_sessions:
        raise HTTPException(status_code=404, detail="練習會話不存在")
    
    session = practice_sessions[session_id]
    return {
        "session_id": session_id,
        "question_count": len(session["questions"]),
        "started_at": session["started_at"].isoformat(),
        "config": session["config"]
    }
