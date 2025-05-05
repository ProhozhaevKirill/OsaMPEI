document.addEventListener('DOMContentLoaded', function() {
    // Элементы управления
    const profileBtn = document.getElementById('profileBtn');
    const profileMenu = document.getElementById('profileMenu');
    const notificationsBtn = document.getElementById('notificationsBtn');
    const notificationsMenu = document.getElementById('notificationsMenu');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const closeMenuBtn = document.getElementById('closeMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileOverlay = document.getElementById('mobileOverlay');

    // Переключение меню профиля
    profileBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        profileMenu.classList.toggle('hidden');
        notificationsMenu.classList.add('hidden');

        // Добавляем/удаляем класс active для родительского элемента
        this.parentElement.classList.toggle('active');
    });

    // Переключение меню уведомлений
    notificationsBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationsMenu.classList.toggle('hidden');
        profileMenu.classList.add('hidden');

        // Добавляем/удаляем класс active для родительского элемента
        this.parentElement.classList.toggle('active');
    });

    // Открытие мобильного меню
    mobileMenuBtn.addEventListener('click', function() {
        mobileMenu.classList.remove('hidden');
        mobileOverlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    });

    // Закрытие мобильного меню
    closeMenuBtn.addEventListener('click', function() {
        mobileMenu.classList.add('hidden');
        mobileOverlay.classList.add('hidden');
        document.body.style.overflow = '';
    });

    // Закрытие мобильного меню при клике на оверлей
    mobileOverlay.addEventListener('click', function() {
        mobileMenu.classList.add('hidden');
        this.classList.add('hidden');
        document.body.style.overflow = '';
    });

    // Закрытие выпадающих меню при клике вне их
    document.addEventListener('click', function() {
        profileMenu.classList.add('hidden');
        notificationsMenu.classList.add('hidden');

        // Удаляем класс active у родительских элементов
        document.querySelectorAll('.profile-dropdown, .notifications-dropdown').forEach(el => {
            el.classList.remove('active');
        });
    });

    // Предотвращаем закрытие при клике внутри меню
    profileMenu.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    notificationsMenu.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Закрытие меню при нажатии ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            profileMenu.classList.add('hidden');
            notificationsMenu.classList.add('hidden');
            mobileMenu.classList.add('hidden');
            mobileOverlay.classList.add('hidden');
            document.body.style.overflow = '';

            // Удаляем класс active у родительских элементов
            document.querySelectorAll('.profile-dropdown, .notifications-dropdown').forEach(el => {
                el.classList.remove('active');
            });
        }
    });

    // Анимация при загрузке страницы
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 50);
});