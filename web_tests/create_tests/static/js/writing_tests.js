$(document).ready(function() {
    var expressionCount = $('.fullExpression').length;
    MathfieldElement.locale = 'ru';

    // Инициализация MathField
    function initMathFields() {
        document.querySelectorAll('math-field').forEach(mf => {
            if (!mf.mathfield) {
                new MathfieldElement(mf);
            }
        });
    }
    initMathFields();

    // Обновление видимости элементов
    function updateAnswerVisibility(expression) {
        const answers = expression.find('.answer-row');
        const showControls = answers.length > 1;

        answers.each(function() {
            const $row = $(this);
            if (answers.length === 1) {
                $row.find('.select-ans').prop('checked', true);
            }
            $row.find('.del-ans, .select-ans').toggleClass('hidden', !showControls);
            $row.find('.accuracy-field').removeClass('hidden');
        });
    }

    // Перенумерация заданий
    function updateAssignmentNumbers() {
        $('.fullExpression').each(function(index) {
            const newId = index + 1;
            $(this).attr('id', `fullExpression${newId}`);
            $(this).find('h3').attr('id', `count${newId}`).text(`Задание №${newId}.`);
            $(this).find('[id^="point_solve"]').attr('id', `point_solve${newId}`);
            $(this).find('[id^="expr"]').attr('id', `expr${newId}`);
        });
        expressionCount = $('.fullExpression').length;
    }

    // Добавление задания
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

    // Подготовка данных перед сохранением
    function updateFormFields() {
        let point = [];
        let expressions = [];
        let answers = [];
        let epsilons = [];
        let boolAns = [];

        $('.fullExpression').each(function(index) {
            const questionIndex = index + 1;
            point.push($(`#point_solve${questionIndex}`).val() || "1");
            expressions.push($(`#expr${questionIndex}`).val());

            let answerValues = [];
            let epsilonValues = [];
            let boolAnsValues = [];

            $(this).find('.answer-row').each(function() {
                answerValues.push($(this).find('.answer-field').val());
                epsilonValues.push($(this).find('.accuracy-field').val() || "0");
                boolAnsValues.push($(this).find('.select-ans').is(':checked') ? "1" : "0");
            });

            answers.push(answerValues.join(';'));
            epsilons.push(epsilonValues.join(';'));
            boolAns.push(boolAnsValues.join(';'));
        });

        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_time_solve').val(`${$('#hours').val() || 0}:${$('#minutes').val() || 0}:${$('#seconds').val() || 0}`);
        $('#hidden_subj_test').val($('#subj_test').val());
        $('#hidden_description_test').val($('#description_test').val() || "Без описания");
        $('#hidden_point_solve1').val(JSON.stringify(point));
        $('#hidden_expr1').val(JSON.stringify(expressions));
        $('#hidden_ans1').val(JSON.stringify(answers));
        $('#hidden_eps1').val(JSON.stringify(epsilons));
        $('#hidden_bool_ans1').val(JSON.stringify(boolAns));
    }

    // Обработчик сохранения
    $('.save-and-go-to-list').on('click', function(e) {
        updateFormFields();
    });
});