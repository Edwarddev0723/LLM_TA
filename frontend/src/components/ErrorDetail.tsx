/**
 * ErrorDetail component for displaying error record details
 * Requirements: 8.1 - 錯題重述流程
 */

import type { ErrorRecord, ErrorType } from '../types';
import './ErrorDetail.css';

interface ErrorDetailProps {
  error: ErrorRecord;
  onStartReview: () => void;
  onMarkRepaired: () => void;
  isMarking?: boolean;
}

const ERROR_TYPE_LABELS: Record<ErrorType, string> = {
  CALCULATION: '計算錯誤',
  CONCEPT: '觀念錯誤',
  CARELESS: '粗心錯誤',
};

const ERROR_TYPE_DESCRIPTIONS: Record<ErrorType, string> = {
  CALCULATION: '在計算過程中出現錯誤，可能是運算符號或數字處理不當',
  CONCEPT: '對數學概念的理解有偏差，需要重新理解相關知識點',
  CARELESS: '因粗心大意導致的錯誤，如抄錯數字或看錯題目',
};

export function ErrorDetail({
  error,
  onStartReview,
  onMarkRepaired,
  isMarking,
}: ErrorDetailProps) {
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="error-detail">
      <div className="detail-header">
        <div className="detail-badges">
          <span className={`error-type-badge error-${error.error_type.toLowerCase()}`}>
            {ERROR_TYPE_LABELS[error.error_type]}
          </span>
          {error.repaired && (
            <span className="repaired-badge">✓ 已修復</span>
          )}
        </div>
        <span className="error-date">{formatDate(error.timestamp)}</span>
      </div>

      <div className="detail-section">
        <h4>題目資訊</h4>
        <p className="question-id">題目 ID: {error.question_id}</p>
      </div>

      <div className="detail-section">
        <h4>答案比較</h4>
        <div className="answer-comparison">
          <div className="answer-box wrong">
            <span className="answer-label">你的答案</span>
            <p className="answer-value">{error.student_answer}</p>
          </div>
          <div className="answer-box correct">
            <span className="answer-label">正確答案</span>
            <p className="answer-value">{error.correct_answer}</p>
          </div>
        </div>
      </div>

      <div className="detail-section">
        <h4>錯誤分析</h4>
        <p className="error-description">
          {ERROR_TYPE_DESCRIPTIONS[error.error_type]}
        </p>
        {error.error_tags.length > 0 && (
          <div className="error-tags">
            <span className="tags-label">相關標籤:</span>
            {error.error_tags.map((tag, index) => (
              <span key={index} className="tag">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {error.repaired && error.repaired_at && (
        <div className="detail-section repaired-info">
          <h4>修復資訊</h4>
          <p>修復時間: {formatDate(error.repaired_at)}</p>
        </div>
      )}

      <div className="detail-actions">
        {!error.repaired ? (
          <>
            <button className="btn-primary" onClick={onStartReview}>
              開始重新講解
            </button>
            <button
              className="btn-secondary"
              onClick={onMarkRepaired}
              disabled={isMarking}
            >
              {isMarking ? '處理中...' : '標記為已修復'}
            </button>
          </>
        ) : (
          <button className="btn-secondary" onClick={onStartReview}>
            再次練習
          </button>
        )}
      </div>
    </div>
  );
}
