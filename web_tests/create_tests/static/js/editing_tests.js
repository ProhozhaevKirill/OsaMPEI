$(document).ready(function () {
    MathfieldElement.locale = 'ru';

    // Инициализация MathLive-полей
    function initMathFields() {
        document.querySelectorAll('math-field').forEach(mf => {
            if (!mf.mathfield) {
                console.log("Initializing MathLive field:", mf);
                // Принудительная инициализация
                mf.style.display = 'block';
                setTimeout(() => {
                    if (!mf.mathfield) {
                        console.warn("MathLive field still not initialized:", mf);
                    }
                }, 100);
            }
        });
    }
    initMathFields();

    // Показывать/скрывать кнопки удаления и чекбоксы
    function updateAnswerVisibility(expression) {
        const answers = expression.find('.answer-row');
        const showControls = answers.length > 1;

        answers.each(function () {
            const $row = $(this);
            if (answers.length === 1) {
                $row.find('.select-ans').prop('checked', true);
                // Показываем поля типа и точности для единственного ответа
                $row.find('.meta-fields').show();
                $row.find('.answer-field').css('width', '');
            } else {
                // Скрываем поля типа и точности для множественных ответов
                $row.find('.meta-fields').hide();
                $row.find('.answer-field').css('width', '100%');
            }
            $row.find('.del-ans, .select-ans').toggleClass('hidden', !showControls);
        });
    }

    // Обновление нумерации заданий и id
    function updateAssignmentNumbers() {
        $('.fullExpression').each(function (index) {
            const newId = index + 1;
            $(this).attr('id', `fullExpression${newId}`);
            $(this).find('h3').attr('id', `count${newId}`).text(`Задание №${newId}.`);
            $(this).find('[id^="point_solve"]').attr('id', `point_solve${newId}`);
            $(this).find('[id^="expr"]').attr('id', `expr${newId}`);
        });
    }

    // Добавление нового задания
    $(document).on('click', '#sel-type', function () {
        const $clone = $('.fullExpression').first().clone();
        $clone.find('input').val('');
        $clone.find('math-field').each(function () {
            this.value = '';
        });
        $clone.find('.answer-row').not(':first').remove();
        $clone.find('[id]').removeAttr('id');
        $clone.find('.select-ans').prop('checked', false);
        $clone.find('.type-field').val('');
        $('.butChange').before($clone);
        initMathFields();
        updateAssignmentNumbers();
        updateAnswerVisibility($clone);
    });

    // Добавление варианта ответа
    $(document).on('click', '.btn-add-answer', function () {
        const $expression = $(this).closest('.fullExpression');
        const $clone = $expression.find('.answer-row').first().clone();

        $clone.find('input').val('');
        $clone.find('math-field').each(function () {
            this.value = '';
        });
        $clone.find('.select-ans').prop('checked', false);
        $clone.find('.type-field').val('');

        $expression.find('.answers-container').append($clone);
        updateAnswerVisibility($expression);
        initMathFields();
    });

    // Обработчик фокуса убран - теперь видимость полей управляется количеством ответов

    // Удаление варианта ответа
    $(document).on('click', '.del-ans', function () {
        const $parent = $(this).closest('.fullExpression');
        if ($parent.find('.answer-row').length > 1) {
            $(this).closest('.answer-row').remove();
            updateAnswerVisibility($parent);
        }
    });

    // Удаление задания
    $(document).on('click', '.del-expr', function () {
        if ($('.fullExpression').length > 1) {
            $(this).closest('.fullExpression').remove();
            updateAssignmentNumbers();
        }
    });

    // Удаляем пустые элементы с конца массива
    function removeTrailingEmpty(arr) {
        while (arr.length > 0 && arr[arr.length - 1] === '') {
            arr.pop();
        }
        return arr;
    }

    // Собираем данные перед отправкой
    function collectTestData() {
        const expressions = [];
        const answers = [];
        const trueAnswers = [];
        const epsilons = [];
        const types = [];
        const points = [];
        const boolAnswers = [];

        console.log('Starting data collection...');

        $('.fullExpression').each(function(index) {
            // Выражение и баллы
            const expr = $(this).find('math-field[name="user_expression"]').val() || '';
            const point = $(this).find('input[name="point_solve"]').val() || '0';

            console.log(`Expression ${index + 1}: "${expr}", Points: ${point}`);

            // Списки для одного задания
            let answerList = [];
            let epsilonList = [];
            let typeList = [];
            let boolList = [];

            // Получаем тип от первого ответа (тип един для всего выражения)
            let firstTypeVal = '';

            // Проходим по всем строкам ответа
            $(this).find('.answer-row').each(function(ansIndex) {
                const answerVal = $(this).find('.answer-field').val()?.trim() || '';
                const epsVal    = $(this).find('.accuracy-field').val()?.trim() || '0';
                const typeVal   = $(this).find('.type-field').val()?.trim() || '';
                const isTrue    = $(this).find('.select-ans').is(':checked') ? '1' : '0';

                // Берем тип от первого непустого ответа
                if (answerVal !== '' && !firstTypeVal) {
                    firstTypeVal = typeVal;
                }

                console.log(`  Answer ${ansIndex + 1}: "${answerVal}", Eps: "${epsVal}", Type: "${typeVal}", IsTrue: ${isTrue}`);

                // Если ответ есть, добавляем в массивы (кроме типа)
                if (answerVal !== '') {
                    answerList.push(answerVal);
                    epsilonList.push(epsVal || '0');
                    boolList.push(isTrue);
                }
            });

            // Удаляем пустые в конце (предотвращает лишние ;)
            answerList  = removeTrailingEmpty(answerList);
            epsilonList = removeTrailingEmpty(epsilonList);
            boolList    = removeTrailingEmpty(boolList);

            // Формируем строки
            const exist_select = answerList.length > 1 ? 1 : 0;
            const ansString    = exist_select ? answerList.join(';') : (answerList[0] || '');
            const epsString    = exist_select ? epsilonList.join(';') : (epsilonList[0] || '0');
            const typeString   = firstTypeVal; // Тип един для всего выражения
            const boolString   = exist_select ? boolList.join(';') : (boolList[0] || '0');

            console.log(`  Final strings - Ans: "${ansString}", Eps: "${epsString}", Type: "${typeString}", Bool: "${boolString}"`);

            // Сохраняем в массивы
            expressions.push(expr);
            points.push(point);
            answers.push(ansString);
            epsilons.push(epsString);
            types.push(typeString);
            boolAnswers.push(boolString);
        });

        console.log('Final arrays:', {
            expressions,
            answers,
            epsilons,
            types,
            boolAnswers,
            points
        });

        // Присваиваем скрытым полям
        $('#hidden_expr1').val(JSON.stringify(expressions));
        $('#hidden_point_solve1').val(JSON.stringify(points));
        $('#hidden_ans1').val(JSON.stringify(answers));
        $('#hidden_eps1').val(JSON.stringify(epsilons));
        $('#hidden_type1').val(JSON.stringify(types));
        $('#hidden_bool_ans1').val(JSON.stringify(boolAnswers));

        // Остальные скрытые поля
        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_description_test').val($('#description_test').val());
        $('#hidden_subj_test').val($('#subj_test').val());
        $('#hidden_num_attempts').val($('#num_attempts').val());

        // Время в формате HH:MM:SS
        const h = String(parseInt($('#hours').val() || '0')).padStart(2,'0');
        const m = String(parseInt($('#minutes').val() || '0')).padStart(2,'0');
        const s = String(parseInt($('#seconds').val() || '0')).padStart(2,'0');
        $('#hidden_time_solve').val(`${h}:${m}:${s}`);
    }

    // Проверка корректности времени
    function isValidTime() {
        let valid = true;
        $('.time-input').removeClass('invalid');

        const h = parseInt($('#hours').val()) || 0;
        const m = parseInt($('#minutes').val()) || 0;
        const s = parseInt($('#seconds').val()) || 0;

        if (h < 0)      { $('#hours').addClass('invalid'); valid = false; }
        if (m < 0 || m > 59) { $('#minutes').addClass('invalid'); valid = false; }
        if (s < 0 || s > 59) { $('#seconds').addClass('invalid'); valid = false; }

        return valid;
    }

    // Добавляем стиль для ошибок времени
    $('<style>')
        .prop('type', 'text/css')
        .html('.invalid { border-color: red !important; background-color: #ffe6e6 !important; }')
        .appendTo('head');

    // Инициализация видимости кнопок при загрузке страницы
    $('.fullExpression').each(function() {
        updateAnswerVisibility($(this));
    });

    // Перед сохранением собираем данные и проверяем время
    $(document).on('click', '.save-and-go-to-list', function(e) {
        if (!isValidTime()) {
            e.preventDefault();
            alert("Пожалуйста, введите корректное время (часы ≥ 0, минуты и секунды от 0 до 59).");
            return;
        }
        collectTestData();
    });
});