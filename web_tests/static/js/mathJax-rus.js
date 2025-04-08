MathfieldElement.locale = 'ru';  // Устанавливаем русский язык

customElements.whenDefined('math-field').then(() => {
    console.log("Locale:", MathfieldElement.locale);
    console.log(MathfieldElement.strings[MathfieldElement.locale.substring(0, 2)]);
});

// Перехват пробела в math-field (оставляем без изменений)
$(document).on('keydown', 'math-field', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
        this.insert("\\;");
        if (typeof this.executeCommand === "function") {
            this.executeCommand('insertNewline');
        }
    }
});

$('.container').on('keydown', 'math-field', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        let mathField = this;
        let content = mathField.getValue();
        if (!content.startsWith('\\displaylines{')) {
            content = '\\[\n\\displaylines{\n    ' + content + '\n}\n\\]';
            mathField.setValue(content);
        }
    }
});

$('.container').on('input', 'math-field', function() {
    let mathField = this;
    let cursorPosition = mathField.selectionStart;
    let fieldWidth = mathField.clientWidth;
    let scrollWidth = mathField.scrollWidth;
    if (scrollWidth - cursorPosition <= fieldWidth * 0.1) {
        mathField.insertText('\\newline ');
    }
});
