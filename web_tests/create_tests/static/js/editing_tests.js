$(document).ready(function() {
    MathfieldElement.locale = 'ru';

    // Инициализация MathLive-полей
    function initMathFields() {
        document.querySelectorAll('math-field').forEach(mf => {
            if (!mf.mathfield) {
                mf.mathfield = MathLive.makeMathField(mf, {
                    virtualKeyboardMode: 'manual',
                    smartFence: true
                });
            }
        });
    }
    initMathFields();

    // Обновляем видимость кнопок удаления для ответов (если один - скрываем)
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

    // Обновляем нумерацию заданий (номера, id)
    function updateAssignmentNumbers() {
        $('.fullExpression').each(function(index) {
            const num = index + 1;
            $(this).attr('id', 'fullExpression' + num);
            $(this).find('h3[id^="count"]').text('Задание №' + num + '.').attr('id', 'count' + num);
            // Можно обновить атрибуты name/id для инпутов внутри, если надо
        });
    }

    // Добавить новое задание (пустое)
    $('#sel-type').click(function() {
        const count = $('.fullExpression').length + 1;
        const newExpr = $(`
            <div class="fullExpression" id="fullExpression${count}">
                <div class="header-expression">
                    <div class="task-header-left">
                        <div class="task-number">
                            <h3 id="count${count}">Задание №${count}.</h3>
                        </div>
                        <div class="point-for-solve">
                            <input type="text" name="point_solve_${count}" id="point_solve${count}" value="1">
                        </div>
                    </div>
                    <button type="button" class="btn btn-icon del-expr" title="Удалить задание">
                        Удалить задание <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
                <div class="expression">
                    <math-field id="expr${count}" virtual-keyboard-mode="manual" name="user_expression_${count}" lang="ru"></math-field>
                </div>
                <div class="answers-container">
                    <div class="answer-row">
                        <div class="answer-wrapper">
                            <div class="answer-header">
                                <input type="checkbox" class="select-ans" name="exist_select_${count}">
                                <button class="del-ans">Удалить вариант ответа</button>
                            </div>
                            <div class="answer-content">
                                <math-field class="answer-field" name="user_ans_${count}"></math-field>
                                <div class="meta-fields">
                                    <input type="text" class="accuracy-field" name="user_eps_${count}" value="0">
                                    <input type="text" class="type-field" name="user_type_${count}" value="float">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="add-answer-footer">
                    <button type="button" class="btn-add-answer">
                        <i class="fas fa-plus-circle"></i> Добавить вариант ответа
                    </button>
                </div>
            </div>
        `);
        $('.mainPart').append(newExpr);
        initMathFields();
        updateAnswerVisibility(newExpr);
        updateAssignmentNumbers();
    });

    // Удаление задания
    $(document).on('click', '.del-expr', function() {
        $(this).closest('.fullExpression').remove();
        updateAssignmentNumbers();
    });

    // Добавление варианта ответа в задание
    $(document).on('click', '.btn-add-answer', function() {
        const expression = $(this).closest('.fullExpression');
        const count = $('.fullExpression').index(expression) + 1;

        const newAnswer = $(`
            <div class="answer-row">
                <div class="answer-wrapper">
                    <div class="answer-header">
                        <input type="checkbox" class="select-ans" name="exist_select_${count}">
                        <button class="del-ans">Удалить вариант ответа</button>
                    </div>
                    <div class="answer-content">
                        <math-field class="answer-field" name="user_ans_${count}"></math-field>
                        <div class="meta-fields">
                            <input type="text" class="accuracy-field" name="user_eps_${count}" value="0">
                            <input type="text" class="type-field" name="user_type_${count}" value="float">
                        </div>
                    </div>
                </div>
            </div>
        `);
        expression.find('.answers-container').append(newAnswer);
        initMathFields();
        updateAnswerVisibility(expression);
    });

    // Удаление варианта ответа
    $(document).on('click', '.del-ans', function() {
        const expression = $(this).closest('.fullExpression');
        $(this).closest('.answer-row').remove();
        updateAnswerVisibility(expression);
    });

    // Обработка сохранения - сбор данных в JSON
    $('.save-and-go-to-list').click(function(event) {
        event.preventDefault();

        const expressions = [];
        const points = [];
        const answers = [];
        const epsilons = [];
        const types = [];
        const boolAnswers = [];

        $('.fullExpression').each(function() {
            const expr = $(this);
            // user_expression из mathfield
            const userExpression = expr.find('math-field[name^="user_expression"]').get(0).mathfield.getValue();

            // Баллы
            const pointsForSolve = expr.find('input[id^="point_solve"]').val();

            // Для каждого варианта ответа собираем данные
            const ansList = [];
            const epsList = [];
            const typeList = [];
            const boolList = [];

            expr.find('.answer-row').each(function() {
                const ansField = $(this).find('math-field.answer-field').get(0);
                const ansVal = ansField ? ansField.mathfield.getValue() : "";

                const epsVal = $(this).find('.accuracy-field').val();
                const typeVal = $(this).find('.type-field').val();
                const boolVal = $(this).find('.select-ans').prop('checked');

                ansList.push(ansVal);
                epsList.push(epsVal);
                typeList.push(typeVal);
                boolList.push(boolVal);
            });

            expressions.push(userExpression);
            points.push(pointsForSolve);
            answers.push(ansList);
            epsilons.push(epsList);
            types.push(typeList);
            boolAnswers.push(boolList);
        });

        // Заполняем скрытые поля формы JSON-строками
        $('#expressions_json').val(JSON.stringify(expressions));
        $('#points_json').val(JSON.stringify(points));
        $('#answers_json').val(JSON.stringify(answers));
        $('#epsilons_json').val(JSON.stringify(epsilons));
        $('#types_json').val(JSON.stringify(types));
        $('#bool_answers_json').val(JSON.stringify(boolAnswers));

        // Заполняем остальные скрытые поля (тест)
        $('#hidden_name_test').val($('#testNameInput').val());
        const h = parseInt($('#hours').val() || 0);
        const m = parseInt($('#minutes').val() || 0);
        const s = parseInt($('#seconds').val() || 0);
        // Формируем DurationField в формате HH:MM:SS
        $('#hidden_time_solve').val(`${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`);
        $('#hidden_num_attempts').val($('#num_attempts').val());
        $('#hidden_subj_test').val($('#subj_test').val());
        $('#hidden_description_test').val($('#description_test').val());

        // Теперь сабмитим форму
        $('#testForm').submit();
    });
});
