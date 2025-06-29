export default function HintList({ hints }) {
  if (!hints.length) return null;
  return (
    <ul data-testid="hint-list">
      {hints.map((hint, idx) => (
        <li key={idx}>{hint}</li>
      ))}
    </ul>
  );
}
