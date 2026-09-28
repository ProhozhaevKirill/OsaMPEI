// Validate the whole editor before serialization can omit incomplete variants.
window.validateEditorVariants = function () {
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
