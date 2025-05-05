$(document).ready(function() {
    // Добавление задания (может быть частью модального интерфейса)
    $(document).on('click', '#sel-type', function() {
        const $clone = $('.fullExpression').first().clone();
        $clone.find('input').val('');
        $clone.find('math-field').each(function() {
            this.value = '';
        });
        $clone.find('.answer-row').not(':first').remove();
        $('.butChange').before($clone);

        initMathFields();
        updateAssignmentNumbers();
        updateAnswerVisibility($clone);
    });



    // Добавление варианта ответа
    $(document).on('click', '.btn-add-answer', function() {
        const $expression = $(this).closest('.fullExpression');
        const $clone = $expression.find('.answer-row').first().clone();
        $clone.find('input').val('');
        $clone.find('math-field').each(function() {
            this.value = '';
        });
        $clone.find('.select-ans').prop('checked', false);
        $expression.find('.answers-container').append($clone);
        updateAnswerVisibility($expression);
        initMathFields();
    });

    // Удаление варианта ответа
    $(document).on('click', '.del-ans', function() {
        const $parent = $(this).closest('.fullExpression');
        if ($parent.find('.answer-row').length > 1) {
            $(this).closest('.answer-row').remove();
            updateAnswerVisibility($parent);
        }
    });

    // Удаление задания
    $(document).on('click', '.del-expr', function() {
        if ($('.fullExpression').length > 1) {
            $(this).closest('.fullExpression').remove();
            updateAssignmentNumbers();
        }
    });
});
