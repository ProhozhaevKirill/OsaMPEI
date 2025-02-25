function submitForm() {
    const mathFields = document.querySelectorAll('.answer');
    mathFields.forEach((mathField, index) => {
        const value = mathField.getValue('latex');
        document.getElementById(`hidden-answer-${index + 1}`).value = value;
    });

    document.getElementById('answerForm').submit();
}
