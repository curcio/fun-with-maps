import { render, screen } from '@testing-library/react';
import App from './App';
import { vi } from 'vitest';

vi.mock('./Game', () => ({ default: () => <div>Game</div> }));

test('renders header', () => {
  render(<App />);
  expect(screen.getByText(/guess the country/i)).toBeInTheDocument();
});
