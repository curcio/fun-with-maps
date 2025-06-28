// Game state management
class CountryGuessingGame {
    constructor() {
        // Static list of 10 countries for validation (iteration 3)
        this.validCountries = [
            'iran', 'persia', 'united states', 'usa', 'america',
            'france', 'germany', 'japan', 'china', 'brazil',
            'canada', 'australia', 'india', 'russia', 'italy'
        ];

        const data = window.GAME_DATA || {};
        // Correct answer and validation list provided by backend
        this.validCountries = data.valid_countries || this.validCountries;
        this.correctAnswer = (data.country || 'iran').toLowerCase();
        this.alternativeAnswers = [];

        // Game state
        this.wrongAttempts = 0;
        this.maxHints = 4;
        this.maxErrors = 4;
        this.gameWon = false;
        this.gameOver = false;

        // Initialize the game
        this.init();
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

        if (!userAnswer) {
            return; // Just return, no feedback needed
        }

        // Check if answer is correct
        if (this.isCorrectAnswer(userAnswer)) {
            this.handleCorrectAnswer();
        } else {
            this.handleWrongAnswer(userAnswer);
        }

        // Clear input
        input.value = '';
    }

    isCorrectAnswer(answer) {
        const correctAnswers = [this.correctAnswer, ...this.alternativeAnswers];
        return correctAnswers.includes(answer);
    }

    handleCorrectAnswer() {
        this.gameWon = true;

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
        this.wrongAttempts++;

        // Check if answer is in valid countries list
        if (!this.validCountries.includes(answer)) {
            // Invalid country, don't count as wrong attempt, don't show hint
            this.wrongAttempts--;
            return;
        }

        // Check for game over after 4 errors
        if (this.wrongAttempts >= this.maxErrors) {
            this.handleGameOver();
            return;
        }

        // Show next hint for wrong but valid answer
        this.showNextHint();
    }

    showNextHint() {
        // Reveal the next hint based on number of wrong attempts
        // wrongAttempts = 1 -> reveal hint-2, wrongAttempts = 2 -> reveal hint-3, etc.
        const nextHintIndex = this.wrongAttempts + 1;
        if (nextHintIndex <= this.maxHints) {
            const hintElement = document.getElementById(`hint-${nextHintIndex}`);
            if (hintElement) {
                hintElement.classList.add('revealed');
            }
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

    resetGame() {
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

        this.hideCelebration();
    }
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
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
