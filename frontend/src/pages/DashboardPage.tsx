/**
 * Dashboard Page - Learning metrics visualization
 * Requirements: 10.1, 10.2, 10.3, 10.4
 */

import { useState, useEffect } from 'react';
import { dashboardApi } from '../api';
import type {
  MetricsResponse,
  HeatmapResponse,
  DashboardOverviewResponse,
  KnowledgeNodeMastery,
  SessionDetailResponse,
} from '../types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import './DashboardPage.css';

interface DashboardPageProps {
  studentId: string;
}

export function DashboardPage({ studentId }: DashboardPageProps) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [overview, setOverview] = useState<DashboardOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeNodeMastery | null>(null);
  const [selectedSession, setSelectedSession] = useState<SessionDetailResponse | null>(null);
  const [loadingSession, setLoadingSession] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, [studentId]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsData, heatmapData, overviewData] = await Promise.all([
        dashboardApi.getMetrics(studentId, 20),
        dashboardApi.getHeatmap(studentId),
        dashboardApi.getOverview(studentId),
      ]);
      setMetrics(metricsData);
      setHeatmap(heatmapData);
      setOverview(overviewData);
    } catch (err) {
      setError(err instanceof Error ? err.message : '載入儀表板資料失敗');
    } finally {
      setLoading(false);
    }
  };

  const loadSessionDetail = async (sessionId: string) => {
    setLoadingSession(true);
    try {
      const detail = await dashboardApi.getSessionDetail(sessionId);
      setSelectedSession(detail);
    } catch (err) {
      console.error('Failed to load session detail:', err);
    } finally {
      setLoadingSession(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)} 秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes} 分 ${remainingSeconds.toFixed(0)} 秒`;
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>載入儀表板資料中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="error-state">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={loadDashboardData}>重試</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <h1>學習儀表板</h1>
        <button className="refresh-btn" onClick={loadDashboardData}>
          🔄 重新整理
        </button>
      </header>

      {/* Overview Section */}
      {overview && (
        <section className="overview-section">
          <h2>學習概覽</h2>
          <div className="overview-cards">
            <div className="overview-card">
              <span className="card-icon">📚</span>
              <div className="card-content">
                <span className="card-value">{overview.total_sessions}</span>
                <span className="card-label">總學習次數</span>
              </div>
            </div>
            <div className="overview-card">
              <span className="card-icon">✅</span>
              <div className="card-content">
                <span className="card-value">{overview.completed_sessions}</span>
                <span className="card-label">完成次數</span>
              </div>
            </div>
            <div className="overview-card">
              <span className="card-icon">📊</span>
              <div className="card-content">
                <span className="card-value">{(overview.average_coverage * 100).toFixed(1)}%</span>
                <span className="card-label">平均概念覆蓋率</span>
              </div>
            </div>
            <div className="overview-card">
              <span className="card-icon">⏱️</span>
              <div className="card-content">
                <span className="card-value">{overview.total_duration_minutes.toFixed(1)}</span>
                <span className="card-label">總學習時長 (分鐘)</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Metrics Charts Section */}
      {metrics && metrics.metrics_history.length > 0 && (
        <section className="metrics-section">
          <h2>學習指標趨勢</h2>
          
          {/* WPM Trend Chart */}
          <div className="chart-container">
            <h3>語速趨勢 (WPM)</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={metrics.metrics_history.map((m, i) => ({
                    ...m,
                    index: i + 1,
                    date: new Date(m.timestamp).toLocaleDateString('zh-TW'),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip
                    formatter={(value) => [`${Number(value).toFixed(1)} 字/分`, 'WPM']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="wpm"
                    stroke="#4CAF50"
                    strokeWidth={2}
                    dot={{ fill: '#4CAF50' }}
                    name="語速 (WPM)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-summary">
              <span>平均語速: <strong>{metrics.average_wpm.toFixed(1)}</strong> 字/分</span>
            </div>
          </div>

          {/* Pause Rate Distribution */}
          <div className="chart-container">
            <h3>停頓比例分佈</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={metrics.metrics_history.map((m, i) => ({
                    ...m,
                    index: i + 1,
                    date: new Date(m.timestamp).toLocaleDateString('zh-TW'),
                    pause_percent: m.pause_rate * 100,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis unit="%" />
                  <Tooltip
                    formatter={(value) => [`${Number(value).toFixed(1)}%`, '停頓比例']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Legend />
                  <Bar
                    dataKey="pause_percent"
                    fill="#FF9800"
                    name="停頓比例 (%)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-summary">
              <span>平均停頓比例: <strong>{(metrics.average_pause_rate * 100).toFixed(1)}%</strong></span>
            </div>
          </div>

          {/* Hint Dependency Statistics */}
          <div className="chart-container">
            <h3>提示依賴度統計</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={metrics.metrics_history.map((m, i) => ({
                    ...m,
                    index: i + 1,
                    date: new Date(m.timestamp).toLocaleDateString('zh-TW'),
                    hint_percent: m.hint_dependency * 100,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip
                    formatter={(value) => [`${Number(value).toFixed(1)}%`, '獨立度']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="hint_percent"
                    stroke="#2196F3"
                    strokeWidth={2}
                    dot={{ fill: '#2196F3' }}
                    name="獨立度 (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-summary">
              <span>平均獨立度: <strong>{(metrics.average_hint_dependency * 100).toFixed(1)}%</strong></span>
              <span className="hint-text">(越高表示越少依賴提示)</span>
            </div>
          </div>
        </section>
      )}

      {/* Heatmap Section */}
      {heatmap && heatmap.nodes.length > 0 && (
        <section className="heatmap-section">
          <h2>弱點熱力圖</h2>
          <div className="heatmap-legend">
            <span className="legend-item">
              <span className="legend-color green"></span> 掌握良好 (≥80%)
            </span>
            <span className="legend-item">
              <span className="legend-color yellow"></span> 需加強 (50-79%)
            </span>
            <span className="legend-item">
              <span className="legend-color red"></span> 弱點 (&lt;50%)
            </span>
          </div>
          <div className="heatmap-grid">
            {heatmap.nodes.map((node) => (
              <div
                key={node.node_id}
                className={`heatmap-node ${node.mastery_level}`}
                onClick={() => setSelectedNode(selectedNode?.node_id === node.node_id ? null : node)}
              >
                <span className="node-name">{node.node_name}</span>
                <span className="node-score">{(node.mastery_score * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>

          {/* Node Detail Panel */}
          {selectedNode && (
            <div className="node-detail-panel">
              <h3>{selectedNode.node_name}</h3>
              <button className="close-btn" onClick={() => setSelectedNode(null)}>×</button>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">科目</span>
                  <span className="detail-value">{selectedNode.subject}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">單元</span>
                  <span className="detail-value">{selectedNode.unit}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">掌握度</span>
                  <span className={`detail-value ${selectedNode.mastery_level}`}>
                    {(selectedNode.mastery_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">錯誤次數</span>
                  <span className="detail-value">{selectedNode.error_count}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">總嘗試次數</span>
                  <span className="detail-value">{selectedNode.total_attempts}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">概念覆蓋率</span>
                  <span className="detail-value">{(selectedNode.concept_coverage * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Mastery Distribution Pie Chart */}
          <div className="chart-container">
            <h3>掌握度分佈</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: '掌握良好', value: heatmap.strong_areas.length, color: '#4CAF50' },
                      { name: '需加強', value: heatmap.nodes.filter(n => n.mastery_level === 'yellow').length, color: '#FF9800' },
                      { name: '弱點', value: heatmap.weak_areas.length, color: '#f44336' },
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                    outerRadius={100}
                    dataKey="value"
                  >
                    {[
                      { name: '掌握良好', value: heatmap.strong_areas.length, color: '#4CAF50' },
                      { name: '需加強', value: heatmap.nodes.filter(n => n.mastery_level === 'yellow').length, color: '#FF9800' },
                      { name: '弱點', value: heatmap.weak_areas.length, color: '#f44336' },
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      )}

      {/* Focus Duration Section */}
      {metrics && metrics.metrics_history.length > 0 && (
        <section className="focus-section">
          <h2>專注時長分析</h2>
          <div className="chart-container">
            <h3>專注時長趨勢</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={metrics.metrics_history.map((m, i) => ({
                    ...m,
                    index: i + 1,
                    date: new Date(m.timestamp).toLocaleDateString('zh-TW'),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis unit="分" />
                  <Tooltip
                    formatter={(value) => [`${Number(value).toFixed(1)} 分鐘`, '專注時長']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Legend />
                  <Bar
                    dataKey="focus_duration"
                    fill="#9C27B0"
                    name="專注時長 (分鐘)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-summary">
              <span>總專注時長: <strong>{metrics.total_focus_duration.toFixed(1)}</strong> 分鐘</span>
            </div>
          </div>
        </section>
      )}

      {/* Recent Sessions */}
      {overview && overview.recent_sessions.length > 0 && (
        <section className="recent-section">
          <h2>最近學習紀錄</h2>
          <div className="sessions-list">
            {overview.recent_sessions.map((session) => (
              <div
                key={session.session_id}
                className={`session-item ${selectedSession?.session_id === session.session_id ? 'selected' : ''}`}
                onClick={() => loadSessionDetail(session.session_id)}
              >
                <div className="session-info">
                  <span className="session-date">
                    {new Date(session.start_time).toLocaleString('zh-TW')}
                  </span>
                  <span className="session-question">題目: {session.question_id}</span>
                </div>
                <div className="session-stats">
                  <span className="session-coverage">
                    覆蓋率: {(session.concept_coverage * 100).toFixed(0)}%
                  </span>
                  <span className={`session-state ${session.final_state?.toLowerCase()}`}>
                    {session.final_state || '進行中'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Session Detail Panel */}
          {loadingSession && (
            <div className="session-detail-loading">
              <div className="loading-spinner small"></div>
              <span>載入詳情中...</span>
            </div>
          )}
          {selectedSession && !loadingSession && (
            <div className="session-detail-panel">
              <div className="detail-header">
                <h3>學習歷程詳情</h3>
                <button className="close-btn" onClick={() => setSelectedSession(null)}>×</button>
              </div>
              
              <div className="detail-metrics">
                <div className="metric-item">
                  <span className="metric-label">專注時長</span>
                  <span className="metric-value">
                    {selectedSession.focus_duration ? formatDuration(selectedSession.focus_duration * 60) : '無資料'}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">語速 (WPM)</span>
                  <span className="metric-value">
                    {selectedSession.wpm?.toFixed(1) ?? '無資料'}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">停頓比例</span>
                  <span className="metric-value">
                    {selectedSession.pause_rate ? `${(selectedSession.pause_rate * 100).toFixed(1)}%` : '無資料'}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">獨立度</span>
                  <span className="metric-value">
                    {selectedSession.hint_dependency ? `${(selectedSession.hint_dependency * 100).toFixed(1)}%` : '無資料'}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">提示使用次數</span>
                  <span className="metric-value">{selectedSession.hint_count}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">概念覆蓋率</span>
                  <span className="metric-value">
                    {(selectedSession.concept_coverage * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Distraction/Pause Periods */}
              {selectedSession.pauses.length > 0 && (
                <div className="pause-section">
                  <h4>分心時段分析</h4>
                  <div className="pause-summary">
                    <span>總停頓時間: <strong>{formatDuration(selectedSession.total_pause_duration)}</strong></span>
                    <span>停頓次數: <strong>{selectedSession.pauses.length}</strong></span>
                  </div>
                  <div className="pause-timeline">
                    {selectedSession.pauses.map((pause, index) => (
                      <div key={index} className="pause-item">
                        <span className="pause-time">
                          {formatDuration(pause.start_time)} - {formatDuration(pause.end_time)}
                        </span>
                        <span className="pause-duration">
                          停頓 {formatDuration(pause.duration)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedSession.pauses.length === 0 && (
                <div className="no-pauses">
                  <span className="success-icon">✓</span>
                  <span>此次學習沒有明顯的分心時段，表現良好！</span>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Empty State */}
      {(!metrics || metrics.metrics_history.length === 0) && 
       (!heatmap || heatmap.nodes.length === 0) && (
        <div className="empty-state">
          <span className="empty-icon">📊</span>
          <h3>尚無學習資料</h3>
          <p>開始練習題目後，這裡會顯示您的學習指標和進度分析。</p>
        </div>
      )}
    </div>
  );
}
