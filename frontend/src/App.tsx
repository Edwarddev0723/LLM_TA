/**
 * Main App component for AI Math Tutor
 */

import { useState } from 'react';
import { PracticePage } from './pages/PracticePage';
import { SessionPage } from './pages/SessionPage';
import { ErrorBookPage } from './pages/ErrorBookPage';
import { DashboardPage } from './pages/DashboardPage';
import './App.css';

// Navigation tabs
type Tab = 'practice' | 'session' | 'errors' | 'dashboard';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('practice');
  const [currentSessionQuestionId, setCurrentSessionQuestionId] = useState<string | null>(null);
  
  // Mock student ID (in production, this would come from authentication)
  const studentId = 'student-001';

  const handleStartSession = (questionId: string) => {
    setCurrentSessionQuestionId(questionId);
    setActiveTab('session');
  };

  const handleEndSession = () => {
    setCurrentSessionQuestionId(null);
    setActiveTab('practice');
  };

  return (
    <div className="app">
      <nav className="app-nav">
        <div className="nav-brand">
          <span className="brand-icon">📐</span>
          <span className="brand-text">AI 數學助教</span>
        </div>
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'practice' ? 'active' : ''}`}
            onClick={() => setActiveTab('practice')}
          >
            題目練習
          </button>
          <button
            className={`nav-tab ${activeTab === 'session' ? 'active' : ''}`}
            onClick={() => setActiveTab('session')}
            disabled={!currentSessionQuestionId}
          >
            口語講題
          </button>
          <button
            className={`nav-tab ${activeTab === 'errors' ? 'active' : ''}`}
            onClick={() => setActiveTab('errors')}
          >
            錯題本
          </button>
          <button
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            儀表板
          </button>
        </div>
        <div className="nav-user">
          <span className="user-avatar">👤</span>
          <span className="user-name">學生</span>
        </div>
      </nav>

      <main className="app-main">
        {activeTab === 'practice' && (
          <PracticePage
            studentId={studentId}
            onStartSession={handleStartSession}
          />
        )}
        {activeTab === 'session' && currentSessionQuestionId && (
          <SessionPage
            questionId={currentSessionQuestionId}
            studentId={studentId}
            onEndSession={handleEndSession}
          />
        )}
        {activeTab === 'errors' && (
          <ErrorBookPage
            studentId={studentId}
            onStartReview={handleStartSession}
          />
        )}
        {activeTab === 'dashboard' && (
          <DashboardPage
            studentId={studentId}
          />
        )}
      </main>
    </div>
  );
}

export default App;
