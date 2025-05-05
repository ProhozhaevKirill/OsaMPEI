document.addEventListener('DOMContentLoaded', function() {
    // Элементы модального окна
    const modal = document.getElementById('testInfoModal');
    const modalOverlay = document.querySelector('.modal-overlay');
    const closeModalButtons = document.querySelectorAll('.close-modal');

    // Кнопки "Подробнее"
    const infoButtons = document.querySelectorAll('.info-btn');

    // Поиск и фильтрация
    const testSearch = document.getElementById('testSearch');
    const testFilter = document.getElementById('testFilter');

    // Открытие модального окна
    infoButtons.forEach(button => {
        button.addEventListener('click', function() {
            const testId = this.getAttribute('data-test-id');
            const testCard = this.closest('.test-card');

            // Заполняем модальное окно данными (здесь можно добавить AJAX запрос)
            document.getElementById('modalTestTitle').textContent = testCard.querySelector('.test-title a').textContent;

            const description = testCard.querySelector('.test-description');
            document.getElementById('modalTestDescription').textContent = description ? description.textContent : 'Описание отсутствует';

            const time = testCard.querySelector('.test-meta span:nth-child(1)').textContent;
            document.getElementById('modalTestTime').textContent = time;

            const attempts = testCard.querySelector('.test-meta span:nth-child(2)').textContent;
            document.getElementById('modalTestAttempts').textContent = attempts;

            // Пример данных (можно заменить на реальные)
            document.getElementById('modalTestDeadline').textContent = 'до 15.12.2023';

            // Устанавливаем ссылку на тест
            document.getElementById('modalStartBtn').href = testCard.querySelector('.test-title a').href;

            // Показываем модальное окно
            modal.classList.add('active');
            modalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    // Закрытие модального окна
    closeModalButtons.forEach(button => {
        button.addEventListener('click', function() {
            modal.classList.remove('active');
            modalOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    });

    modalOverlay.addEventListener('click', function() {
        modal.classList.remove('active');
        this.classList.remove('active');
        document.body.style.overflow = '';
    });

    // Поиск тестов
    testSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const filterValue = testFilter.value;

        document.querySelectorAll('.test-card').forEach(card => {
            const title = card.querySelector('.test-title a').textContent.toLowerCase();
            const isCompleted = card.dataset.completed === 'true';
            const isNew = card.dataset.new === 'true';

            const matchesSearch = title.includes(searchTerm);
            let matchesFilter = true;

            if (filterValue === 'uncompleted' && isCompleted) {
                matchesFilter = false;
            } else if (filterValue === 'completed' && !isCompleted) {
                matchesFilter = false;
            } else if (filterValue === 'new' && !isNew) {
                matchesFilter = false;
            }

            if (matchesSearch && matchesFilter) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    });

    // Фильтрация тестов
    testFilter.addEventListener('change', function() {
        testSearch.dispatchEvent(new Event('input'));
    });

    // Закрытие при нажатии ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
            modalOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
});