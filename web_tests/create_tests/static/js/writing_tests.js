$(document).ready(function() {
    var expressionCount = 1;
    var answerCount = 1;

    MathfieldElement.locale = 'ru';  // Устанавливаем русский язык

    customElements.whenDefined('math-field').then(() => {
        console.log("Locale:", MathfieldElement.locale);
        console.log(MathfieldElement.strings[MathfieldElement.locale.substring(0, 2)]);
    });

    // Перехват пробела в math-field (оставляем без изменений)
    $(document).on('keydown', 'math-field', function(e) {
        if (e.key === ' ') {
            e.preventDefault();
            this.insert("\\;");
            if (typeof this.executeCommand === "function") {
                this.executeCommand('insertNewline');
            }
        }
    });

    $('.container').on('keydown', 'math-field', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            let mathField = this;
            let content = mathField.getValue();
            if (!content.startsWith('\\displaylines{')) {
                content = '\\[\n\\displaylines{\n    ' + content + '\n}\n\\]';
                mathField.setValue(content);
            }
        }
    });

    $('.container').on('input', 'math-field', function() {
        let mathField = this;
        let cursorPosition = mathField.selectionStart;
        let fieldWidth = mathField.clientWidth;
        let scrollWidth = mathField.scrollWidth;
        if (scrollWidth - cursorPosition <= fieldWidth * 0.1) {
            mathField.insertText('\\newline ');
        }
    });

    // Обновление видимости чекбоксов и кнопок удаления вариантов ответа
    function updateAnswerVisibility(expressionId) {
        var $expression = $('#fullExpression' + expressionId);
        var answers = $expression.find('.right-side');
        var checkboxes = $expression.find('.select-ans');
        var deleteButtons = $expression.find('.del-ans');

        if (answers.length > 1) {
            checkboxes.css('visibility', 'visible');
            deleteButtons.css('visibility', 'visible');
        } else {
            checkboxes.css('visibility', 'hidden');
            deleteButtons.css('visibility', 'hidden');
        }
    }

    // Функция для перенумерации заданий после удаления или добавления
    function updateAssignmentNumbers() {
        expressionCount = 0;
        $('.fullExpression').each(function(index) {
            var newIndex = index + 1;
            expressionCount = newIndex;
            // Обновляем id и заголовки
            $(this).attr('id', 'fullExpression' + newIndex);
            $(this).find('.header-expression h4').attr('id', 'count' + newIndex)
                  .text('Задание №' + newIndex + ':');
            // Обновляем id внутренних элементов (при необходимости)
            $(this).find('[id^=point_solve]').attr('id', 'point_solve' + newIndex);
            $(this).find('[id^=expr]').attr('id', 'expr' + newIndex);
        });
    }

    // Добавление нового задания (пустого)
    $('.add-btn').click(function() {
        expressionCount++;
        var $newExpression = $('.fullExpression').first().clone();
        // Обновляем id нового задания
        $newExpression.attr('id', 'fullExpression' + expressionCount);
        // Очищаем все input и math-field в новом задании
        $newExpression.find('input, math-field').each(function() {
            $(this).val('');
        });
        // Обновляем id внутренних элементов
        $newExpression.find('[id^=point_solve]').attr('id', 'point_solve' + expressionCount);
        $newExpression.find('[id^=expr]').attr('id', 'expr' + expressionCount);
        $newExpression.find('.header-expression h4').attr('id', 'count' + expressionCount)
                  .text('Задание №' + expressionCount + ':');
        // Оставляем только один вариант ответа
        $newExpression.find('.right-side').not(':first').remove();
        $newExpression.find('.right-side input, .right-side math-field').val('');
        // Вставляем новое задание перед блоком с кнопками
        $newExpression.insertBefore('.butChange');
        updateAnswerVisibility(expressionCount);
    });

    // Добавление нового варианта ответа (пустого)
    $('.add-ans').click(function() {
        var $currentExpression = $('.fullExpression').last();
        var expressionId = $currentExpression.attr('id').replace('fullExpression', '');
        answerCount++;
        var $lastAnswer = $currentExpression.find('.right-side').last();
        var $newAnswer = $lastAnswer.clone();
        $newAnswer.attr('id', 'right-side' + answerCount);
        $newAnswer.find('input, math-field').val('');
        $newAnswer.find('[id^=select-ans]').removeAttr('id').css('visibility', 'visible');
        $newAnswer.find('.del-ans').css('visibility', 'visible');
        $lastAnswer.after($newAnswer);
        updateAnswerVisibility(expressionId);
    });

    // Удаление варианта ответа
    $('.container').on('click', '.del-ans', function() {
        var $expression = $(this).closest('.fullExpression');
        var expressionId = $expression.attr('id').replace('fullExpression', '');
        if ($expression.find('.right-side').length > 1) {
            $(this).closest('.right-side').remove();
            updateAnswerVisibility(expressionId);
        }
    });

    // Удаление конкретного задания (нажатие кнопки внутри блока задания)
    $('.container').on('click', '.del-expr', function() {
        if ($('.fullExpression').length > 1) {
            $(this).closest('.fullExpression').remove();
            updateAssignmentNumbers();
        } else {
            alert("Нельзя удалить последнее задание!");
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
