#!/usr/bin/env python3
"""
資料庫初始化腳本 - 建立表格並插入範例資料
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from backend.models.database import Base, engine, SessionLocal
from backend.models.knowledge import KnowledgeNode, KnowledgeRelation
from backend.models.question import Question, Misconception, Hint


def create_tables():
    """建立所有資料庫表格"""
    print("建立資料庫表格...")
    Base.metadata.create_all(bind=engine)
    print("✓ 表格建立完成")


def create_sample_knowledge_nodes(db):
    """建立範例知識圖譜節點"""
    print("建立知識圖譜節點...")
    
    nodes = [
        # 代數
        KnowledgeNode(
            id="algebra-linear-eq",
            name="一元一次方程式",
            subject="數學",
            unit="代數",
            difficulty=1,
            description="包含一個未知數的一次方程式，形如 ax + b = c"
        ),
        KnowledgeNode(
            id="algebra-quadratic-eq",
            name="一元二次方程式",
            subject="數學",
            unit="代數",
            difficulty=2,
            description="包含一個未知數的二次方程式，形如 ax² + bx + c = 0"
        ),
        KnowledgeNode(
            id="algebra-factoring",
            name="因式分解",
            subject="數學",
            unit="代數",
            difficulty=2,
            description="將多項式分解為較簡單因式的乘積"
        ),
        KnowledgeNode(
            id="algebra-quadratic-formula",
            name="公式解",
            subject="數學",
            unit="代數",
            difficulty=2,
            description="使用公式 x = (-b ± √(b²-4ac)) / 2a 求解二次方程式"
        ),
        # 幾何
        KnowledgeNode(
            id="geometry-triangle",
            name="三角形性質",
            subject="數學",
            unit="幾何",
            difficulty=1,
            description="三角形的基本性質，包含內角和、邊長關係等"
        ),
        KnowledgeNode(
            id="geometry-pythagorean",
            name="畢氏定理",
            subject="數學",
            unit="幾何",
            difficulty=2,
            description="直角三角形中，斜邊平方等於兩股平方和：a² + b² = c²"
        ),
        KnowledgeNode(
            id="geometry-circle",
            name="圓的性質",
            subject="數學",
            unit="幾何",
            difficulty=2,
            description="圓的基本性質，包含圓周、面積、弦、弧等"
        ),
        # 統計
        KnowledgeNode(
            id="stats-mean",
            name="平均數",
            subject="數學",
            unit="統計",
            difficulty=1,
            description="一組數據的算術平均值"
        ),
        KnowledgeNode(
            id="stats-median",
            name="中位數",
            subject="數學",
            unit="統計",
            difficulty=1,
            description="將數據排序後位於中間位置的數值"
        ),
    ]
    
    for node in nodes:
        existing = db.query(KnowledgeNode).filter_by(id=node.id).first()
        if not existing:
            db.add(node)
    
    db.commit()
    print(f"✓ 建立 {len(nodes)} 個知識節點")
    
    # 建立知識節點關聯
    relations = [
        KnowledgeRelation(
            from_id="algebra-linear-eq",
            to_id="algebra-quadratic-eq",
            relation_type="PREREQUISITE",
            weight=1.0
        ),
        KnowledgeRelation(
            from_id="algebra-factoring",
            to_id="algebra-quadratic-eq",
            relation_type="RELATED",
            weight=0.8
        ),
        KnowledgeRelation(
            from_id="algebra-quadratic-formula",
            to_id="algebra-quadratic-eq",
            relation_type="RELATED",
            weight=0.9
        ),
        KnowledgeRelation(
            from_id="geometry-triangle",
            to_id="geometry-pythagorean",
            relation_type="PREREQUISITE",
            weight=1.0
        ),
    ]
    
    for rel in relations:
        existing = db.query(KnowledgeRelation).filter_by(
            from_id=rel.from_id, to_id=rel.to_id, relation_type=rel.relation_type
        ).first()
        if not existing:
            db.add(rel)
    
    db.commit()
    print(f"✓ 建立 {len(relations)} 個知識關聯")


def create_sample_questions(db):
    """建立範例題目"""
    print("建立範例題目...")
    
    questions = [
        # 一元一次方程式
        Question(
            id="q-linear-001",
            content="解方程式：3x + 5 = 20",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=1,
            standard_solution="3x + 5 = 20\n3x = 20 - 5\n3x = 15\nx = 5"
        ),
        Question(
            id="q-linear-002",
            content="解方程式：2(x - 3) = 10",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=1,
            standard_solution="2(x - 3) = 10\n2x - 6 = 10\n2x = 16\nx = 8"
        ),
        Question(
            id="q-linear-003",
            content="小明有一些糖果，給了弟弟 5 顆後，剩下的是原來的 2/3。請問小明原來有幾顆糖果？",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=2,
            standard_solution="設原來有 x 顆糖果\nx - 5 = (2/3)x\nx - (2/3)x = 5\n(1/3)x = 5\nx = 15\n答：小明原來有 15 顆糖果"
        ),
        # 一元二次方程式
        Question(
            id="q-quadratic-001",
            content="解方程式：x² - 5x + 6 = 0",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=2,
            standard_solution="x² - 5x + 6 = 0\n(x - 2)(x - 3) = 0\nx = 2 或 x = 3"
        ),
        Question(
            id="q-quadratic-002",
            content="解方程式：x² + 4x - 5 = 0",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=2,
            standard_solution="x² + 4x - 5 = 0\n(x + 5)(x - 1) = 0\nx = -5 或 x = 1"
        ),
        Question(
            id="q-quadratic-003",
            content="使用公式解求解：2x² - 3x - 2 = 0",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=3,
            standard_solution="a=2, b=-3, c=-2\nx = (3 ± √(9+16)) / 4\nx = (3 ± 5) / 4\nx = 2 或 x = -1/2"
        ),
        # 幾何
        Question(
            id="q-geometry-001",
            content="一個直角三角形的兩股分別為 3 公分和 4 公分，求斜邊長度。",
            type="CALCULATION",
            subject="數學",
            unit="幾何",
            difficulty=1,
            standard_solution="根據畢氏定理：c² = a² + b²\nc² = 3² + 4² = 9 + 16 = 25\nc = 5\n答：斜邊長度為 5 公分"
        ),
        Question(
            id="q-geometry-002",
            content="一個圓的半徑為 7 公分，求圓的面積。（π 取 22/7）",
            type="CALCULATION",
            subject="數學",
            unit="幾何",
            difficulty=1,
            standard_solution="圓面積 = πr²\n= (22/7) × 7²\n= (22/7) × 49\n= 154\n答：圓的面積為 154 平方公分"
        ),
        Question(
            id="q-geometry-003",
            content="三角形 ABC 中，∠A = 50°，∠B = 70°，求 ∠C。",
            type="CALCULATION",
            subject="數學",
            unit="幾何",
            difficulty=1,
            standard_solution="三角形內角和 = 180°\n∠C = 180° - ∠A - ∠B\n∠C = 180° - 50° - 70°\n∠C = 60°"
        ),
        # 統計
        Question(
            id="q-stats-001",
            content="求以下數據的平均數：12, 15, 18, 21, 24",
            type="CALCULATION",
            subject="數學",
            unit="統計",
            difficulty=1,
            standard_solution="平均數 = (12 + 15 + 18 + 21 + 24) / 5\n= 90 / 5\n= 18"
        ),
        Question(
            id="q-stats-002",
            content="求以下數據的中位數：7, 3, 9, 5, 11, 2, 8",
            type="CALCULATION",
            subject="數學",
            unit="統計",
            difficulty=1,
            standard_solution="先排序：2, 3, 5, 7, 8, 9, 11\n共 7 個數，中位數是第 4 個\n中位數 = 7"
        ),
    ]
    
    for q in questions:
        existing = db.query(Question).filter_by(id=q.id).first()
        if not existing:
            db.add(q)
    
    db.commit()
    print(f"✓ 建立 {len(questions)} 道題目")
    
    # 建立迷思概念
    misconceptions = [
        Misconception(
            id="misc-001",
            question_id="q-linear-001",
            description="移項時忘記變號",
            error_type="CONCEPT",
            correction="移項時要記得變號，正變負、負變正"
        ),
        Misconception(
            id="misc-002",
            question_id="q-quadratic-001",
            description="因式分解時找錯因數",
            error_type="CALCULATION",
            correction="找兩個數相乘等於常數項，相加等於一次項係數"
        ),
        Misconception(
            id="misc-003",
            question_id="q-geometry-001",
            description="畢氏定理公式記錯",
            error_type="CONCEPT",
            correction="畢氏定理：斜邊² = 股¹² + 股²²，斜邊是最長的邊"
        ),
    ]
    
    for m in misconceptions:
        existing = db.query(Misconception).filter_by(id=m.id).first()
        if not existing:
            db.add(m)
    
    db.commit()
    print(f"✓ 建立 {len(misconceptions)} 個迷思概念")
    
    # 建立提示
    hints = [
        # q-linear-001 的提示
        Hint(id="hint-001", question_id="q-linear-001", level=1, content="想想看，要怎麼把 x 單獨留在等號一邊？"),
        Hint(id="hint-002", question_id="q-linear-001", level=2, content="先把 +5 移到等號右邊，記得要變號"),
        Hint(id="hint-003", question_id="q-linear-001", level=3, content="3x = 15，兩邊同除以 3 就能得到 x 的值"),
        # q-quadratic-001 的提示
        Hint(id="hint-004", question_id="q-quadratic-001", level=1, content="這題可以用因式分解來解"),
        Hint(id="hint-005", question_id="q-quadratic-001", level=2, content="找兩個數，相乘等於 6，相加等於 -5"),
        Hint(id="hint-006", question_id="q-quadratic-001", level=3, content="這兩個數是 -2 和 -3，所以 (x-2)(x-3)=0"),
        # q-geometry-001 的提示
        Hint(id="hint-007", question_id="q-geometry-001", level=1, content="這是直角三角形，可以用什麼定理？"),
        Hint(id="hint-008", question_id="q-geometry-001", level=2, content="畢氏定理：斜邊² = 兩股平方和"),
        Hint(id="hint-009", question_id="q-geometry-001", level=3, content="c² = 3² + 4² = 9 + 16 = 25，所以 c = ?"),
    ]
    
    for h in hints:
        existing = db.query(Hint).filter_by(id=h.id).first()
        if not existing:
            db.add(h)
    
    db.commit()
    print(f"✓ 建立 {len(hints)} 個提示")


def main():
    """主程式"""
    print("=" * 50)
    print("AI 數學語音助教 - 資料庫初始化")
    print("=" * 50)
    
    # 建立表格
    create_tables()
    
    # 建立範例資料
    db = SessionLocal()
    try:
        create_sample_knowledge_nodes(db)
        create_sample_questions(db)
        print("=" * 50)
        print("✓ 資料庫初始化完成！")
        print("=" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    main()
