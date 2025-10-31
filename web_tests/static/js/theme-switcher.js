document.addEventListener('DOMContentLoaded', function() {
    // Применяем тему сразу при загрузке страницы
    const currentTheme = document.body.getAttribute('data-user-theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);

    // Обработчик переключения темы
    const themeToggles = document.querySelectorAll('input[name="theme"]');
    themeToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);

            // Показываем индикатор загрузки
            const statusSpan = this.closest('.setting-item').querySelector('span:last-child');
            if (statusSpan) {
                statusSpan.textContent = 'Сохранение...';
            }

            // Отправляем форму
            this.form.submit();
        });
    });
});