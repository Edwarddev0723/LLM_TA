/**
 * ConversationPanel component for displaying dialog history
 * Requirements: 6.1 - 建立對話框顯示區域
 */

import { useRef, useEffect } from 'react';
import type { ResponseType, HintLevel } from '../types';
import './ConversationPanel.css';

export interface ConversationMessage {
  id: string;
  speaker: 'student' | 'tutor';
  text: string;
  timestamp: Date;
  responseType?: ResponseType;
  hintLevel?: HintLevel;
}

interface ConversationPanelProps {
  messages: ConversationMessage[];
  isLoading?: boolean;
}

const RESPONSE_TYPE_LABELS: Record<ResponseType, string> = {
  PROBE: '追問',
  HINT: '提示',
  REPAIR: '修正',
  CONSOLIDATE: '總結',
  ACKNOWLEDGE: '確認',
};

const HINT_LEVEL_LABELS: Record<HintLevel, string> = {
  1: 'Level 1 - 方向性暗示',
  2: 'Level 2 - 關鍵步驟',
  3: 'Level 3 - 解法框架',
};

export function ConversationPanel({ messages, isLoading }: ConversationPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="conversation-panel">
      <div className="messages-container">
        {messages.length === 0 && !isLoading && (
          <div className="empty-state">
            <p>開始講解你的解題思路吧！</p>
            <p className="hint">AI 助教會根據你的講解提供引導和回饋</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.speaker === 'student' ? 'student' : 'tutor'}`}
          >
            <div className="message-header">
              <span className="speaker-label">
                {message.speaker === 'student' ? '你' : 'AI 助教'}
              </span>
              <span className="message-time">{formatTime(message.timestamp)}</span>
            </div>

            {message.responseType && (
              <div className="response-type-badge">
                {RESPONSE_TYPE_LABELS[message.responseType]}
                {message.hintLevel && (
                  <span className="hint-level">
                    {HINT_LEVEL_LABELS[message.hintLevel]}
                  </span>
                )}
              </div>
            )}

            <div className="message-content">
              <p>{message.text}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message tutor loading">
            <div className="message-header">
              <span className="speaker-label">AI 助教</span>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
