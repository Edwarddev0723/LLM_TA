/**
 * ErrorFilter component for filtering error records
 * Requirements: 4.3 - 錯題篩選功能
 */

import { useState } from 'react';
import type { ErrorCriteria, ErrorType } from '../types';
import './ErrorFilter.css';

interface ErrorFilterProps {
  onFilter: (criteria: ErrorCriteria) => void;
  isLoading?: boolean;
}

const ERROR_TYPES: { value: ErrorType; label: string }[] = [
  { value: 'CALCULATION', label: '計算錯誤' },
  { value: 'CONCEPT', label: '觀念錯誤' },
  { value: 'CARELESS', label: '粗心錯誤' },
];

const UNITS = ['整數運算', '分數運算', '一元一次方程式', '二元一次方程式', '三角形', '四邊形'];

export function ErrorFilter({ onFilter, isLoading }: ErrorFilterProps) {
  const [errorType, setErrorType] = useState<ErrorType | ''>('');
  const [unit, setUnit] = useState<string>('');
  const [repaired, setRepaired] = useState<boolean | ''>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const criteria: ErrorCriteria = {};
    if (errorType) criteria.error_type = errorType;
    if (unit) criteria.unit = unit;
    if (repaired !== '') criteria.repaired = repaired;
    onFilter(criteria);
  };

  const handleReset = () => {
    setErrorType('');
    setUnit('');
    setRepaired('');
    onFilter({});
  };

  return (
    <form className="error-filter" onSubmit={handleSubmit}>
      <h3 className="filter-title">錯題篩選</h3>

      <div className="filter-group">
        <label htmlFor="error-type">錯誤類型</label>
        <select
          id="error-type"
          value={errorType}
          onChange={(e) => setErrorType(e.target.value as ErrorType | '')}
          disabled={isLoading}
        >
          <option value="">全部類型</option>
          {ERROR_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
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
          disabled={isLoading}
        >
          <option value="">全部單元</option>
          {UNITS.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="repaired">修復狀態</label>
        <select
          id="repaired"
          value={repaired === '' ? '' : repaired.toString()}
          onChange={(e) => {
            const val = e.target.value;
            setRepaired(val === '' ? '' : val === 'true');
          }}
          disabled={isLoading}
        >
          <option value="">全部狀態</option>
          <option value="false">未修復</option>
          <option value="true">已修復</option>
        </select>
      </div>

      <div className="filter-actions">
        <button type="submit" className="btn-primary" disabled={isLoading}>
          {isLoading ? '搜尋中...' : '篩選'}
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
