/**
 * QuestionFilter component for filtering questions by subject, unit, and difficulty
 * Requirements: 1.1 - 顯示科目、單元、難度的篩選介面
 */

import { useState } from 'react';
import type { QuestionCriteria, DifficultyLevel } from '../types';
import './QuestionFilter.css';

interface QuestionFilterProps {
  onFilter: (criteria: QuestionCriteria) => void;
  isLoading?: boolean;
}

// Available subjects and units matching database data
const SUBJECTS = ['數學'];
const UNITS: Record<string, string[]> = {
  數學: ['代數', '幾何', '統計'],
};

const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  1: '簡單',
  2: '中等',
  3: '困難',
};

export function QuestionFilter({ onFilter, isLoading }: QuestionFilterProps) {
  const [subject, setSubject] = useState<string>('');
  const [unit, setUnit] = useState<string>('');
  const [difficulty, setDifficulty] = useState<DifficultyLevel | ''>('');

  const availableUnits = subject ? UNITS[subject] || [] : [];

  const handleSubjectChange = (newSubject: string) => {
    setSubject(newSubject);
    setUnit(''); // Reset unit when subject changes
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const criteria: QuestionCriteria = {};
    if (subject) criteria.subject = subject;
    if (unit) criteria.unit = unit;
    if (difficulty) criteria.difficulty = difficulty as DifficultyLevel;
    onFilter(criteria);
  };

  const handleReset = () => {
    setSubject('');
    setUnit('');
    setDifficulty('');
    onFilter({});
  };

  return (
    <form className="question-filter" onSubmit={handleSubmit}>
      <h3 className="filter-title">題目篩選</h3>
      
      <div className="filter-group">
        <label htmlFor="subject">科目</label>
        <select
          id="subject"
          value={subject}
          onChange={(e) => handleSubjectChange(e.target.value)}
          disabled={isLoading}
        >
          <option value="">全部科目</option>
          {SUBJECTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="unit">單元</label>
        <select
          id="unit"
          value={unit}
          onChange={(e) => setUnit(e.target.value)}
          disabled={isLoading || !subject}
        >
          <option value="">全部單元</option>
          {availableUnits.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="difficulty">難度</label>
        <select
          id="difficulty"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value as DifficultyLevel | '')}
          disabled={isLoading}
        >
          <option value="">全部難度</option>
          {([1, 2, 3] as DifficultyLevel[]).map((d) => (
            <option key={d} value={d}>
              {DIFFICULTY_LABELS[d]}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-actions">
        <button type="submit" className="btn-primary" disabled={isLoading}>
          {isLoading ? '搜尋中...' : '搜尋題目'}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={handleReset}
          disabled={isLoading}
        >
          重置
        </button>
      </div>
    </form>
  );
}
