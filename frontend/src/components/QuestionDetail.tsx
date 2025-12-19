/**
 * QuestionDetail component for displaying question details and answer submission
 * Requirements: 1.2, 3.1 - 題目詳情顯示與答題回饋
 */

import { useState } from 'react';
import type { Question, DifficultyLevel, ValidateAnswerResponse } from '../types';
import './QuestionDetail.css';

interface QuestionDetailProps {
  question: Question;
  onValidateAnswer: (answer: string) => Promise<ValidateAnswerResponse>;
  onStartPractice: () => void;
  isValidating?: boolean;
}

const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  1: '簡單',
  2: '中等',
  3: '困難',
};

const TYPE_LABELS: Record<string, string> = {
  MULTIPLE_CHOICE: '選擇題',
  FILL_BLANK: '填空題',
  CALCULATION: '計算題',
  PROOF: '證明題',
};

export function QuestionDetail({
  question,
  onValidateAnswer,
  onStartPractice,
  isValidating,
}: QuestionDetailProps) {
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<ValidateAnswerResponse | null>(null);
  const [showSolution, setShowSolution] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;

    try {
      const response = await onValidateAnswer(answer);
      setResult(response);
    } catch (error) {
      console.error('Failed to validate answer:', error);
    }
  };

  const handleReset = () => {
    setAnswer('');
    setResult(null);
    setShowSolution(false);
  };

  return (
    <div className="question-detail">
      <div className="detail-header">
        <div className="detail-badges">
          <span className={`difficulty-badge difficulty-${question.difficulty}`}>
            {DIFFICULTY_LABELS[question.difficulty]}
          </span>
          <span className="type-badge">{TYPE_LABELS[question.type] || question.type}</span>
        </div>
        <div className="detail-meta">
          <span>{question.subject}</span>
          <span className="separator">•</span>
          <span>{question.unit}</span>
        </div>
      </div>

      <div className="detail-content">
        <h3>題目</h3>
        <p className="question-text">{question.content}</p>
      </div>

      {!result && (
        <form className="answer-form" onSubmit={handleSubmit}>
          <label htmlFor="answer">你的答案</label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="請輸入你的答案..."
            rows={3}
            disabled={isValidating}
          />
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={isValidating || !answer.trim()}>
              {isValidating ? '驗證中...' : '提交答案'}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={onStartPractice}
              disabled={isValidating}
            >
              開始口語講題
            </button>
          </div>
        </form>
      )}

      {result && (
        <div className={`result-panel ${result.is_correct ? 'correct' : 'incorrect'}`}>
          <div className="result-header">
            <span className="result-icon">{result.is_correct ? '✓' : '✗'}</span>
            <span className="result-text">{result.is_correct ? '答對了！' : '答錯了'}</span>
            {result.response_time_ms && (
              <span className="response-time">回應時間: {result.response_time_ms}ms</span>
            )}
          </div>

          <div className="result-details">
            <div className="result-row">
              <span className="label">你的答案:</span>
              <span className="value">{result.student_answer}</span>
            </div>
            {!result.is_correct && (
              <div className="result-row">
                <span className="label">正確答案:</span>
                <span className="value correct-answer">{result.correct_answer}</span>
              </div>
            )}
            {result.feedback && (
              <div className="result-feedback">
                <p>{result.feedback}</p>
              </div>
            )}
          </div>

          <div className="result-actions">
            <button className="btn-secondary" onClick={handleReset}>
              再試一次
            </button>
            {!result.is_correct && (
              <button className="btn-primary" onClick={onStartPractice}>
                開始口語講題
              </button>
            )}
            {result.is_correct && question.standard_solution && (
              <button
                className="btn-secondary"
                onClick={() => setShowSolution(!showSolution)}
              >
                {showSolution ? '隱藏解答' : '查看解答'}
              </button>
            )}
          </div>
        </div>
      )}

      {showSolution && question.standard_solution && (
        <div className="solution-panel">
          <h4>標準解答</h4>
          <p>{question.standard_solution}</p>
        </div>
      )}

      {question.hints.length > 0 && (
        <div className="hints-panel">
          <h4>提示 ({question.hints.length} 個)</h4>
          <p className="hints-note">提示將在口語講題時依需要提供</p>
        </div>
      )}
    </div>
  );
}
