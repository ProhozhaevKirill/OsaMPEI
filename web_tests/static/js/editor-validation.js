// Validate the whole editor before serialization can omit incomplete variants.
window.validateEditorVariants = function () {
    document.querySelectorAll('.task-variant .invalid').forEach(el => el.classList.remove('invalid'));
    for (const variant of document.querySelectorAll('.task-variant')) {
        let invalid = null;
        const expression = variant.querySelector('math-field[name="user_expression"]');
        if (!expression || !expression.value.trim()) invalid = expression || variant;
        for (const row of variant.querySelectorAll('.answer-row')) {
            const type = row.querySelector('.type-field');
            const answer = row.querySelector('.answer-field');
            const free = Number(type.selectedOptions[0]?.dataset.typeCode) === 5;
            if (!type.value) invalid = type;
            if (!free && !answer.value.trim()) invalid = answer;
        }
        if (invalid) {
            invalid.classList.add('invalid');
            const group = variant.closest('.task-group');
            document.querySelectorAll('.task-group').forEach(el => el.classList.toggle('active', el === group));
            invalid.focus();
            throw new Error('Заполните условие, ответы и тип ответа каждого варианта. Изменения не отправлены.');
        }
    }
};

// Clear a previous required-field error as soon as the user fills the field.
for (const eventName of ['input', 'change']) {
    document.addEventListener(eventName, function (event) {
        const field = event.target;
        if (!field.matches('math-field, input, select')) return;
        if (String(field.value || '').trim()) field.classList.remove('invalid');
        if (field.matches('.type-field') && Number(field.selectedOptions[0]?.dataset.typeCode) === 5) {
            field.closest('.answer-row').querySelector('.answer-field')?.classList.remove('invalid');
        }
    });
}
