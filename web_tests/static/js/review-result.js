(() => {
    const config = document.currentScript.dataset;
    const csrfToken = () => document.cookie.split(';').map(value => value.trim())
        .find(value => value.startsWith('csrftoken='))?.slice('csrftoken='.length) || '';

    window.gradeFreeAnswer = async (questionIndex, isCorrect, button) => {
        const card = document.getElementById('question-card-' + questionIndex);
        const buttons = [...card.querySelectorAll('.btn-grade')];
        if (buttons.some(item => item.disabled)) return;
        buttons.forEach(item => { item.disabled = true; });
        try {
            const response = await fetch(config.reviewUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': decodeURIComponent(csrfToken())},
                body: JSON.stringify({result_id: Number(config.resultId), question_index: questionIndex, is_correct: isCorrect}),
            });
            const data = await response.json();
            if (!response.ok || !data.success || data.result_id !== Number(config.resultId)) {
                throw new Error(data.error || 'Не удалось сохранить оценку.');
            }

            // Only show a grade after the server saved this exact attempt.
            buttons.forEach(item => item.classList.remove('active'));
            button.classList.add('active');
            card.classList.toggle('question-correct', isCorrect === true);
            card.classList.toggle('question-incorrect', isCorrect === false);
            const answer = document.getElementById('answer-block-' + questionIndex);
            answer.classList.toggle('answer-correct', isCorrect === true);
            answer.classList.toggle('answer-incorrect', isCorrect === false);
            const badge = document.getElementById('badge-' + questionIndex);
            badge.className = isCorrect === null ? '' : `status-badge ${isCorrect ? 'correct-badge' : 'incorrect-badge'}`;
            badge.innerHTML = isCorrect === null ? '' : `<i class="fas ${isCorrect ? 'fa-check' : 'fa-times'}"></i>`;
            const pending = document.getElementById('pending-' + questionIndex);
            if (pending) {
                pending.hidden = isCorrect !== null;
                pending.style.display = isCorrect === null ? '' : 'none';
            }
            const score = document.querySelector('.summary-value[data-score]');
            if (score) score.textContent = `${data.new_score.toFixed(1)} / ${data.max_score.toFixed(1)}`;
            const remaining = document.querySelector('[data-review-remaining]');
            if (remaining) remaining.textContent = data.ungraded_count ?
                `Непроверенных ответов: ${data.ungraded_count}` : 'Все свободные ответы проверены';
            const message = document.getElementById('score-msg-' + questionIndex);
            if (message) {
                message.style.display = 'inline-block';
                setTimeout(() => { message.style.display = 'none'; }, 2500);
            }
        } catch (error) {
            window.alert('Оценка не сохранена. ' + error.message);
        } finally {
            buttons.forEach(item => { item.disabled = false; });
        }
    };
})();
