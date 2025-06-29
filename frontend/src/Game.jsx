import { useState, useEffect } from 'react';
import HintList from './HintList';
import GuessInput from './GuessInput';
import Celebration from './Celebration';

export default function Game() {
  const [hints, setHints] = useState([]);
  const [country, setCountry] = useState('');
  const [guess, setGuess] = useState('');
  const [won, setWon] = useState(false);

  useEffect(() => {
    fetch('/new-game')
      .then((r) => r.json())
      .then((data) => {
        setCountry(data.country);
        setHints(data.hints);
      });
  }, []);

  const handleGuess = () => {
    if (guess.trim().toLowerCase() === country.toLowerCase()) {
      setWon(true);
    }
  };

  return (
    <div>
      {won && <Celebration />}
      <GuessInput value={guess} onChange={setGuess} onSubmit={handleGuess} />
      {!won && <HintList hints={hints} />}
    </div>
  );
}
