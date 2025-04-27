$(document).ready(function() {
    var expressionCount = $('.fullExpression').length;
    MathfieldElement.locale = 'ru';

    // Инициализация MathField для существующих элементов
    function initMathFields(container) {
        container.find('math-field').each(function() {
            if (!this.isConnected) {
                new MathfieldElement(this);
            }
        });
    }

    // Обновление видимости элементов
    function updateAnswerVisibility(expressionId) {
        const $expression = $(`#${expressionId}`);
        const answers = $expression.find('.right-side');
        answers.find('.select-ans, .del-ans').toggle(answers.length > 1);
    }

    // Перенумерация заданий
    function updateAssignmentNumbers() {
        $('.fullExpression').each(function(index) {
            const newId = index + 1;
            $(this).attr('id', `fullExpression${newId}`);
            $(this).find('h4').text(`Задание №${newId}:`);
            $(this).find('[id^="point_solve"]').attr('id', `point_solve${newId}`);
            $(this).find('[id^="expr"]').attr('id', `expr${newId}`);
        });
        expressionCount = $('.fullExpression').length;
    }

    // Добавление задания
    $(document).on('click', '#sel-type', function() {
        const $clone = $('.fullExpression').first().clone();
        $clone.find('input, math-field').val('');
        $clone.find('.right-side').not(':first').remove();
        $clone.insertBefore('.butChange');

        // Инициализация новых MathField
        initMathFields($clone);
        updateAssignmentNumbers();
        updateAnswerVisibility($clone.attr('id'));
    });

    // Добавление варианта ответа
    $(document).on('click', '.add-ans', function() {
        const $expression = $(this).closest('.butChange').prev('.fullExpression');
        const $clone = $expression.find('.right-side').first().clone();
        $clone.find('input, math-field').val('');
        $expression.find('.right-side').last().after($clone);
        updateAnswerVisibility($expression.attr('id'));
    });

    // Удаление варианта ответа
    $(document).on('click', '.del-ans', function() {
        const $parent = $(this).closest('.fullExpression');
        if ($parent.find('.right-side').length > 1) {
            $(this).closest('.right-side').remove();
            updateAnswerVisibility($parent.attr('id'));
        }
    });

    // Удаление задания
    $(document).on('click', '.del-expr', function() {
        if ($('.fullExpression').length > 1) {
            $(this).closest('.fullExpression').remove();
            updateAssignmentNumbers();
        }
    });

    // Запись в скрытые инпуты
    function updateFormFields() {
        let point = [];
        let expressions = [];
        let answers = [];
        let epsilons = [];
        let types = [];
        let boolAns = [];

        $('.fullExpression').each(function(index) {
            const questionIndex = index + 1;
            point.push($(`#point_solve${questionIndex}`).val());
            expressions.push($(`#expr${questionIndex}`).val());
            let answerValues = [];
            let epsilonValues = [];
            let typeValues = [];
            let boolAnsValues = [];

            $(this).find('.right-side').each(function() {
                answerValues.push($(this).find('.answer').get(0).value);
                epsilonValues.push($(this).find('.accuracy').val() || "0");
                typeValues.push($(this).find('.type-field').val() || "float");
                boolAnsValues.push($(this).find('.select-ans').is(':checked') ? "1" : "0");
            });
            answers.push(answerValues.join(';'));
            epsilons.push(epsilonValues.join(';'));
            types.push(typeValues.join(';'));
            boolAns.push(boolAnsValues.join(';'));
        });

        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_time_solve').val($('#timeSolve').val());
        $('#hidden_point_solve1').val(JSON.stringify(point));
        $('#hidden_expr1').val(JSON.stringify(expressions));
        $('#hidden_ans1').val(JSON.stringify(answers));
        $('#hidden_eps1').val(JSON.stringify(epsilons));
        $('#hidden_typ1').val(JSON.stringify(types));
        $('#hidden_bool_ans1').val(JSON.stringify(boolAns));
    }

    $('.save-and-go-to-list').on('click', function(e) {
        updateFormFields();
    });
});
