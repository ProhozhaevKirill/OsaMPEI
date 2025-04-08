// Инициализация всех math-field
document.querySelectorAll('math-field').forEach(field => {
    MathLive.makeMathField(field);
});

// Функция для сбора ответов из чекбоксов и полей math-field
function collectAnswers() {
    const answers = [];

    // Сбор ответов для полей math-field
    document.querySelectorAll('math-field').forEach(field => {
        answers.push(field.getValue());
    });

    // Сбор состояний чекбоксов в виде бинарной строки
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const binaryStr = Array.from(checkboxes).map(cb => cb.checked ? '1' : '0').join('');
    answers.push(binaryStr);

    return answers.join('; ');
}

// Функция для отправки формы
function submitForm(event) {
    event.preventDefault();
    const answersStr = collectAnswers();
    document.getElementById('binary-answers').value = answersStr;
    document.getElementById('answerForm').submit();
}