export default function GuessInput({ value, onChange, onSubmit }) {
  return (
    <div>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Your guess"
      />
      <button onClick={onSubmit}>Guess</button>
    </div>
  );
}
