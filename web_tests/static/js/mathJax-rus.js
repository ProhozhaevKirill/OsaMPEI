MathfieldElement.locale = 'ru';

// Use MathLive's input handling; never rewrite the field's LaTeX on a timer.
document.addEventListener('focusin', function (event) {
    if (event.target.matches('math-field')) {
        event.target.mathModeSpace = '\\;';
    }
});
