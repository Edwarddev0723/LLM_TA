import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the AI Math Tutor heading', () => {
    render(<App />);
    expect(screen.getByText('AI 數學助教')).toBeInTheDocument();
  });

  it('renders the navigation tabs', () => {
    render(<App />);
    // Use getAllByRole to find buttons with specific text
    const navButtons = screen.getAllByRole('button');
    const tabTexts = navButtons.map(btn => btn.textContent);
    expect(tabTexts).toContain('題目練習');
    expect(tabTexts).toContain('口語講題');
    expect(tabTexts).toContain('錯題本');
  });

  it('renders the practice page by default', () => {
    render(<App />);
    // The h1 heading should be present
    expect(screen.getByRole('heading', { level: 1, name: '題目練習' })).toBeInTheDocument();
  });
});
