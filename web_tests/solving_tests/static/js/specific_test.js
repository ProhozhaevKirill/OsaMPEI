document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("answerForm");

    form.addEventListener("submit", function (e) {
        const results = [];
        const questions = document.querySelectorAll(".question-card");

        questions.forEach((questionCard) => {
            const checkboxes = questionCard.querySelectorAll('input[type="checkbox"]');

            if (checkboxes.length > 0) {
                // Есть checkbox — собрать выбранные
                const selected = Array.from(checkboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);
                results.push(selected.join(";"));
            } else {
                // Нет checkbox — значит свободный ответ, берём из math-field
                const mathField = questionCard.querySelector("math-field");
                results.push(mathField ? mathField.getValue().trim() : "");
            }
        });

        // Сохраняем как JSON-строку в скрытое поле
        document.getElementById("binaryAnswers").value = JSON.stringify(results);
    });
});
