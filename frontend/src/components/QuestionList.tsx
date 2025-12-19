/**
 * QuestionList component for displaying filtered questions
 * Requirements: 1.2 - 返回符合條件的題目列表
 */

import type { Question, DifficultyLevel } from '../types';
import './QuestionList.css';

interface QuestionListProps {
  questions: Question[];
  onSelectQuestion: (question: Question) => void;
  selectedQuestionId?: string;
  emptyMessage?: string;
}

const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  1: '簡單',
  2: '中等',
  3: '困難',
};

const DIFFICULTY_COLORS: Record<DifficultyLevel, string> = {
  1: 'difficulty-easy',
  2: 'difficulty-medium',
  3: 'difficulty-hard',
};

const TYPE_LABELS: Record<string, string> = {
  MULTIPLE_CHOICE: '選擇題',
  FILL_BLANK: '填空題',
  CALCULATION: '計算題',
  PROOF: '證明題',
};

export function QuestionList({
  questions,
  onSelectQuestion,
  selectedQuestionId,
  emptyMessage = '無符合條件的題目，請調整篩選條件',
}: QuestionListProps) {
  if (questions.length === 0) {
    return (
      <div className="question-list-empty">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="question-list">
      <div className="list-header">
        <span className="list-count">共 {questions.length} 題</span>
      </div>
      <ul className="list-items">
        {questions.map((question) => (
          <li
            key={question.id}
            className={`question-item ${selectedQuestionId === question.id ? 'selected' : ''}`}
            onClick={() => onSelectQuestion(question)}
          >
            <div className="question-header">
              <span className={`difficulty-badge ${DIFFICULTY_COLORS[question.difficulty]}`}>
                {DIFFICULTY_LABELS[question.difficulty]}
              </span>
              <span className="type-badge">{TYPE_LABELS[question.type] || question.type}</span>
            </div>
            <p className="question-content">{question.content}</p>
            <div className="question-meta">
              <span className="meta-item">{question.subject}</span>
              <span className="meta-separator">•</span>
              <span className="meta-item">{question.unit}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
