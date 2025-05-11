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

document.addEventListener("DOMContentLoaded", () => {
    const timerElement = document.getElementById('timer');
    const timeRemaining = timerElement.textContent.trim();  // Получаем начальное время

    // Преобразуем время в объект Date
    const [hours, minutes, seconds] = timeRemaining.split(':').map(num => parseInt(num));
    let remainingTimeInSeconds = hours * 3600 + minutes * 60 + seconds;

    function updateTimer() {
        // Считаем оставшееся время
        if (remainingTimeInSeconds <= 0) {
            clearInterval(timerInterval);
            timerElement.textContent = "Время вышло!";
            return;
        }

        remainingTimeInSeconds--;

        const h = Math.floor(remainingTimeInSeconds / 3600);
        const m = Math.floor((remainingTimeInSeconds % 3600) / 60);
        const s = remainingTimeInSeconds % 60;

        // Обновляем текст таймера
        timerElement.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }

    // Запуск таймера, обновление каждую секунду
    const timerInterval = setInterval(updateTimer, 1000);
});
