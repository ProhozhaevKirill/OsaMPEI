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

    // Инициализация карты заданий при загрузке страницы
    updateTaskMap();

    // Убеждаемся, что первое задание активно
    switchToTask(1);

    // Показывать/скрывать кнопки удаления и чекбоксы
    function updateAnswerVisibility(variant) {
        const answers = variant.find('.answer-row');
        const showControls = answers.length > 1;

        answers.each(function () {
            const $row = $(this);
            if (answers.length === 1) {
                $row.find('.select-ans').prop('checked', true);
                // Показываем meta-fields для единственного ответа
                $row.find('.meta-fields').show();
                $row.find('.answer-field').css('width', '');
                // Проверяем нужно ли показать поле нормы
                toggleNormField($row);
                // Скрываем надпись "верный ответ" для единственного ответа
                $row.find('.correct-label').addClass('hidden');
            } else {
                // Скрываем meta-fields для множественных ответов
                $row.find('.meta-fields').hide();
                $row.find('.answer-field').css('width', '100%');
                // Показываем надпись "верный ответ" для множественных ответов
                $row.find('.correct-label').removeClass('hidden');
            }
            // Показываем/скрываем элементы управления ответами (кнопка удаления и чекбокс)
            $row.find('.del-ans, .select-ans').toggleClass('hidden', !showControls);
        });
    }

    // Показывать/скрывать кнопки удаления вариантов
    function updateVariantVisibility(taskGroup) {
        const variants = taskGroup.find('.task-variant');
        const showControls = variants.length > 1;

        variants.each(function () {
            const $variant = $(this);
            $variant.find('.del-variant').toggleClass('hidden', !showControls);
        });
    }

    // Показывать/скрывать поле нормы матрицы и изменять размер поля ответа
    function toggleNormField($answerRow) {
        const $typeField = $answerRow.find('.type-field');
        const $normField = $answerRow.find('.norm-field');
        const $answerField = $answerRow.find('.answer-field');
        const selectedType = $typeField.val();

        if (selectedType === '4') { // ID типа "Матрицы"
            $normField.show();
            $answerField.css({
                'height': '170px',
                'min-height': '100px'
            });
        } else {
            $normField.hide();
            $answerField.css({
                'height': '',
                'min-height': ''
            });
        }
    }

    // Обновление нумерации групп заданий и вариантов
    function updateTaskGroupNumbers() {
        $('.task-group').each(function (groupIndex) {
            const groupId = groupIndex + 1;
            $(this).attr('id', `taskGroup${groupId}`);
            $(this).find('.task-group-number h2').attr('id', `groupCount${groupId}`).text(`Задание №${groupId}`);
            $(this).find('[id^="group_points"]').attr('id', `group_points${groupId}`);

            // Обновляем нумерацию вариантов внутри группы
            $(this).find('.task-variant').each(function (variantIndex) {
                const variantId = variantIndex + 1;
                $(this).attr('id', `variant${groupId}_${variantId}`);
                $(this).find('.variant-left h4').attr('id', `variantCount${groupId}_${variantId}`).text(`Вариант №${variantId}`);
                $(this).find('[id^="expr"]').attr('id', `expr${groupId}_${variantId}`);
            });
        });
    }

    // Функция обновления карты заданий
    function updateTaskMap() {
        const $taskMapContainer = $('#taskMapContainer');
        $taskMapContainer.empty();

        $('.task-group').each(function (index) {
            const taskId = index + 1;
            const $mapItem = $('<div>')
                .addClass('task-map-item')
                .attr('data-task-id', taskId)
                .html(`
                    <div class="task-map-item-content">
                        <span class="task-number">${taskId}</span>
                    </div>
                    <button class="delete-task-btn" title="Удалить задание">
                        <i class="fas fa-times"></i>
                    </button>
                `);

            if (taskId === 1) {
                $mapItem.addClass('active');
            }

            $taskMapContainer.append($mapItem);
        });
    }

    // Функция переключения между заданиями
    function switchToTask(taskId) {
        // Убираем active класс со всех групп и элементов карты
        $('.task-group').removeClass('active');
        $('.task-map-item').removeClass('active');

        // Добавляем active класс к выбранным элементам
        $(`#taskGroup${taskId}`).addClass('active');
        $(`.task-map-item[data-task-id="${taskId}"]`).addClass('active');
    }

    // Обработчик клика по элементам карты заданий
    $(document).on('click', '.task-map-item', function (e) {
        // Проверяем, не был ли клик по кнопке удаления
        if ($(e.target).closest('.delete-task-btn').length === 0) {
            const taskId = $(this).data('task-id');
            switchToTask(taskId);
        }
    });

    // Переменная для хранения ID задания для удаления
    let taskToDelete = null;

    // Обработчик клика по кнопке удаления задания в карте
    $(document).on('click', '.delete-task-btn', function (e) {
        e.stopPropagation(); // Предотвращаем всплытие события

        // Проверяем, есть ли больше одного задания
        if ($('.task-group').length <= 1) {
            return; // Не позволяем удалить последнее задание
        }

        const taskId = $(this).closest('.task-map-item').data('task-id');
        taskToDelete = taskId;

        // Показываем модальное окно
        $('#deleteTaskModal').addClass('active');
    });

    // Обработчик для кнопки "Отмена" в модальном окне
    $(document).on('click', '#cancelDeleteTask', function () {
        $('#deleteTaskModal').removeClass('active');
        taskToDelete = null;
    });

    // Обработчик для кнопки "Удалить" в модальном окне
    $(document).on('click', '#confirmDeleteTask', function () {
        if (taskToDelete && $('.task-group').length > 1) {
            const $taskGroup = $(`#taskGroup${taskToDelete}`);
            const wasActive = $taskGroup.hasClass('active');

            $taskGroup.remove();
            updateTaskGroupNumbers();
            updateTaskMap();

            // Если удалили активное задание, переключаемся на первое
            if (wasActive) {
                switchToTask(1);
            }
        }

        $('#deleteTaskModal').removeClass('active');
        taskToDelete = null;
    });

    // Закрытие модального окна по клику на фон
    $(document).on('click', '#deleteTaskModal', function (e) {
        if (e.target === this) {
            $(this).removeClass('active');
            taskToDelete = null;
        }
    });

    // Добавление новой группы заданий
    $(document).on('click', '#add-task-group', function () {
        const $clone = $('.task-group').first().clone();
        $clone.find('input').val('');
        $clone.find('math-field').each(function () {
            this.value = '';
        });
        $clone.find('.task-variant').not(':first').remove();
        $clone.find('.answer-row').not(':first').remove();
        $clone.find('[id]').removeAttr('id');
        $clone.removeClass('active');

        $('#taskGroupsContainer').append($clone);
        initMathFields();
        updateTaskGroupNumbers();
        updateAnswerVisibility($clone.find('.task-variant').first());
        updateVariantVisibility($clone);
        updateTaskMap();

        // Переключаемся на новое задание
        const newTaskId = $('.task-group').length;
        switchToTask(newTaskId);
    });

    // Добавление варианта задания
    $(document).on('click', '.btn-add-variant', function () {
        const $taskGroup = $(this).closest('.task-group');
        const $clone = $taskGroup.find('.task-variant').first().clone();

        $clone.find('input').val('');
        $clone.find('math-field').each(function () {
            this.value = '';
        });
        $clone.find('.answer-row').not(':first').remove();
        $clone.find('[id]').removeAttr('id');

        $taskGroup.find('.task-variants-container').append($clone);
        initMathFields();
        updateTaskGroupNumbers();
        updateAnswerVisibility($clone);
        updateVariantVisibility($taskGroup);
    });

    // Добавление варианта ответа
    $(document).on('click', '.btn-add-answer', function () {
        const $variant = $(this).closest('.task-variant');
        const $clone = $variant.find('.answer-row').first().clone();

        $clone.find('input').val('');
        $clone.find('math-field').each(function () {
            this.value = '';
        });
        $clone.find('.select-ans').prop('checked', false);

        // Скрыть поля типа и точности и расширить поле ответа
        $clone.find('.meta-fields').hide();
        $clone.find('.answer-field').css('width', '100%');

        $variant.find('.answers-container').append($clone);
        updateAnswerVisibility($variant);
        initMathFields();
    });

    // Обработка изменения типа ответа
    $(document).on('change', '.type-field', function () {
        const $answerRow = $(this).closest('.answer-row');
        toggleNormField($answerRow);
    });

    // Удаление варианта ответа
    $(document).on('click', '.del-ans', function () {
        const $variant = $(this).closest('.task-variant');
        if ($variant.find('.answer-row').length > 1) {
            $(this).closest('.answer-row').remove();
            updateAnswerVisibility($variant);
        }
    });

    // Удаление варианта задания
    $(document).on('click', '.del-variant', function () {
        const $taskGroup = $(this).closest('.task-group');
        if ($taskGroup.find('.task-variant').length > 1) {
            $(this).closest('.task-variant').remove();
            updateTaskGroupNumbers();
            updateVariantVisibility($taskGroup);
        }
    });

    // Удаление группы заданий
    $(document).on('click', '.del-task-group', function (e) {
        e.stopPropagation();

        // Проверяем, есть ли больше одного задания
        if ($('.task-group').length <= 1) {
            return; // Не позволяем удалить последнее задание
        }

        const $taskGroup = $(this).closest('.task-group');
        const taskId = $taskGroup.data('task-id');
        taskToDelete = taskId;

        // Показываем модальное окно
        $('#deleteTaskModal').addClass('active');
    });

    // Удаляем пустые элементы с конца массива
    function removeTrailingEmpty(arr) {
        while (arr.length > 0 && arr[arr.length - 1] === '') {
            arr.pop();
        }
        return arr;
    }

    // Получение значения из math-field элемента
    function getMathFieldValue(element) {
        const mathField = element[0]; // Получаем DOM элемент
        if (mathField && mathField.value !== undefined) {
            return mathField.value;
        }
        return element.val() || '';
    }

    // Собираем данные перед отправкой (старый принцип через массивы)
    function collectTestData() {
        console.log('Начинаю сбор данных...');
        const expressions = [];
        const answers = [];
        const trueAnswers = [];
        const epsilons = [];
        const types = [];
        const norms = [];
        const points = [];
        const boolAnswers = [];
        const blockNumbers = [];
        const variantNumbers = [];

        $('.task-group').each(function (groupIndex) {
            console.log(`Обрабатываю группу ${groupIndex + 1}`);
            const groupPoints = $(this).find('input[name="group_points"]').val() || '1';
            const blockNum = groupIndex + 1; // номер задания

            $(this).find('.task-variant').each(function (variantIndex) {
                console.log(`  Обрабатываю вариант ${variantIndex + 1}`);

                // Получаем значение из math-field для выражения
                const $exprField = $(this).find('math-field[name="user_expression"]');
                const expr = getMathFieldValue($exprField);

                console.log(`    Выражение: "${expr}"`);

                if (!expr || !expr.trim()) {
                    console.log(`    Пропускаю пустой вариант`);
                    return; // Пропускаем пустые варианты
                }

                let answerList = [];
                let epsilonList = [];
                let typeList = [];
                let normList = [];
                let boolList = [];

                $(this).find('.answer-row').each(function (answerIndex) {
                    console.log(`    Обрабатываю ответ ${answerIndex + 1}`);

                    // Получаем значение из math-field для ответа
                    const $answerField = $(this).find('.answer-field');
                    const answerVal = getMathFieldValue($answerField).trim();

                    const epsVal = $(this).find('.accuracy-field').val() || '';
                    const typeVal = $(this).find('.type-field').val() || '';
                    const normVal = $(this).find('.norm-field').val() || '';
                    const isTrue = $(this).find('.select-ans').is(':checked') ? '1' : '0';

                    console.log(`      Ответ: "${answerVal}", Тип: "${typeVal}"`);

                    if (answerVal !== '') {
                        answerList.push(answerVal);
                        epsilonList.push(epsVal);
                        typeList.push(typeVal);
                        normList.push(normVal);
                        boolList.push(isTrue);
                    }
                });

                if (answerList.length === 0) {
                    console.log(`    Пропускаю вариант без ответов`);
                    return; // Пропускаем варианты без ответов
                }

                console.log(`    Найдено ответов: ${answerList.length}`);

                // Добавляем данные в общие массивы
                expressions.push(expr);
                points.push(groupPoints);
                blockNumbers.push(blockNum);           // block_expression_num (номер задания)
                variantNumbers.push(variantIndex + 1); // number (номер варианта)

                // Форматируем ответы как в старой системе
                const exist_select = answerList.length > 1;
                const ansString = exist_select ? answerList.join(';') : (answerList[0] || '');
                const epsString = exist_select ? epsilonList.join(';') : (epsilonList[0] || '');
                const typeString = exist_select ? typeList.join(';') : (typeList[0] || '');
                const normString = exist_select ? normList.join(';') : (normList[0] || '');
                const boolString = exist_select ? boolList.join(';') : (boolList[0] || '');

                answers.push(ansString);
                epsilons.push(epsString);
                types.push(typeString);
                norms.push(normString);
                boolAnswers.push(boolString);

                console.log(`    Добавлен вариант с выражением: "${expr}", блок: ${blockNum}, номер: ${variantIndex + 1}`);
            });
        });

        console.log(`Всего собрано заданий: ${expressions.length}`);
        console.log('Выражения:', expressions);
        console.log('Блоки:', blockNumbers);
        console.log('Номера вариантов:', variantNumbers);

        // Записываем данные в скрытые поля как в старой системе
        $('#hidden_expr1').val(JSON.stringify(expressions));
        $('#hidden_point_solve1').val(JSON.stringify(points));
        $('#hidden_ans1').val(JSON.stringify(answers));
        $('#hidden_eps1').val(JSON.stringify(epsilons));
        $('#hidden_type1').val(JSON.stringify(types));
        $('#hidden_norm1').val(JSON.stringify(norms));
        $('#hidden_bool_ans1').val(JSON.stringify(boolAnswers));

        // Остальные скрытые поля
        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_description_test').val($('#description_test').val());
        $('#hidden_subj_test').val($('#subj_test').val());
        $('#hidden_num_attempts').val($('#num_attempts').val());

        const h = String(parseInt($('#hours').val() || '0')).padStart(2, '0');
        const m = String(parseInt($('#minutes').val() || '0')).padStart(2, '0');
        const s = String(parseInt($('#seconds').val() || '0')).padStart(2, '0');
        $('#hidden_time_solve').val(`${h}:${m}:${s}`);

        console.log('Данные собраны и помещены в скрытые поля (старый формат)');
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
        console.log('Save button clicked!');

        if (!isValidTime()) {
            e.preventDefault();
            alert("Пожалуйста, введите корректное время (часы ≥ 0, минуты и секунды от 0 до 59).");
            return;
        }

        console.log('Time validation passed, collecting data...');
        collectTestData();

        console.log('Data collected, checking hidden fields:');
        console.log('user_expression:', $('#hidden_expr1').val());
        console.log('user_ans:', $('#hidden_ans1').val());
        console.log('user_type:', $('#hidden_type1').val());
        console.log('point_solve:', $('#hidden_point_solve1').val());
        console.log('name_test:', $('#hidden_name_test').val());
        console.log('description_test:', $('#hidden_description_test').val());
        console.log('subj_test:', $('#hidden_subj_test').val());
        console.log('num_attempts:', $('#hidden_num_attempts').val());
        console.log('time_solve:', $('#hidden_time_solve').val());
    });
});