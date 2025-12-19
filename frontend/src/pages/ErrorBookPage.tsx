/**
 * ErrorBookPage - Main page for error book management
 * Requirements: 4.3, 8.1 - 錯題本頁面
 */

import { useState, useCallback, useEffect } from 'react';
import { ErrorFilter } from '../components/ErrorFilter';
import { ErrorList } from '../components/ErrorList';
import { ErrorDetail } from '../components/ErrorDetail';
import { errorApi } from '../api';
import type { ErrorRecord, ErrorCriteria } from '../types';
import './ErrorBookPage.css';

interface ErrorBookPageProps {
  studentId: string;
  onStartReview: (questionId: string) => void;
}

export function ErrorBookPage({ studentId, onStartReview }: ErrorBookPageProps) {
  const [errors, setErrors] = useState<ErrorRecord[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMarking, setIsMarking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  // Load errors on mount
  useEffect(() => {
    loadErrors({});
  }, [studentId]);

  const loadErrors = useCallback(
    async (criteria: ErrorCriteria) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await errorApi.getErrors(studentId, criteria);
        setErrors(response.errors);
        setSelectedError(null);
        setHasLoaded(true);
      } catch (err) {
        console.error('Failed to load errors:', err);
        setError('無法載入錯題記錄，請稍後再試');
        setErrors([]);
      } finally {
        setIsLoading(false);
      }
    },
    [studentId]
  );

  const handleFilter = useCallback(
    (criteria: ErrorCriteria) => {
      loadErrors(criteria);
    },
    [loadErrors]
  );

  const handleSelectError = useCallback((errorRecord: ErrorRecord) => {
    setSelectedError(errorRecord);
  }, []);

  const handleStartReview = useCallback(
    (errorRecord: ErrorRecord) => {
      onStartReview(errorRecord.question_id);
    },
    [onStartReview]
  );

  const handleMarkRepaired = useCallback(async () => {
    if (!selectedError) return;

    setIsMarking(true);
    try {
      await errorApi.markAsRepaired(selectedError.id);
      
      // Update local state
      setErrors((prev) =>
        prev.map((e) =>
          e.id === selectedError.id
            ? { ...e, repaired: true, repaired_at: new Date().toISOString() }
            : e
        )
      );
      setSelectedError((prev) =>
        prev ? { ...prev, repaired: true, repaired_at: new Date().toISOString() } : null
      );
    } catch (err) {
      console.error('Failed to mark as repaired:', err);
      setError('無法標記為已修復，請稍後再試');
    } finally {
      setIsMarking(false);
    }
  }, [selectedError]);

  return (
    <div className="error-book-page">
      <header className="page-header">
        <h1>錯題本</h1>
        <p className="page-subtitle">複習錯題，鞏固學習成果</p>
      </header>

      <div className="error-book-layout">
        <aside className="filter-sidebar">
          <ErrorFilter onFilter={handleFilter} isLoading={isLoading} />
        </aside>

        <main className="error-book-main">
          {error && (
            <div className="error-message">
              <p>{error}</p>
            </div>
          )}

          {!hasLoaded && !error && (
            <div className="loading-state">
              <p>載入中...</p>
            </div>
          )}

          {hasLoaded && !error && (
            <div className="content-area">
              <div className="error-list-container">
                <ErrorList
                  errors={errors}
                  onSelectError={handleSelectError}
                  onStartReview={handleStartReview}
                  selectedErrorId={selectedError?.id}
                  emptyMessage={
                    isLoading ? '載入中...' : '沒有錯題記錄，繼續保持！'
                  }
                />
              </div>

              {selectedError && (
                <div className="error-detail-container">
                  <ErrorDetail
                    error={selectedError}
                    onStartReview={() => handleStartReview(selectedError)}
                    onMarkRepaired={handleMarkRepaired}
                    isMarking={isMarking}
                  />
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
