// Простая логика для демонстрации
document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для кнопки уведомлений
    document.querySelector('.notifications-btn').addEventListener('click', function() {
        alert('Здесь будут ваши уведомления');
    });

    // Анимация карточек при загрузке
    const cards = document.querySelectorAll('.stat-card, .test-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});