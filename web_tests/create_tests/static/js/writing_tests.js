$(document).ready(function () {
    MathfieldElement.locale = 'ru';

    // Инициализация MathLive-полей
    function initMathFields() {
        document.querySelectorAll('math-field').forEach(mf => {
            if (!mf.mathfield) {
                console.warn("MathLive field not initialized properly");
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

        // Скрыть поля типа и точности и расширить поле ответа
        $clone.find('.meta-fields').hide();
        $clone.find('.answer-field').css('width', '100%');

        $expression.find('.answers-container').append($clone);
        updateAnswerVisibility($expression);
        initMathFields();
    });

    // Показать тип и точность при фокусе на поле ответа
    $(document).on('focus', '.answer-field', function () {
        const $metaFields = $(this).closest('.answer-content').find('.meta-fields');
        $metaFields.show();
        $(this).css('width', '');
    });

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

        $('.fullExpression').each(function () {
            const expr = $(this).find('math-field[name="user_expression"]').val() || '';
            const point = $(this).find('input[name="point_solve"]').val() || '0';

            let answerList = [];
            let epsilonList = [];
            let typeList = [];
            let boolList = [];

            $(this).find('.answer-row').each(function () {
                const answerVal = $(this).find('.answer-field').val().trim();
                const epsVal = $(this).find('.accuracy-field').val().trim();
                const typeVal = $(this).find('.type-field').val().trim();
                const isTrue = $(this).find('.select-ans').is(':checked') ? '1' : '0';

                if (answerVal !== '') {
                    answerList.push(answerVal);
                    epsilonList.push(epsVal);
                    typeList.push(typeVal);
                    boolList.push(isTrue);
                }
            });

            answerList = removeTrailingEmpty(answerList);
            epsilonList = removeTrailingEmpty(epsilonList);
            typeList = removeTrailingEmpty(typeList);
            boolList = removeTrailingEmpty(boolList);

            const exist_select = answerList.length > 1 ? 1 : 0;
            const ansString = exist_select ? answerList.join(';') : (answerList[0] || '');
            const epsString = exist_select ? epsilonList.join(';') : (epsilonList[0] || '');
            const typeString = exist_select ? typeList.join(';') : (typeList[0] || '');
            const boolString = exist_select ? boolList.join(';') : (boolList[0] || '');

            expressions.push(expr);
            points.push(point);
            answers.push(ansString);
            epsilons.push(epsString);
            types.push(typeString);
            boolAnswers.push(boolString);
        });

        return {
            expressions: expressions,
            points: points,
            answers: answers,
            epsilons: epsilons,
            types: types,
            boolAnswers: boolAnswers
        };
    }

    // Заполнение скрытых полей данными
    function fillHiddenFields() {
        const data = collectTestData();

        $('#hidden_expr1').val(JSON.stringify(data.expressions));
        $('#hidden_point_solve1').val(JSON.stringify(data.points));
        $('#hidden_ans1').val(JSON.stringify(data.answers));
        $('#hidden_eps1').val(JSON.stringify(data.epsilons));
        $('#hidden_type1').val(JSON.stringify(data.types));
        $('#hidden_bool_ans1').val(JSON.stringify(data.boolAnswers));

        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_description_test').val($('#description_test').val());
        $('#hidden_subj_test').val($('#subj_test').val());
        $('#hidden_num_attempts').val($('#num_attempts').val());

        const h = String(parseInt($('#hours').val() || '0')).padStart(2, '0');
        const m = String(parseInt($('#minutes').val() || '0')).padStart(2, '0');
        const s = String(parseInt($('#seconds').val() || '0')).padStart(2, '0');
        $('#hidden_time_solve').val(`${h}:${m}:${s}`);
    }

    // Проверка корректности времени
    function isValidTime() {
        let valid = true;
        $('.time-input').removeClass('invalid');

        const h = parseInt($('#hours').val()) || 0;
        const m = parseInt($('#minutes').val()) || 0;
        const s = parseInt($('#seconds').val()) || 0;

        if (h < 0) { $('#hours').addClass('invalid'); valid = false; }
        if (m < 0 || m > 59) { $('#minutes').addClass('invalid'); valid = false; }
        if (s < 0 || s > 59) { $('#seconds').addClass('invalid'); valid = false; }

        return valid;
    }

    // Добавляем стиль для ошибок времени
    $('<style>')
        .prop('type', 'text/css')
        .html(`.invalid { border-color: red !important; background-color: #ffe6e6 !important; }`)
        .appendTo('head');

    // Перед сохранением собираем данные и проверяем время
    $(document).on('click', '.save-and-go-to-list', function (e) {
        if (!isValidTime()) {
            e.preventDefault();
            alert("Пожалуйста, введите корректное время (часы ≥ 0, минуты и секунды от 0 до 59).");
            return;
        }
        fillHiddenFields();
    });

    // === Черновик: начало ===

    // Флаг сохранения
    let isSaved = false;
    let isFormChanged = false;

    // Отслеживание изменений в форме
    $(document).on('input change', 'input, select, math-field', function() {
        isFormChanged = true;
        isSaved = false;
    });

    // Функция сохранения черновика
    function saveAsDraft() {
        const data = collectTestData();

        // Подготавливаем данные для отправки
        const formData = new FormData();
        formData.append('name_test', $('#testNameInput').val() || 'Черновик');
        formData.append('description_test', $('#description_test').val() || '');
                formData.append('subj_test', $('#subj_test').val() || '');
        formData.append('num_attempts', $('#num_attempts').val() || 1);

        const h = String(parseInt($('#hours').val() || '0')).padStart(2, '0');
        const m = String(parseInt($('#minutes').val() || '0')).padStart(2, '0');
        const s = String(parseInt($('#seconds').val() || '0')).padStart(2, '0');
        formData.append('time_to_solution', `${h}:${m}:${s}`);

        formData.append('expressions', JSON.stringify(data.expressions));
        formData.append('points', JSON.stringify(data.points));
        formData.append('answers', JSON.stringify(data.answers));
        formData.append('epsilons', JSON.stringify(data.epsilons));
        formData.append('types', JSON.stringify(data.types));
        formData.append('boolAnswers', JSON.stringify(data.boolAnswers));

        // Флаг черновика
        formData.append('is_draft', '1');

        $.ajax({
            url: '/your-save-draft-endpoint/',  // Замените на ваш URL для сохранения черновика
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (response) {
                isSaved = true;
                isFormChanged = false;
                console.log('Черновик сохранен');
            },
            error: function (xhr) {
                console.error('Ошибка при сохранении черновика', xhr);
            }
        });
    }

    // Периодическое сохранение черновика
    setInterval(function () {
        if (isFormChanged && !isSaved) {
            saveAsDraft();
        }
    }, 10000); // каждые 10 секунд

    // Восстановление черновика при загрузке (если нужно)
    function restoreDraft(draftData) {
        if (!draftData) return;

        $('#testNameInput').val(draftData.name_test);
        $('#description_test').val(draftData.description_test);
        $('#subj_test').val(draftData.subj_test);
        $('#num_attempts').val(draftData.num_attempts);

        const [h, m, s] = (draftData.time_to_solution || '01:30:00').split(':');
        $('#hours').val(parseInt(h));
        $('#minutes').val(parseInt(m));
        $('#seconds').val(parseInt(s));

        const exprs = JSON.parse(draftData.expressions || '[]');
        const points = JSON.parse(draftData.points || '[]');
        const answers = JSON.parse(draftData.answers || '[]');
        const epsilons = JSON.parse(draftData.epsilons || '[]');
        const types = JSON.parse(draftData.types || '[]');
        const bools = JSON.parse(draftData.boolAnswers || '[]');

        $('.fullExpression').not(':first').remove();
        const $first = $('.fullExpression').first();
        for (let i = 0; i < exprs.length; i++) {
            const $exprBlock = (i === 0) ? $first : $first.clone();
            $exprBlock.find('math-field[name="user_expression"]').val(exprs[i]);
            $exprBlock.find('input[name="point_solve"]').val(points[i] || '0');

            const ansList = (answers[i] || '').split(';');
            const epsList = (epsilons[i] || '').split(';');
            const typeList = (types[i] || '').split(';');
            const boolList = (bools[i] || '').split(';');

            const $ansContainer = $exprBlock.find('.answers-container');
            $ansContainer.find('.answer-row').not(':first').remove();
            const $firstAns = $ansContainer.find('.answer-row').first();

            ansList.forEach((ans, j) => {
                const $ansRow = (j === 0) ? $firstAns : $firstAns.clone();
                $ansRow.find('.answer-field').val(ans);
                $ansRow.find('.accuracy-field').val(epsList[j] || '');
                $ansRow.find('.type-field').val(typeList[j] || '');
                $ansRow.find('.select-ans').prop('checked', boolList[j] === '1');
                if (j > 0) {
                    $ansContainer.append($ansRow);
                }
            });

            if (i > 0) {
                $('.butChange').before($exprBlock);
            }
        }

        updateAssignmentNumbers();
        initMathFields();
    }

    // === Черновик: конец ===
});
