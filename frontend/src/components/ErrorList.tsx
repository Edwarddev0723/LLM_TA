/**
 * ErrorList component for displaying error records
 * Requirements: 4.3 - 錯題列表
 */

import type { ErrorRecord, ErrorType } from '../types';
import './ErrorList.css';

interface ErrorListProps {
  errors: ErrorRecord[];
  onSelectError: (error: ErrorRecord) => void;
  onStartReview: (error: ErrorRecord) => void;
  selectedErrorId?: string;
  emptyMessage?: string;
}

const ERROR_TYPE_LABELS: Record<ErrorType, string> = {
  CALCULATION: '計算錯誤',
  CONCEPT: '觀念錯誤',
  CARELESS: '粗心錯誤',
};

const ERROR_TYPE_COLORS: Record<ErrorType, string> = {
  CALCULATION: 'error-calculation',
  CONCEPT: 'error-concept',
  CARELESS: 'error-careless',
};

export function ErrorList({
  errors,
  onSelectError,
  onStartReview,
  selectedErrorId,
  emptyMessage = '沒有錯題記錄',
}: ErrorListProps) {
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  if (errors.length === 0) {
    return (
      <div className="error-list-empty">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="error-list">
      <div className="list-header">
        <span className="list-count">共 {errors.length} 題錯題</span>
      </div>
      <ul className="list-items">
        {errors.map((error) => (
          <li
            key={error.id}
            className={`error-item ${selectedErrorId === error.id ? 'selected' : ''} ${error.repaired ? 'repaired' : ''}`}
            onClick={() => onSelectError(error)}
          >
            <div className="error-header">
              <span className={`error-type-badge ${ERROR_TYPE_COLORS[error.error_type]}`}>
                {ERROR_TYPE_LABELS[error.error_type]}
              </span>
              {error.repaired && <span className="repaired-badge">✓ 已修復</span>}
            </div>

            <div className="error-content">
              <p className="error-question">題目 ID: {error.question_id}</p>
              <div className="error-answers">
                <span className="wrong-answer">你的答案: {error.student_answer}</span>
                <span className="correct-answer">正確答案: {error.correct_answer}</span>
              </div>
            </div>

            <div className="error-footer">
              <span className="error-date">{formatDate(error.timestamp)}</span>
              {error.error_tags.length > 0 && (
                <div className="error-tags">
                  {error.error_tags.slice(0, 2).map((tag, index) => (
                    <span key={index} className="tag">
                      {tag}
                    </span>
                  ))}
                  {error.error_tags.length > 2 && (
                    <span className="tag more">+{error.error_tags.length - 2}</span>
                  )}
                </div>
              )}
              {!error.repaired && (
                <button
                  className="btn-review"
                  onClick={(e) => {
                    e.stopPropagation();
                    onStartReview(error);
                  }}
                >
                  重新講解
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
