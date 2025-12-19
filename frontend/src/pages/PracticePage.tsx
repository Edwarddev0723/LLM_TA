/**
 * PracticePage - Main page for question filtering and practice
 * Requirements: 1.1, 1.2 - 題目篩選與練習頁面
 */

import { useState, useCallback } from 'react';
import { QuestionFilter } from '../components/QuestionFilter';
import { QuestionList } from '../components/QuestionList';
import { QuestionDetail } from '../components/QuestionDetail';
import { questionApi } from '../api';
import type { Question, QuestionCriteria, ValidateAnswerResponse } from '../types';
import './PracticePage.css';

interface PracticePageProps {
  studentId: string;
  onStartSession: (questionId: string) => void;
}

export function PracticePage({ studentId: _studentId, onStartSession }: PracticePageProps) {
  // studentId will be used when implementing session creation
  void _studentId;
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleFilter = useCallback(async (criteria: QuestionCriteria) => {
    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await questionApi.filterQuestions(criteria);
      setQuestions(response.questions);
      setSelectedQuestion(null);
    } catch (err) {
      console.error('Failed to filter questions:', err);
      setError('無法載入題目，請稍後再試');
      setQuestions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSelectQuestion = useCallback((question: Question) => {
    setSelectedQuestion(question);
  }, []);

  const handleValidateAnswer = useCallback(
    async (answer: string): Promise<ValidateAnswerResponse> => {
      if (!selectedQuestion) {
        throw new Error('No question selected');
      }

      setIsValidating(true);
      try {
        const response = await questionApi.validateAnswer({
          question_id: selectedQuestion.id,
          answer,
        });
        return response;
      } finally {
        setIsValidating(false);
      }
    },
    [selectedQuestion]
  );

  const handleStartPractice = useCallback(() => {
    if (selectedQuestion) {
      onStartSession(selectedQuestion.id);
    }
  }, [selectedQuestion, onStartSession]);

  return (
    <div className="practice-page">
      <header className="page-header">
        <h1>題目練習</h1>
        <p className="page-subtitle">選擇題目開始練習，或進行口語講題</p>
      </header>

      <div className="practice-layout">
        <aside className="filter-sidebar">
          <QuestionFilter onFilter={handleFilter} isLoading={isLoading} />
        </aside>

        <main className="practice-main">
          {error && (
            <div className="error-message">
              <p>{error}</p>
            </div>
          )}

          {!hasSearched && !error && (
            <div className="welcome-message">
              <h2>歡迎使用 AI 數學助教</h2>
              <p>請使用左側篩選條件搜尋題目，開始你的學習之旅！</p>
            </div>
          )}

          {hasSearched && !error && (
            <div className="content-area">
              <div className="question-list-container">
                <QuestionList
                  questions={questions}
                  onSelectQuestion={handleSelectQuestion}
                  selectedQuestionId={selectedQuestion?.id}
                  emptyMessage={
                    isLoading
                      ? '載入中...'
                      : '無符合條件的題目，請調整篩選條件'
                  }
                />
              </div>

              {selectedQuestion && (
                <div className="question-detail-container">
                  <QuestionDetail
                    question={selectedQuestion}
                    onValidateAnswer={handleValidateAnswer}
                    onStartPractice={handleStartPractice}
                    isValidating={isValidating}
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
