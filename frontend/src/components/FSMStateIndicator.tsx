/**
 * FSMStateIndicator component for displaying current FSM state
 * Requirements: 6.1, 6.6 - 顯示 FSM 狀態指示
 */

import type { FSMState } from '../types';
import './FSMStateIndicator.css';

interface FSMStateIndicatorProps {
  state: FSMState;
  conceptCoverage: number;
  hintsUsed: number;
}

const STATE_INFO: Record<FSMState, { label: string; description: string; color: string }> = {
  IDLE: {
    label: '待機',
    description: '等待開始',
    color: 'state-idle',
  },
  LISTENING: {
    label: '聆聽中',
    description: '正在聆聽你的講解',
    color: 'state-listening',
  },
  ANALYZING: {
    label: '分析中',
    description: '正在分析你的回答',
    color: 'state-analyzing',
  },
  PROBING: {
    label: '追問',
    description: '需要更多說明',
    color: 'state-probing',
  },
  HINTING: {
    label: '提示',
    description: '提供引導提示',
    color: 'state-hinting',
  },
  REPAIR: {
    label: '修正',
    description: '發現需要修正的地方',
    color: 'state-repair',
  },
  CONSOLIDATING: {
    label: '總結',
    description: '整理學習成果',
    color: 'state-consolidating',
  },
};

export function FSMStateIndicator({
  state,
  conceptCoverage,
  hintsUsed,
}: FSMStateIndicatorProps) {
  const stateInfo = STATE_INFO[state];
  const coveragePercent = Math.round(conceptCoverage * 100);

  return (
    <div className="fsm-state-indicator">
      <div className="state-section">
        <div className={`state-badge ${stateInfo.color}`}>
          <span className="state-dot" />
          <span className="state-label">{stateInfo.label}</span>
        </div>
        <p className="state-description">{stateInfo.description}</p>
      </div>

      <div className="metrics-section">
        <div className="metric">
          <span className="metric-label">概念覆蓋率</span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${coveragePercent}%` }}
            />
          </div>
          <span className="metric-value">{coveragePercent}%</span>
        </div>

        <div className="metric">
          <span className="metric-label">已使用提示</span>
          <span className="metric-value hints-count">{hintsUsed}</span>
        </div>
      </div>
    </div>
  );
}
