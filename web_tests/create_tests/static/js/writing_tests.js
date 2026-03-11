$(document).ready(function () {
    MathfieldElement.locale = 'ru';

    if (window.MathfieldElement) {
        window.MathfieldElement.fontsDirectory = '/static/libs/mathlive/fonts/';
    }

    // Инъекция CSS в shadow DOM для ограничения ширины контейнера MathLive
    function injectShadowStyles(mf) {
        if (mf.dataset.shadowStyled) return;
        mf.dataset.shadowStyled = 'true';
        const tryInject = () => {
            const sr = mf.shadowRoot;
            if (!sr) { setTimeout(tryInject, 50); return; }
            const style = document.createElement('style');
            style.textContent = '.ML__container { max-width: 100% !important; overflow-x: auto !important; box-sizing: border-box !important; }';
            sr.appendChild(style);
        };
        tryInject();
    }

    // Добавляет Enter как синоним Alt+Enter (addRowAfter) через keybindings MathLive
    function setEnterKeybinding(mf) {
        if (mf.dataset.enterInit) return;
        mf.dataset.enterInit = 'true';
        setTimeout(() => {
            const existing = mf.keybindings || [];
            mf.setOptions({
                keybindings: [
                    { key: '[Enter]', ifMode: 'math', command: 'addRowAfter' },
                    ...existing
                ]
            });
        }, 50);
    }

    // Инициализация MathLive-полей (как в старой версии)
    function initMathFields() {
        document.querySelectorAll('math-field').forEach(mf => {
            if (!mf.mathfield) {
                new MathfieldElement(mf);  // Простая инициализация
            }
            injectShadowStyles(mf);
            setEnterKeybinding(mf);
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

    // Показывать/скрывать поле нормы матрицы, поле ответа и поле погрешности
    function toggleNormField($answerRow) {
        const $typeField = $answerRow.find('.type-field');
        const $normField = $answerRow.find('.norm-field');
        const $answerField = $answerRow.find('.answer-field');
        const $accuracyField = $answerRow.find('.accuracy-field');
        const $freeNote = $answerRow.find('.free-answer-note');
        const selectedTypeCode = parseInt($typeField.find('option:selected').data('type-code')) || 0;

        if (selectedTypeCode === 5) { // Свободный ответ
            $answerField.hide();
            $accuracyField.hide();
            $normField.hide();
            $freeNote.show();
        } else if (selectedTypeCode === 4) { // Матрицы
            $answerField.show();
            $accuracyField.show();
            $freeNote.hide();
            $normField.show();
            $answerField.css({ 'height': '170px', 'min-height': '100px' });
        } else {
            $answerField.show();
            $accuracyField.show();
            $freeNote.hide();
            $normField.hide();
            $answerField.css({ 'height': '', 'min-height': '' });
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

                // Определяем тип вопроса - тестовый или обычный
                const isTestQuestion = $(this).find('.select-ans:not(.hidden)').length > 0;
                let firstAnswerType = '';
                let firstAnswerEps = '';
                let firstAnswerNorm = '';

                $(this).find('.answer-row').each(function (answerIndex) {
                    console.log(`    Обрабатываю ответ ${answerIndex + 1}`);

                    // Получаем значение из math-field для ответа
                    const $answerField = $(this).find('.answer-field');
                    const typeVal = $(this).find('.type-field').val() || '';
                    const selectedTypeCode = parseInt($(this).find('.type-field option:selected').data('type-code')) || 0;
                    const isFreeAnswer = selectedTypeCode === 5;

                    // Для свободного ответа используем плейсхолдер, т.к. поле ответа скрыто
                    const answerVal = isFreeAnswer ? '__FREE__' : getMathFieldValue($answerField).trim();

                    const epsVal = $(this).find('.accuracy-field').val() || '';
                    const normVal = $(this).find('.norm-field').val() || '';
                    const isTrue = $(this).find('.select-ans').is(':checked') ? '1' : '0';

                    console.log(`      Ответ: "${answerVal}", Тип: "${typeVal}", Правильный: ${isTrue}, Свободный: ${isFreeAnswer}`);

                    if (answerVal !== '') {
                        answerList.push(answerVal);
                        boolList.push(isTrue);

                        // Для тестовых вопросов берем тип, точность и норму только из первого ответа
                        if (isTestQuestion) {
                            if (answerIndex === 0) {
                                firstAnswerType = typeVal;
                                firstAnswerEps = epsVal;
                                firstAnswerNorm = normVal;
                            }
                            // Для всех ответов тестового вопроса используем данные первого ответа
                            epsilonList.push(firstAnswerEps);
                            typeList.push(firstAnswerType);
                            normList.push(firstAnswerNorm);
                        } else {
                            // Для обычных вопросов используем данные каждого ответа
                            epsilonList.push(epsVal);
                            typeList.push(typeVal);
                            normList.push(normVal);
                        }
                    }
                });

                if (answerList.length === 0) {
                    console.log(`    Пропускаю вариант без ответов`);
                    return; // Пропускаем варианты без ответов
                }

                // Для тестовых вопросов проверяем, что есть хотя бы один правильный ответ
                if (isTestQuestion) {
                    const hasCorrectAnswer = boolList.some(val => val === '1');
                    if (!hasCorrectAnswer) {
                        console.log(`    Внимание: У тестового вопроса нет правильного ответа, помечаем первый как правильный`);
                        if (boolList.length > 0) {
                            boolList[0] = '1';
                        }
                    }
                }

                console.log(`    Найдено ответов: ${answerList.length}, тестовый вопрос: ${isTestQuestion}`);

                // Добавляем данные в общие массивы
                expressions.push(expr);
                points.push(groupPoints);
                blockNumbers.push(blockNum);           // block_expression_num (номер задания) - одинаковый для всех вариантов задания
                variantNumbers.push(variantIndex + 1); // number (номер варианта внутри задания) - 1,2,3...

                // Форматируем ответы как в старой системе
                const exist_select = answerList.length > 1;
                const ansString = exist_select ? answerList.join(';') : (answerList[0] || '');
                const epsString = exist_select ? epsilonList.join(';') : (epsilonList[0] || '');
                const boolString = exist_select ? boolList.join(';') : (boolList[0] || '');

                // Для типов и норм всегда берем значение из первого ответа (не массив)
                const typeValue = firstAnswerType || typeList[0] || '';
                const normValue = firstAnswerNorm || normList[0] || '';

                // Проверяем, что тип ответа обязательно выбран
                if (!typeValue || typeValue === '') {
                    console.log(`    Пропускаю вариант без выбранного типа ответа`);
                    return; // Пропускаем варианты без типа ответа
                }

                answers.push(ansString);
                epsilons.push(epsString);
                types.push(typeValue);  // Одиночное значение, не строка с ;
                norms.push(normValue);  // Одиночное значение, не строка с ;
                boolAnswers.push(boolString);

                console.log(`    Добавлен вариант с выражением: "${expr}", блок: ${blockNum}, номер варианта: ${variantIndex + 1}`);
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

        // Добавляем новые поля для номеров блоков и вариантов
        // Удаляем старые скрытые поля если они есть
        $('input[name="number"]').remove();
        $('input[name="block_expression_num"]').remove();

        $('#testForm').append('<input type="hidden" name="number" value=\'' + JSON.stringify(variantNumbers) + '\'>');
        $('#testForm').append('<input type="hidden" name="block_expression_num" value=\'' + JSON.stringify(blockNumbers) + '\'>');

        // Остальные скрытые поля
        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_description_test').val($('#description_test').val());
        $('#hidden_subj_test').val($('#subj_test').val());
        $('#hidden_num_attempts').val($('#num_attempts').val());
        $('#hidden_result_display_mode').val($('#result_display_mode').val());

        // Критерии оценивания
        $('#hidden_grade_5_threshold').val($('#grade_5_threshold').val() || '80');
        $('#hidden_grade_4_threshold').val($('#grade_4_threshold').val() || '60');
        $('#hidden_grade_3_threshold').val($('#grade_3_threshold').val() || '35');

        const h = String(parseInt($('#hours').val() || '0')).padStart(2, '0');
        const m = String(parseInt($('#minutes').val() || '0')).padStart(2, '0');
        $('#hidden_time_solve').val(`${h}:${m}:00`);

        console.log('Данные собраны и помещены в скрытые поля (старый формат)');
    }

    // Проверка корректности времени
    function isValidTime() {
        let valid = true;
        $('.time-input').removeClass('invalid');

        const h = parseInt($('#hours').val()) || 0;
        const m = parseInt($('#minutes').val()) || 0;

        if (h < 0) { $('#hours').addClass('invalid'); valid = false; }
        if (m < 0 || m > 59) { $('#minutes').addClass('invalid'); valid = false; }

        return valid;
    }

    // Валидация всех полей формы
    function validateFormFields() {
        let isValid = true;

        // Убираем предыдущие ошибки
        $('.wide-input, .time-input, math-field').removeClass('invalid');

        // Проверяем название теста
        const testName = $('#testNameInput').val().trim();
        if (!testName) {
            $('#testNameInput').addClass('invalid');
            isValid = false;
        }

        // Проверяем предмет
        const subject = $('#subj_test').val();
        if (!subject) {
            $('#subj_test').addClass('invalid');
            isValid = false;
        }

        // Проверяем время
        const hours = parseInt($('#hours').val()) || 0;
        const minutes = parseInt($('#minutes').val()) || 0;
        if (hours === 0 && minutes === 0) {
            $('#hours, #minutes').addClass('invalid');
            isValid = false;
        }

        // Проверяем количество попыток
        const attempts = $('#num_attempts').val().trim();
        if (!attempts || parseInt(attempts) <= 0) {
            $('#num_attempts').addClass('invalid');
            isValid = false;
        }

        // Проверяем баллы за задания
        $('.task-group').each(function() {
            const points = $(this).find('[id^="group_points"]').val().trim();
            if (!points || parseFloat(points) <= 0) {
                $(this).find('[id^="group_points"]').addClass('invalid');
                isValid = false;
            }
        });

        // Проверяем заполненность математических полей
        $('.task-group').each(function() {
            const expression = $(this).find('[id^="expr"]')[0];
            if (expression && (!expression.value || expression.value.trim() === '')) {
                $(expression).addClass('invalid');
                isValid = false;
            }

            // Проверяем ответы (пропускаем для свободного ответа)
            $(this).find('.answer-field').each(function() {
                const typeCode = parseInt($(this).closest('.answer-row').find('.type-field option:selected').data('type-code')) || 0;
                if (typeCode === 5) return; // свободный ответ — поле не нужно
                if (!this.value || this.value.trim() === '') {
                    $(this).addClass('invalid');
                    isValid = false;
                }
            });

            // Проверяем точность (пропускаем для свободного ответа)
            $(this).find('.accuracy-field').each(function() {
                const typeCode = parseInt($(this).closest('.answer-row').find('.type-field option:selected').data('type-code')) || 0;
                if (typeCode === 5) return; // свободный ответ — точность не нужна
                const accuracy = $(this).val().trim();
                if (!accuracy) {
                    $(this).addClass('invalid');
                    isValid = false;
                }
            });

            // Проверяем выбор типа ответа
            $(this).find('.type-field').each(function() {
                const typeValue = $(this).val();
                if (!typeValue || typeValue === '') {
                    $(this).addClass('invalid');
                    isValid = false;
                }
            });
        });

        return isValid;
    }

    // Добавляем стиль для ошибок времени
    $('<style>')
        .prop('type', 'text/css')
        .html(`.invalid { border-color: red !important; background-color: #ffe6e6 !important; }`)
        .appendTo('head');

    // Перед сохранением собираем данные и проверяем время
    $(document).on('click', '.save-and-go-to-list', function (e) {
        console.log('Save button clicked!');

        if (!validateFormFields()) {
            e.preventDefault();
            alert("Пожалуйста, заполните все обязательные поля (отмечены красной рамкой).");
            return;
        }

        if (!isValidTime()) {
            e.preventDefault();
            alert("Пожалуйста, введите корректное время (часы ≥ 0, минуты от 0 до 59).");
            return;
        }

        // Собираем данные перед отправкой
        collectTestData();
    });

    // Обработчики для ползунков критериев оценивания
    $('#grade_5_threshold').on('input', function() {
        const value = $(this).val();
        $('#grade_5_value').text(value + '%');

        // Автоматически корректируем другие критерии если нужно
        const grade4 = parseInt($('#grade_4_threshold').val());
        const grade3 = parseInt($('#grade_3_threshold').val());

        if (parseInt(value) <= grade4) {
            const newGrade4 = Math.max(parseInt(value) - 5, 30);
            $('#grade_4_threshold').val(newGrade4);
            $('#grade_4_value').text(newGrade4 + '%');
        }

        if (parseInt(value) <= grade3) {
            const newGrade3 = Math.max(parseInt(value) - 10, 10);
            $('#grade_3_threshold').val(newGrade3);
            $('#grade_3_value').text(newGrade3 + '%');
        }
    });

    $('#grade_4_threshold').on('input', function() {
        const value = $(this).val();
        $('#grade_4_value').text(value + '%');

        // Автоматически корректируем другие критерии если нужно
        const grade5 = parseInt($('#grade_5_threshold').val());
        const grade3 = parseInt($('#grade_3_threshold').val());

        if (parseInt(value) >= grade5) {
            const newGrade5 = Math.min(parseInt(value) + 5, 100);
            $('#grade_5_threshold').val(newGrade5);
            $('#grade_5_value').text(newGrade5 + '%');
        }

        if (parseInt(value) <= grade3) {
            const newGrade3 = Math.max(parseInt(value) - 5, 10);
            $('#grade_3_threshold').val(newGrade3);
            $('#grade_3_value').text(newGrade3 + '%');
        }
    });

    $('#grade_3_threshold').on('input', function() {
        const value = $(this).val();
        $('#grade_3_value').text(value + '%');

        // Автоматически корректируем другие критерии если нужно
        const grade5 = parseInt($('#grade_5_threshold').val());
        const grade4 = parseInt($('#grade_4_threshold').val());

        if (parseInt(value) >= grade4) {
            const newGrade4 = Math.min(parseInt(value) + 5, 90);
            $('#grade_4_threshold').val(newGrade4);
            $('#grade_4_value').text(newGrade4 + '%');
        }

        if (parseInt(value) >= grade5) {
            const newGrade5 = Math.min(parseInt(value) + 10, 100);
            $('#grade_5_threshold').val(newGrade5);
            $('#grade_5_value').text(newGrade5 + '%');
        }
    });

    // ===================== DRAFT SYSTEM =====================

    const DRAFT_LS_KEY = 'wt_draft_' + (window.DRAFT_SLUG || 'new');

    function serializeFormState() {
        const state = { meta: {}, groups: [] };

        state.meta = {
            name: $('#testNameInput').val() || '',
            subj: $('#subj_test').val() || '',
            hours: $('#hours').val() || '',
            minutes: $('#minutes').val() || '',
            attempts: $('#num_attempts').val() || '',
            description: $('#description_test').val() || '',
            result_display_mode: $('#result_display_mode').val() || 'only_score',
            grade_5: $('#grade_5_threshold').val() || '80',
            grade_4: $('#grade_4_threshold').val() || '60',
            grade_3: $('#grade_3_threshold').val() || '35',
        };

        $('.task-group').each(function () {
            const group = { points: $(this).find('[name="group_points"]').val() || '', variants: [] };

            $(this).find('.task-variant').each(function () {
                const $exprField = $(this).find('math-field[name="user_expression"]');
                const variant = {
                    expression: $exprField[0] ? ($exprField[0].value || '') : '',
                    answers: []
                };
                $(this).find('.answer-row').each(function () {
                    const $ansField = $(this).find('.answer-field');
                    variant.answers.push({
                        value: $ansField[0] ? ($ansField[0].value || '') : '',
                        epsilon: $(this).find('.accuracy-field').val() || '',
                        type: $(this).find('.type-field').val() || '',
                        norm: $(this).find('.norm-field').val() || '',
                        isCorrect: $(this).find('.select-ans').is(':checked')
                    });
                });
                group.variants.push(variant);
            });

            state.groups.push(group);
        });

        return state;
    }

    function restoreFormState(state) {
        if (!state || typeof state !== 'object') return;

        if (state.meta) {
            const m = state.meta;
            if (m.name) $('#testNameInput').val(m.name);
            if (m.subj) $('#subj_test').val(m.subj);
            if (m.hours) $('#hours').val(m.hours);
            if (m.minutes) $('#minutes').val(m.minutes);
            if (m.attempts) $('#num_attempts').val(m.attempts);
            if (m.description) $('#description_test').val(m.description);
            if (m.result_display_mode) $('#result_display_mode').val(m.result_display_mode);
            if (m.grade_5) { $('#grade_5_threshold').val(m.grade_5); $('#grade_5_value').text(m.grade_5 + '%'); }
            if (m.grade_4) { $('#grade_4_threshold').val(m.grade_4); $('#grade_4_value').text(m.grade_4 + '%'); }
            if (m.grade_3) { $('#grade_3_threshold').val(m.grade_3); $('#grade_3_value').text(m.grade_3 + '%'); }
        }

        if (!state.groups || !state.groups.length) return;

        const $container = $('#taskGroupsContainer');
        const $tplGroup = $container.find('.task-group').first();
        $container.find('.task-group').not(':first').remove();

        const mathQueue = [];

        state.groups.forEach(function (groupData, groupIdx) {
            let $group = groupIdx === 0 ? $tplGroup : (function () {
                const $g = $tplGroup.clone();
                $g.find('input').val('');
                $g.find('math-field').each(function () { this.value = ''; });
                $g.find('.task-variant').not(':first').remove();
                $g.find('.answer-row').not(':first').remove();
                $g.find('[id]').removeAttr('id');
                $g.removeClass('active');
                $container.append($g);
                return $g;
            })();

            $group.find('[name="group_points"]').val(groupData.points || '');
            $group.find('.task-variant').not(':first').remove();
            const $tplVariant = $group.find('.task-variant').first();

            (groupData.variants || []).forEach(function (variantData, variantIdx) {
                let $variant = variantIdx === 0 ? $tplVariant : (function () {
                    const $v = $tplVariant.clone();
                    $v.find('input').val('');
                    $v.find('math-field').each(function () { this.value = ''; });
                    $v.find('.answer-row').not(':first').remove();
                    $v.find('[id]').removeAttr('id');
                    $group.find('.task-variants-container').append($v);
                    return $v;
                })();

                const $exprField = $variant.find('math-field[name="user_expression"]');
                if ($exprField[0] && variantData.expression) {
                    mathQueue.push({ el: $exprField[0], val: variantData.expression });
                }

                $variant.find('.answer-row').not(':first').remove();
                const $tplAnswer = $variant.find('.answer-row').first();

                (variantData.answers || []).forEach(function (answerData, answerIdx) {
                    let $answer = answerIdx === 0 ? $tplAnswer : (function () {
                        const $a = $tplAnswer.clone();
                        $a.find('math-field').each(function () { this.value = ''; });
                        $a.find('input').val('');
                        $variant.find('.answers-container').append($a);
                        return $a;
                    })();

                    const $ansField = $answer.find('.answer-field');
                    if ($ansField[0] && answerData.value) {
                        mathQueue.push({ el: $ansField[0], val: answerData.value });
                    }
                    $answer.find('.accuracy-field').val(answerData.epsilon || '');
                    $answer.find('.type-field').val(answerData.type || '');
                    $answer.find('.norm-field').val(answerData.norm || '');
                    $answer.find('.select-ans').prop('checked', answerData.isCorrect || false);
                    toggleNormField($answer);
                });

                updateAnswerVisibility($variant);
            });

            updateVariantVisibility($group);
        });

        initMathFields();
        updateTaskGroupNumbers();
        updateTaskMap();
        switchToTask(1);

        setTimeout(function () {
            mathQueue.forEach(function (item) {
                try { item.el.value = item.val; } catch (e) {}
            });
        }, 600);
    }

    // Авто-сохранение в localStorage
    let draftSaveTimer = null;
    function scheduleDraftSave() {
        clearTimeout(draftSaveTimer);
        draftSaveTimer = setTimeout(function () {
            try { localStorage.setItem(DRAFT_LS_KEY, JSON.stringify(serializeFormState())); } catch (e) {}
        }, 2000);
    }
    $(document).on('input change', 'input:not([type=hidden]), select, textarea', scheduleDraftSave);
    $(document).on('input', 'math-field', scheduleDraftSave);

    // Восстановление при загрузке
    setTimeout(function () {
        if (window.DRAFT_DATA && typeof window.DRAFT_DATA === 'object') {
            restoreFormState(window.DRAFT_DATA);
            return;
        }
        try {
            const saved = localStorage.getItem(DRAFT_LS_KEY);
            if (saved) {
                const state = JSON.parse(saved);
                if (state && (state.meta || state.groups)) restoreFormState(state);
            }
        } catch (e) {}
    }, 400);

    // Очистка localStorage при успешном сохранении
    $(document).on('click', '.save-and-go-to-list', function () {
        setTimeout(function () { localStorage.removeItem(DRAFT_LS_KEY); }, 100);
    });

    // Кнопка "Сохранить черновик"
    $(document).on('click', '#save-draft-btn', function (e) {
        e.preventDefault();
        const state = serializeFormState();
        $('#hidden_draft_state').val(JSON.stringify(state));
        $('#hidden_is_draft').val('true');
        $('#hidden_name_test').val($('#testNameInput').val() || 'Черновик');
        const h = String(parseInt($('#hours').val() || '1')).padStart(2, '0');
        const m = String(parseInt($('#minutes').val() || '30')).padStart(2, '0');
        $('#hidden_time_solve').val(h + ':' + m + ':00');
        $('#hidden_num_attempts').val($('#num_attempts').val() || '1');
        $('#hidden_subj_test').val($('#subj_test').val() || '');
        $('#hidden_description_test').val($('#description_test').val() || '');
        $('#hidden_result_display_mode').val($('#result_display_mode').val() || 'only_score');
        $('#hidden_grade_5_threshold').val($('#grade_5_threshold').val() || '80');
        $('#hidden_grade_4_threshold').val($('#grade_4_threshold').val() || '60');
        $('#hidden_grade_3_threshold').val($('#grade_3_threshold').val() || '35');
        localStorage.removeItem(DRAFT_LS_KEY);
        $('#testForm').submit();
    });
});