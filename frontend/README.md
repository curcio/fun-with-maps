# Frontend Module - Guess the Country Game

A progressive web application that implements a country guessing game using HTML, CSS, and JavaScript.

## Overview

This frontend module is built with 5 progressive iterations, each adding new functionality:

1. **Iteration 1**: Clean HTML page with centered image
2. **Iteration 2**: Interactive guessing game with input field
3. **Iteration 3**: Input validation against a static country list
4. **Iteration 4**: Progressive hint system
5. **Iteration 5**: Celebration animations with fireworks

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── style.css           # Styling and animations
├── script.js           # Game logic and interactivity
└── README.md           # This documentation
```

## Features

### Iteration 1: Basic Display
- Clean, modern design with gradient background
- Centered image display
- Responsive layout
- Professional typography

### Iteration 2: Interactive Game
- Question mark icon with pulse animation
- Input field for country guessing
- Submit button with hover effects
- Image reveals on correct answer

### Iteration 3: Input Validation
- Static list of 10+ valid countries
- Case-insensitive matching
- Feedback for invalid country names
- Accepts alternative names (e.g., "Persia" for "Iran")

### Iteration 4: Hint System
- 4 progressive hints about the country
- Hints reveal one by one on wrong answers
- Smooth slide-in animations
- Contextual geographic and cultural hints

### Iteration 5: Success Celebration
- Fireworks animation on correct answer
- Full-screen celebration overlay
- Animated success message
- Auto-dismiss after 5 seconds

## How to Use

1. **Open the application**: Open `index.html` in a web browser
2. **Navigate iterations**: Use the iteration control panel in the top-right corner
3. **Play the game**: 
   - Enter a country name in the input field
   - Press Enter or click Submit
   - View hints if you get wrong answers (Iteration 4+)
   - Enjoy the celebration when you guess correctly (Iteration 5)

## Game Mechanics

### Valid Countries
The game includes these countries in its validation list:
- Iran/Persia (correct answer)
- United States/USA/America
- France, Germany, Japan, China, Brazil
- Canada, Australia, India, Russia, Italy

### Hints (Iteration 4+)
1. Geographic and cultural heritage information
2. Historical names and famous exports
3. Geographic features and neighboring regions
4. Capital city and natural resources

### Scoring
- Wrong attempts trigger progressive hint reveals
- Game ends on correct answer
- Input disabled after winning

## Technical Details

### Technologies Used
- **HTML5**: Semantic markup and structure
- **CSS3**: Modern styling, animations, and responsive design
- **JavaScript ES6+**: Game logic, DOM manipulation, and event handling
- **Font Awesome**: Icons for enhanced UI

### Key Features
- Object-oriented JavaScript architecture
- Responsive design for mobile and desktop
- Smooth animations and transitions
- Accessibility features (focus rings, keyboard navigation)
- Progressive enhancement across iterations

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile-friendly responsive design
- Graceful degradation for older browsers

## Development

### Architecture
The game uses a class-based approach with the `CountryGuessingGame` class managing:
- Game state and logic
- DOM manipulation
- Event handling
- Iteration management

### Customization
To modify the game:
1. **Change countries**: Edit the `validCountries` array in `script.js`
2. **Update hints**: Modify the hint text in `index.html`
3. **Adjust styling**: Update colors and animations in `style.css`
4. **Add images**: Replace the image source in the HTML

## Future Enhancements

Potential improvements could include:
- Multiple country images and randomization
- Difficulty levels with different hint quantities
- Score tracking and leaderboards
- Sound effects and enhanced animations
- Integration with the backend map analysis features
- Multiplayer functionality

## License

Part of the Fun with Maps project. 