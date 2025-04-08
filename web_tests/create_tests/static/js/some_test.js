function submitForm() {
    const mathFields = document.querySelectorAll('.answer');
    mathFields.forEach((mathField, index) => {
        const value = mathField.getValue('latex');
        document.getElementById(`hidden-answer-${index + 1}`).value = value;
    });

    document.getElementById('answerForm').submit();
}

document.addEventListener('DOMContentLoaded', function() {
    // Функция для вставки переносов
    function insertLineBreaks(expr, maxLineLength = 80) {
        return expr.replace(/(.{1,${maxLineLength}})(\s|$|,|;|\)|\]|\}|\\ )/g, '$1\\\\\n');
    }

    // Функция для обновления формул
    function processMathExpressions() {
        const containers = document.querySelectorAll('.math-expression');

        containers.forEach(container => {
            // Получаем оригинальное выражение из data-атрибута
            const originalExpr = container.dataset.expr;

            // Определяем максимальную длину строки на основе ширины контейнера
            const containerWidth = container.offsetWidth;
            const approxCharsPerLine = Math.floor(containerWidth / 12); // Примерно 12px на символ

            // Добавляем переносы строк
            const formattedExpr = insertLineBreaks(originalExpr, approxCharsPerLine);

            // Обновляем отображение
            container.innerHTML = `$$ ${formattedExpr} $$`;

            // Перерисовываем MathJax
            MathJax.typesetPromise([container]).catch(err => console.log(err));
        });
    }

    // Обработчик изменения размера окна
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(processMathExpressions, 200);
    });

    // Первоначальная обработка
    processMathExpressions();
});