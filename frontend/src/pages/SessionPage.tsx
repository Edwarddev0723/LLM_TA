/**
 * SessionPage - Main page for oral practice sessions
 * Requirements: 6.1, 6.6, 7.1 - 口語講題介面
 */

import { useState, useCallback, useEffect } from 'react';
import { VoiceInput } from '../components/VoiceInput';
import { FSMStateIndicator } from '../components/FSMStateIndicator';
import { ConversationPanel } from '../components/ConversationPanel';
import type { ConversationMessage } from '../components/ConversationPanel';
import { sessionApi, questionApi } from '../api';
import type { Question, FSMState, TutorResponse, SessionState } from '../types';
import './SessionPage.css';

interface SessionPageProps {
  questionId: string;
  studentId: string;
  onEndSession: () => void;
}

export function SessionPage({ questionId, studentId, onEndSession }: SessionPageProps) {
  const [question, setQuestion] = useState<Question | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      try {
        setIsInitializing(true);
        setError(null);

        // Fetch question details
        const questionData = await questionApi.getQuestion(questionId);
        setQuestion(questionData);

        // Start session
        const response = await sessionApi.startSession({
          question_id: questionId,
          student_id: studentId,
        });

        setSessionId(response.session_id);

        // Add initial tutor message
        setMessages([
          {
            id: `msg-${Date.now()}`,
            speaker: 'tutor',
            text: response.message,
            timestamp: new Date(),
            responseType: 'ACKNOWLEDGE',
          },
        ]);

        // Get initial session state
        const state = await sessionApi.getSessionState(response.session_id);
        setSessionState(state);
      } catch (err) {
        console.error('Failed to initialize session:', err);
        setError('無法開始會話，請稍後再試');
      } finally {
        setIsInitializing(false);
      }
    };

    initSession();
  }, [questionId, studentId]);

  const handleTranscription = useCallback(
    async (text: string, _audioBlob: Blob | null) => {
      if (!sessionId || !text.trim()) return;

      // Add student message
      const studentMessage: ConversationMessage = {
        id: `msg-${Date.now()}`,
        speaker: 'student',
        text: text.trim(),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, studentMessage]);

      setIsLoading(true);
      try {
        // Process input and get tutor response
        const response: TutorResponse = await sessionApi.processInput(sessionId, {
          text: text.trim(),
        });

        // Add tutor response
        const tutorMessage: ConversationMessage = {
          id: `msg-${Date.now() + 1}`,
          speaker: 'tutor',
          text: response.text,
          timestamp: new Date(),
          responseType: response.response_type,
          hintLevel: response.hint_level,
        };
        setMessages((prev) => [...prev, tutorMessage]);

        // Update session state
        const state = await sessionApi.getSessionState(sessionId);
        setSessionState(state);
      } catch (err) {
        console.error('Failed to process input:', err);
        // Add error message
        const errorMessage: ConversationMessage = {
          id: `msg-${Date.now() + 1}`,
          speaker: 'tutor',
          text: '抱歉，處理你的回答時發生錯誤，請再試一次。',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  const handleEndSession = useCallback(async () => {
    if (!sessionId) {
      onEndSession();
      return;
    }

    try {
      const summary = await sessionApi.endSession(sessionId);
      
      // Add summary message
      const summaryMessage: ConversationMessage = {
        id: `msg-${Date.now()}`,
        speaker: 'tutor',
        text: `會話結束！\n\n📊 學習總結：\n• 概念覆蓋率：${Math.round(summary.concept_coverage * 100)}%\n• 使用提示：${summary.hints_used.length} 次\n• 對話輪數：${summary.total_turns} 輪\n• 總時長：${Math.round(summary.duration / 60)} 分鐘\n\n繼續加油！`,
        timestamp: new Date(),
        responseType: 'CONSOLIDATE',
      };
      setMessages((prev) => [...prev, summaryMessage]);

      // Wait a moment before navigating away
      setTimeout(() => {
        onEndSession();
      }, 3000);
    } catch (err) {
      console.error('Failed to end session:', err);
      onEndSession();
    }
  }, [sessionId, onEndSession]);

  const handleRequestHint = useCallback(async () => {
    if (!sessionId) return;

    // Send hint request
    await handleTranscription('給我提示', null);
  }, [sessionId, handleTranscription]);

  if (isInitializing) {
    return (
      <div className="session-page loading">
        <div className="loading-spinner" />
        <p>正在準備會話...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="session-page error">
        <p className="error-message">{error}</p>
        <button onClick={onEndSession}>返回</button>
      </div>
    );
  }

  return (
    <div className="session-page">
      <header className="session-header">
        <div className="header-left">
          <button className="btn-back" onClick={handleEndSession}>
            ← 結束講題
          </button>
        </div>
        <div className="header-center">
          <h1>口語講題</h1>
        </div>
        <div className="header-right">
          <button className="btn-hint" onClick={handleRequestHint} disabled={isLoading}>
            💡 請求提示
          </button>
        </div>
      </header>

      <div className="session-layout">
        <aside className="session-sidebar">
          {question && (
            <div className="question-card">
              <h3>題目</h3>
              <p className="question-content">{question.content}</p>
              <div className="question-meta">
                <span>{question.subject}</span>
                <span>•</span>
                <span>{question.unit}</span>
              </div>
            </div>
          )}

          <FSMStateIndicator
            state={(sessionState?.fsm_state as FSMState) || 'LISTENING'}
            conceptCoverage={sessionState?.concept_coverage || 0}
            hintsUsed={sessionState?.hints_used || 0}
          />
        </aside>

        <main className="session-main">
          <ConversationPanel messages={messages} isLoading={isLoading} />

          <div className="input-section">
            <VoiceInput
              onTranscription={handleTranscription}
              disabled={isLoading}
              placeholder="講解你的解題思路，或輸入文字..."
            />
          </div>
        </main>
      </div>
    </div>
  );
}
