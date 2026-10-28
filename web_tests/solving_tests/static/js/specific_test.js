function studentFieldAnswer(field) {
    if (!field) return '';
    const value = field.value || '';
    const template = field.dataset.answerTemplate || '';
    return template && value.replace(/\s/g, '') === template.replace(/\s/g, '') ? '' : value;
}

document.addEventListener('DOMContentLoaded', async () => {
    const form = document.getElementById('answerForm');
    if (!form) return;
    await customElements.whenDefined('math-field');
    const cards = [...document.querySelectorAll('.question-card')];
    const collect = () => cards.map(card => {
        const boxes = [...card.querySelectorAll('input[type="checkbox"]')];
        return boxes.length ? '@answers:' + JSON.stringify(boxes.filter(el => el.checked).map(el => el.value))
            : studentFieldAnswer(card.querySelector('math-field'));
    });
    const initial = document.getElementById('attemptState');
    if (!initial) {
        // Teacher preview never creates a student attempt.
        form.addEventListener('submit', () => document.getElementById('binaryAnswers').value = JSON.stringify(collect()));
        const previewTimer = document.getElementById('timer');
        const duration = previewTimer.textContent.trim().split(':').map(Number).reduce((n, part) => n * 60 + part, 0);
        const started = performance.now();
        const interval = setInterval(() => {
            const seconds = Math.max(0, duration - Math.floor((performance.now() - started) / 1000));
            previewTimer.textContent = seconds ? [Math.floor(seconds / 3600), Math.floor(seconds % 3600 / 60), seconds % 60]
                .map(part => String(part).padStart(2, '0')).join(':') : 'Время вышло!';
            if (!seconds) clearInterval(interval);
        }, 1000);
        return;
    }
    let state = JSON.parse(initial.textContent);
    const api = document.getElementById('attemptApi').value;
    const status = document.getElementById('saveStatus');
    const timer = document.getElementById('timer');
    const key = 'osampei:attempt:' + state.attempt_id;
    let pending = {};
    let chain = Promise.resolve();
    let debounce;
    let finishing = false;
    let finished = false;
    const responseStart = performance.getEntriesByType('navigation')[0]?.responseStart ?? performance.now();
    let serverTime = state.server_now + Math.max(0, performance.now() - responseStart);
    let measuredAt = performance.now();
    const setStatus = (text, error = false) => {
        status.textContent = text;
        status.style.color = error ? '#b02a37' : '';
    };
    const cache = () => {
        try {
            if (Object.keys(pending).length) localStorage.setItem(key, JSON.stringify({deadline: state.deadline, changes: pending}));
            else localStorage.removeItem(key);
        } catch (_) { /* Server autosave still works when local storage is unavailable. */ }
    };
    try {
        const saved = JSON.parse(localStorage.getItem(key));
        if (saved?.deadline === state.deadline && state.server_now < state.deadline) pending = saved.changes || {};
    } catch (_) { /* Ignore a damaged local fallback. */ }
    const restore = () => {
        cards.forEach((card, index) => {
            const answer = pending[index] ?? state.answers[index] ?? '';
            const boxes = [...card.querySelectorAll('input[type="checkbox"]')];
            if (boxes.length) {
                let selected = [];
                try { selected = JSON.parse(answer.slice('@answers:'.length)); } catch (_) { /* Empty answer. */ }
                boxes.forEach(box => box.checked = selected.includes(box.value));
            } else {
                const field = card.querySelector('math-field');
                const display = answer || field?.dataset.answerTemplate || '';
                if (field && field.value !== display) field.value = display;
            }
            document.getElementById('nav-' + (index + 1))?.classList.toggle('completed',
                boxes.length ? boxes.some(box => box.checked) : Boolean(answer.trim()));
        });
    };
    const lock = value => {
        cards.forEach(card => {
            card.querySelectorAll('math-field').forEach(field => field.readOnly = value);
            card.querySelectorAll('input[type="checkbox"]').forEach(box => box.disabled = value);
        });
        form.querySelector('button[type="submit"]').disabled = value;
    };
    const accept = data => {
        state = data;
        serverTime = data.server_now;
        measuredAt = performance.now();
        if (data.submitted || data.completed) {
            finished = true;
            pending = {};
            cache();
            window.location.replace(data.result_url);
            return;
        }
        restore();
    };
    const transmit = async action => {
        if (finished) return;
        for (let retry = 0; retry < 4; retry++) {
            const changes = {...pending};
            const response = await fetch(api, {
                method: 'POST', credentials: 'same-origin', cache: 'no-store',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value},
                body: JSON.stringify({action, revision: state.revision, changes}),
            });
            if (!response.headers.get('content-type')?.includes('application/json')) throw Error('Session unavailable');
            const data = await response.json();
            if (response.status === 409) { accept(data); continue; }
            if (!response.ok) throw Error('Save failed');
            for (const [index, answer] of Object.entries(changes)) {
                if (pending[index] === answer) delete pending[index];
            }
            accept(data);
            cache();
            if (!finished) setStatus(Object.keys(pending).length ? 'Сохраняем ответы…' : 'Все ответы сохранены');
            return;
        }
        throw Error('Concurrent update');
    };
    const send = action => {
        chain = chain.then(() => transmit(action)).catch(() => {
            setStatus('Не удалось сохранить на сервере. Повторяем отправку…', true);
            if (finishing) setTimeout(() => send('finish'), 1500);
        });
        return chain;
    };
    restore();
    const changed = event => {
        const card = event.target.closest('.question-card');
        if (!card || finishing) return;
        const index = cards.indexOf(card);
        pending[index] = collect()[index];
        cache();
        setStatus('Сохраняем ответы…');
        clearTimeout(debounce);
        debounce = setTimeout(() => send('save'), 250);
    };
    document.addEventListener('input', changed);
    document.addEventListener('change', changed);
    const finish = () => {
        if (finishing || finished) return;
        finishing = true;
        lock(true);
        clearTimeout(debounce);
        setStatus('Завершаем попытку…');
        send('finish');
    };
    form.addEventListener('submit', event => { event.preventDefault(); finish(); });
    const tick = () => {
        const seconds = Math.max(0, Math.ceil((state.deadline - serverTime - (performance.now() - measuredAt)) / 1000));
        timer.textContent = [Math.floor(seconds / 3600), Math.floor(seconds % 3600 / 60), seconds % 60]
            .map(part => String(part).padStart(2, '0')).join(':');
        if (!seconds) finish();
    };
    tick();
    setInterval(tick, 250);
    const synchronize = () => {
        if (finished) return;
        if (finishing || Object.keys(pending).length) { send(finishing ? 'finish' : 'save'); return; }
        chain = chain.then(async () => {
            const response = await fetch(api, {cache: 'no-store', credentials: 'same-origin'});
            if (!response.ok) throw Error('Sync failed');
            accept(await response.json());
        }).catch(() => setStatus('Нет связи с сервером. Повторяем подключение…', true));
    };
    setInterval(synchronize, 3000);
    window.addEventListener('online', synchronize);
    window.addEventListener('pageshow', event => { if (event.persisted) synchronize(); });
    document.addEventListener('visibilitychange', () => { if (!document.hidden) synchronize(); });
    window.addEventListener('pagehide', () => {
        if (finished || !Object.keys(pending).length) return;
        cache();
        fetch(api, {method: 'POST', credentials: 'same-origin', keepalive: true,
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value},
            body: JSON.stringify({action: 'save', revision: state.revision, changes: pending})}).catch(() => {});
    });
    if (Object.keys(pending).length) send('save');
    else synchronize();
});

document.addEventListener("DOMContentLoaded", () => {
    const questionCards = document.querySelectorAll(".question-card");

    questionCards.forEach((card) => {
        const questionNumber = card.dataset.question;
        const navLink = document.getElementById(`nav-${questionNumber}`);

        const checkboxes = card.querySelectorAll('input[type="checkbox"]');
        const mathField = card.querySelector("math-field");

        function updateStatus() {
            let filled = false;

            if (checkboxes.length > 0) {
                filled = Array.from(checkboxes).some(cb => cb.checked);
            } else if (mathField) {
                filled = studentFieldAnswer(mathField).trim().length > 0;
            }

            if (filled) {
                navLink.classList.add("completed");
            } else {
                navLink.classList.remove("completed");
            }
        }

        // Навешиваем обработчики
        if (checkboxes.length > 0) {
            checkboxes.forEach(cb => cb.addEventListener("change", updateStatus));
        }

        if (mathField) {
            mathField.addEventListener("input", updateStatus);
        }

        // Обновим статус при загрузке
        updateStatus();
    });

    // Прокрутка к задаче (если нужно с анимацией):
    document.querySelectorAll(".task-number").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = link.getAttribute("href").substring(1);
            const target = document.getElementById(targetId);
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        });
    });
});
