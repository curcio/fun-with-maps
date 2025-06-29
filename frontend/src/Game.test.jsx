import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import Game from './Game';

function mockApi(data) {
  global.fetch = vi.fn(() =>
    Promise.resolve({ json: () => Promise.resolve(data) })
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

test('fetches hints on mount', async () => {
  mockApi({ country: 'France', hints: ['a', 'b'] });
  render(<Game />);
  const list = await screen.findByTestId('hint-list');
  expect(list.children).toHaveLength(2);
});

test('shows celebration after correct guess', async () => {
  mockApi({ country: 'France', hints: [] });
  render(<Game />);
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());

  const input = screen.getByPlaceholderText(/your guess/i);
  fireEvent.change(input, { target: { value: 'France' } });
  fireEvent.click(screen.getByText('Guess'));

  expect(screen.getByTestId('celebration')).toBeInTheDocument();
});
