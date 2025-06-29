// Game state management
class CountryGuessingGame {
    constructor() {
        // Static fallback list of countries for validation
        this.staticValidCountries = [
            'iran', 'persia', 'united states', 'usa', 'america',
            'france', 'germany', 'japan', 'china', 'brazil',
            'canada', 'australia', 'india', 'russia', 'italy'
        ];

        const data = window.GAME_DATA || {};
        console.log('Game data received:', data);

        // Normalize country names to lowercase for comparison
        this.validCountries = data.valid_countries ?
            data.valid_countries.map(country => country.toLowerCase()) :
            this.staticValidCountries;

        this.correctAnswer = (data.country || 'iran').toLowerCase();

        // Set up alternative answers for common country name variations
        this.alternativeAnswers = this.getAlternativeAnswers(this.correctAnswer);

        console.log('Correct answer:', this.correctAnswer);
        console.log('Alternative answers:', this.alternativeAnswers);
        console.log('Valid countries:', this.validCountries.slice(0, 10), '...');

        this.feedbackEl = null;

        // Game state
        this.wrongAttempts = 0;
        this.maxHints = 4;
        this.maxErrors = 4;
        this.gameWon = false;
        this.gameOver = false;

        // Initialize the game
        this.init();
    }

    getAlternativeAnswers(correctAnswer) {
        // Common alternative names for countries
        const alternatives = {
            'united states': ['usa', 'america', 'us', 'united states of america'],
            'united kingdom': ['uk', 'britain', 'great britain', 'england'],
            'russia': ['russian federation'],
            'iran': ['persia'],
            'south korea': ['korea', 'republic of korea'],
            'north korea': ['korea', 'democratic people\'s republic of korea'],
            'china': ['people\'s republic of china', 'prc'],
            'congo': ['democratic republic of congo', 'drc'],
            'myanmar': ['burma'],
            'czech republic': ['czechia'],
            'macedonia': ['north macedonia'],
            'swaziland': ['eswatini'],
            'ivory coast': ['cote d\'ivoire'],
        };

        return alternatives[correctAnswer] || [];
    }

    init() {
        this.bindEvents();
        this.setupGame();
    }

    bindEvents() {
        const submitBtn = document.getElementById('submit-btn');
        const countryInput = document.getElementById('country-input');
        const celebration = document.getElementById('celebration');
        const restartBtn = document.getElementById('restart-btn');

        // Submit button click
        submitBtn.addEventListener('click', () => this.handleSubmit());

        // Enter key press
        countryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSubmit();
            }
        });

        // Close celebration on click
        celebration.addEventListener('click', () => {
            this.hideCelebration();
        });

        // Restart button click
        restartBtn.addEventListener('click', () => {
            this.resetGame();
        });
    }

    setupGame() {
        // Set up the final game with all features enabled
        document.getElementById('game-interface').style.display = 'block';

        // Feedback element
        this.feedbackEl = document.getElementById('feedback');
        if (this.feedbackEl) {
            this.feedbackEl.style.display = 'none';
        }

        // Initialize image container as hidden
        const imageContainer = document.querySelector('.image-container');
        imageContainer.classList.add('hidden');
        imageContainer.classList.remove('show');

        document.getElementById('hints-section').style.display = 'block';

        // Initialize hints - first one revealed, others unrevealed
        for (let i = 1; i <= this.maxHints; i++) {
            const hint = document.getElementById(`hint-${i}`);
            if (hint) {
                if (i === 1) {
                    hint.classList.add('revealed');
                } else {
                    hint.classList.remove('revealed');
                }
            }
        }
    }

    handleSubmit() {
        if (this.gameWon || this.gameOver) return;

        const input = document.getElementById('country-input');
        const userAnswer = input.value.trim().toLowerCase();

        this.hideFeedback();

        if (!userAnswer) {
            return; // Just return, no feedback needed
        }

        console.log('User answer:', userAnswer);

        // Check if answer is correct
        if (this.isCorrectAnswer(userAnswer)) {
            console.log('Correct answer detected!');
            this.handleCorrectAnswer();
        } else {
            console.log('Wrong answer, checking if valid country...');
            this.handleWrongAnswer(userAnswer);
        }

        // Clear input
        input.value = '';
    }

    isCorrectAnswer(answer) {
        const correctAnswers = [this.correctAnswer, ...this.alternativeAnswers];
        const isCorrect = correctAnswers.includes(answer);
        console.log('Checking answer:', answer, 'against:', correctAnswers, 'Result:', isCorrect);
        return isCorrect;
    }

    handleCorrectAnswer() {
        this.gameWon = true;

        this.showFeedback('Correct!', false);

        // Show congratulations message
        document.getElementById('congratulations').style.display = 'block';

        // Smoothly hide the question mark and show the map
        const questionMark = document.querySelector('.question-mark');
        questionMark.classList.add('fade-out');

        setTimeout(() => {
            questionMark.style.display = 'none';
            const imageContainer = document.querySelector('.image-container');
            imageContainer.classList.remove('hidden');
            imageContainer.classList.add('show');
        }, 500);

        // Show celebration animation
        setTimeout(() => {
            this.showCelebration();
        }, 1500);

        // Disable input
        document.getElementById('country-input').disabled = true;
        document.getElementById('submit-btn').disabled = true;
    }

    handleWrongAnswer(answer) {
        console.log('Processing wrong answer:', answer);

        this.wrongAttempts++;

        // Check if answer is in valid countries list
        if (!this.validCountries.includes(answer)) {
            // Invalid country, don't count as wrong attempt, show feedback
            this.wrongAttempts--;
            console.log('Country not recognized:', answer);
            this.showFeedback('Country not recognized.', true);
            return;
        }

        console.log('Valid country but wrong answer. Wrong attempts:', this.wrongAttempts);

        // Check for game over after 4 errors
        if (this.wrongAttempts >= this.maxErrors) {
            console.log('Game over - too many wrong attempts');
            this.handleGameOver();
            return;
        }

        // Show next hint for wrong but valid answer
        this.showNextHint();
        this.showFeedback('Try again!', true);
    }

    showNextHint() {
        // Reveal the next hint based on number of wrong attempts
        // wrongAttempts = 1 -> reveal hint-2, wrongAttempts = 2 -> reveal hint-3, etc.
        const nextHintIndex = this.wrongAttempts + 1;
        console.log('Revealing hint', nextHintIndex, 'after', this.wrongAttempts, 'wrong attempts');

        if (nextHintIndex <= this.maxHints) {
            const hintElement = document.getElementById(`hint-${nextHintIndex}`);
            if (hintElement) {
                hintElement.classList.add('revealed');
                console.log('Hint', nextHintIndex, 'revealed successfully');
            } else {
                console.log('Hint element not found:', `hint-${nextHintIndex}`);
            }
        } else {
            console.log('No more hints to reveal');
        }
    }

    handleGameOver() {
        this.gameOver = true;

        // Show game over message
        document.getElementById('game-over').style.display = 'block';

        // Disable input
        document.getElementById('country-input').disabled = true;
        document.getElementById('submit-btn').disabled = true;
    }

    showCelebration() {
        const celebration = document.getElementById('celebration');
        celebration.classList.add('active');

        // Hide after 5 seconds
        setTimeout(() => {
            this.hideCelebration();
        }, 5000);
    }

    hideCelebration() {
        const celebration = document.getElementById('celebration');
        celebration.classList.remove('active');
    }

    showFeedback(message, isError) {
        if (!this.feedbackEl) {
            this.feedbackEl = document.getElementById('feedback');
        }
        if (!this.feedbackEl) return;
        this.feedbackEl.textContent = message;
        this.feedbackEl.classList.remove('success', 'error');
        this.feedbackEl.classList.add(isError ? 'error' : 'success');
        this.feedbackEl.style.display = 'block';
    }

    hideFeedback() {
        if (this.feedbackEl) {
            this.feedbackEl.style.display = 'none';
        }
    }

    async resetGame() {
        console.log('Resetting game and getting new country...');

        try {
            // Fetch new game data from backend
            const response = await fetch('/api/new-game');
            const newGameData = await response.json();

            console.log('New game data:', newGameData);

                        // Update game state with new country
            this.validCountries = newGameData.valid_countries ?
                newGameData.valid_countries.map(country => country.toLowerCase()) :
                this.staticValidCountries;
            this.correctAnswer = (newGameData.country || 'iran').toLowerCase();
            this.alternativeAnswers = this.getAlternativeAnswers(this.correctAnswer);

            console.log('New correct answer:', this.correctAnswer);
            console.log('New alternative answers:', this.alternativeAnswers);
            console.log('New image path:', newGameData.image_path);

            // Update hints in the DOM
            if (newGameData.hints && newGameData.hints.length > 0) {
                for (let i = 0; i < this.maxHints; i++) {
                    const hintElement = document.getElementById(`hint-${i + 1}`);
                    if (hintElement) {
                        if (i < newGameData.hints.length) {
                            hintElement.textContent = newGameData.hints[i];
                        } else {
                            hintElement.textContent = 'No more hints available';
                        }
                    }
                }
            }

            // Update the image if available
            const mainImage = document.getElementById('main-image');
            if (mainImage && newGameData.image_path) {
                mainImage.src = newGameData.image_path;
                mainImage.alt = newGameData.country;
                mainImage.style.display = 'block';
                console.log('Updated image to:', newGameData.image_path);
            } else if (mainImage) {
                // Clear image if no path provided
                mainImage.src = '';
                mainImage.alt = '';
                mainImage.style.display = 'none';
                console.log('No image available for country:', newGameData.country);
            }

        } catch (error) {
            console.error('Error fetching new game data:', error);
            // Continue with reset even if fetch fails
        }

        // Reset game state
        this.wrongAttempts = 0;
        this.gameWon = false;
        this.gameOver = false;

        // Reset UI
        document.getElementById('country-input').disabled = false;
        document.getElementById('submit-btn').disabled = false;
        document.getElementById('country-input').value = '';

        // Hide messages
        document.getElementById('congratulations').style.display = 'none';
        document.getElementById('game-over').style.display = 'none';

        // Show question mark again with smooth transition
        const questionMark = document.querySelector('.question-mark');
        questionMark.classList.remove('fade-out');
        questionMark.style.display = 'block';

        // Reset hints - only first one revealed
        for (let i = 1; i <= this.maxHints; i++) {
            const hint = document.getElementById(`hint-${i}`);
            if (hint) {
                if (i === 1) {
                    hint.classList.add('revealed');
                } else {
                    hint.classList.remove('revealed');
                }
            }
        }

        // Hide image initially
        const imageContainer = document.querySelector('.image-container');
        imageContainer.classList.add('hidden');
        imageContainer.classList.remove('show');

        this.hideFeedback();
        this.hideCelebration();
    }
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', async () => {
    if (!window.GAME_DATA) {
        try {
            const resp = await fetch('/api/new-game');
            window.GAME_DATA = await resp.json();
        } catch (error) {
            console.error('Error fetching initial game data:', error);
            window.GAME_DATA = {};
        }
    }
    window.game = new CountryGuessingGame();
});

// Add some utility functions for enhanced UX
document.addEventListener('DOMContentLoaded', () => {
    // Add smooth scrolling for better UX
    document.documentElement.style.scrollBehavior = 'smooth';

    // Add loading animation
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('load', () => {
            img.style.opacity = '1';
        });
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.5s ease';
    });

    // Add focus ring for accessibility
    const focusableElements = document.querySelectorAll('button, input');
    focusableElements.forEach(element => {
        element.addEventListener('focus', (e) => {
            e.target.style.outline = '2px solid #667eea';
            e.target.style.outlineOffset = '2px';
        });
        element.addEventListener('blur', (e) => {
            e.target.style.outline = 'none';
        });
    });
});
