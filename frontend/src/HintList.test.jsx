import { render, screen } from '@testing-library/react';
import HintList from './HintList';

test('renders hints', () => {
  const hints = ['a', 'b'];
  render(<HintList hints={hints} />);
  const list = screen.getByTestId('hint-list');
  expect(list.children).toHaveLength(2);
});
