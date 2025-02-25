$(document).ready(function() {
    var expressionCount = 1;

    // Отслеживаем нажатие пробела
    function attachHandlersToMathField(mathField) {
        mathField.addEventListener('keydown', (event) => {
            if (event.key === ' ') {
                event.preventDefault();

                let inputVal = mathField.getValue();

                const regex = /([а-яА-ЯёЁ]+)(\s*)$/;
                if (regex.test(inputVal)) {
                    inputVal = inputVal.replace(regex, '\\text{$1}\\ ');
                    mathField.setValue(inputVal);
                } else {
                    mathField.insertText('\\ ');
                }
            }
        });
    }

    const mathFields = document.querySelectorAll('math-field');
    mathFields.forEach((mathField) => {
        attachHandlersToMathField(mathField);
    });

    $('.add-btn').click(function() {
        expressionCount++;
        var newDiv = $('.fullExpression').first().clone();
        newDiv.attr('id', 'fullExpression' + expressionCount);
        newDiv.find('[id^=point_solve]').attr('id', 'point_solve' + expressionCount).val('');
        newDiv.find('[id^=expr]').attr('id', 'expr' + expressionCount).val('');
        newDiv.find('[id^=ans]').attr('id', 'ans' + expressionCount).val('');
        newDiv.find('[id^=eps]').attr('id', 'eps' + expressionCount).val('');
        newDiv.find('[id^=typ]').attr('id', 'typ' + expressionCount).val('');
        newDiv.find('[id^=count]').attr('id', 'count' + expressionCount).text('Задание №' + expressionCount + '.');
        newDiv.appendTo('.container').insertBefore('.butChange');

        // console.log('point_solve1 value:', $('#point_solve1').val());

        const newMathField = newDiv.find('math-field');
        newMathField.each(function() {
            attachHandlersToMathField(this);
        });
    });

    $('.del-btn').click(function() {
        if (expressionCount > 1) {
            $('#fullExpression' + expressionCount).remove();
            expressionCount--;
        }
    });

    function updateFormFields() {
        let point = [];
        let expressions = [];
        let answers = [];
        let epsilons = [];
        let types = [];

        for (let i = 1; i <= expressionCount; i++) {
            point.push($('#point_solve' + i).val());
            expressions.push($('#expr' + i).val());
            answers.push($('#ans' + i).val());
            epsilons.push($('#eps' + i).val());
            types.push($('#typ' + i).val());
        }

        $('#hidden_name_test').val($('#testNameInput').val());
        $('#hidden_time_solve').val($('#timeSolve').val());

        $('#hidden_point_solve1').val(JSON.stringify(point));
        $('#hidden_expr1').val(JSON.stringify(expressions));
        $('#hidden_ans1').val(JSON.stringify(answers));
        $('#hidden_eps1').val(JSON.stringify(epsilons));
        $('#hidden_typ1').val(JSON.stringify(types));
    }

    $('.save-and-go-to-list').on('click', function(e) {
        updateFormFields();
    });

    $('#menuButton').click(function(event) {
        event.stopPropagation();
        $('#menu').toggle(200); // Плавное появление/исчезновение
    });

    $(document).click(function(event) {
        if (!$(event.target).closest('.dropdown').length) {
            $('#menu').fadeOut(200);
        }
    });

});
