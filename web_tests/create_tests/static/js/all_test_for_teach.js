document.addEventListener('DOMContentLoaded', function() {
    // Инициализация фильтров из URL параметров
    initializeFiltersFromURL();

    // Элементы модальных окон
    const deleteModal = document.getElementById('deleteModal');
    const publishModal = document.getElementById('publishModal');
    const modalOverlay = document.querySelector('.modal-overlay');
    const closeModalButtons = document.querySelectorAll('.close-modal');

    // Элементы управления
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const unpublishButtons = document.querySelectorAll('.unpublish-btn');
    const publishButtons = document.querySelectorAll('.publish-btn');
    const confirmDeleteBtn = document.querySelector('.confirm-delete');
    const cancelDeleteBtn = document.querySelector('.cancel-delete');
    const confirmPublishBtn = document.querySelector('.confirm-publish');
    const cancelPublishBtn = document.querySelector('.cancel-publish');

    let currentTestSlug = null;

    // Функции управления модальными окнами
    function openModal(modal) {
        modal.classList.add('active');
        modalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal(modal) {
        modal.classList.remove('active');
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';

        // Очищаем выбранные группы при закрытии модального окна публикации
        if (modal === publishModal) {
            document.querySelectorAll('.group-checkbox:checked').forEach(checkbox => {
                checkbox.checked = false;
            });
            document.querySelectorAll('.group-item.selected').forEach(item => {
                item.classList.remove('selected');
            });
        }
    }

    // Обработчики удаления теста
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            currentTestSlug = this.getAttribute('data-slug');
            openModal(deleteModal);
        });
    });

    confirmDeleteBtn.addEventListener('click', function() {
        if (currentTestSlug) {
            const deleteUrl = document.querySelector(`.delete-btn[data-slug="${currentTestSlug}"]`).dataset.url;

            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Ошибка сети');
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    showError(deleteModal, data.error || 'Ошибка при удалении теста');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError(deleteModal, 'Произошла ошибка при удалении теста');
            });
        }
    });

    cancelDeleteBtn.addEventListener('click', () => closeModal(deleteModal));

    // Обработчики публикации теста
    publishButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            currentTestSlug = this.getAttribute('data-slug');
            // Инициализируем выбор групп и фильтрацию при открытии модального окна
            initializeGroupSelection();
            initializeFiltering();
            openModal(publishModal);
        });
    });

    confirmPublishBtn.addEventListener('click', function() {
        console.log('Confirm publish button clicked');

        const selectedGroups = Array.from(document.querySelectorAll('.group-checkbox:checked'));
        const selectedGroupIds = selectedGroups.map(checkbox => checkbox.value);
        const publishBtn = document.querySelector(`.publish-btn[data-slug="${currentTestSlug}"]`);
        const publishUrl = publishBtn ? publishBtn.dataset.url : null;

        console.log('Current test slug:', currentTestSlug);
        console.log('Selected groups:', selectedGroupIds);
        console.log('Publish URL:', publishUrl);

        if (!currentTestSlug) {
            showError(publishModal, 'Не выбран тест для публикации');
            return;
        }

        if (!publishUrl) {
            showError(publishModal, 'Не найден URL для публикации');
            return;
        }

        if (selectedGroupIds.length === 0) {
            showError(publishModal, 'Выберите хотя бы одну группу');
            return;
        }

        console.log('Sending publish request...');

        fetch(publishUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ groups: selectedGroupIds })
        })
        .then(response => {
            console.log('Response received:', response.status, response.statusText);
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                window.location.reload();
            } else {
                showError(publishModal, data.error || 'Ошибка публикации теста');
            }
        })
        .catch(error => {
            console.error('Publish error:', error);
            showError(publishModal, 'Произошла ошибка при публикации теста');
        });
    });

    cancelPublishBtn.addEventListener('click', () => closeModal(publishModal));

    // Обработчики снятия с публикации
    unpublishButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;

            if (confirm("Вы уверены, что хотите снять тест с публикации?")) {
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Инициализация выбора групп
    function initializeGroupSelection() {
        console.log('Initializing group selection...');

        // Очищаем предыдущие слушатели событий
        document.querySelectorAll('.institute-header').forEach(header => {
            const newHeader = header.cloneNode(true);
            header.parentNode.replaceChild(newHeader, header);
        });

        document.querySelectorAll('.institute-header').forEach(header => {
            header.style.cursor = 'pointer';

            header.addEventListener('click', function(e) {
                if (e.target.classList.contains('group-checkbox') ||
                    e.target.tagName === 'LABEL' ||
                    e.target.tagName === 'INPUT') return;

                const card = this.closest('.institute-card');
                const toggleBtn = this.querySelector('.btn-toggle');
                toggleGroups(card, toggleBtn);
            });

            const toggleBtn = header.querySelector('.btn-toggle');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const card = this.closest('.institute-card');
                    toggleGroups(card, this);
                });
            }
        });

        // Очищаем предыдущие слушатели для чекбоксов групп
        document.querySelectorAll('.group-checkbox').forEach(checkbox => {
            const newCheckbox = checkbox.cloneNode(true);
            checkbox.parentNode.replaceChild(newCheckbox, checkbox);
        });

        document.querySelectorAll('.group-item').forEach(item => {
            const checkbox = item.querySelector('.group-checkbox');
            const label = item.querySelector('.form-check-label');
            if (checkbox && label) {
                const groupId = checkbox.value;
                checkbox.id = `group-${groupId}`;
                label.htmlFor = `group-${groupId}`;
            }
        });

        document.querySelectorAll('.group-checkbox').forEach(checkbox => {
            checkbox.addEventListener('click', function(e) {
                e.stopPropagation();
                this.closest('.group-item').classList.toggle('selected', this.checked);
                console.log('Group checkbox clicked:', this.value, this.checked);
            });
        });

        console.log('Group selection initialized, found', document.querySelectorAll('.group-checkbox').length, 'checkboxes');
    }

    // Вспомогательные функции
    function toggleGroups(card, toggleBtn) {
        card.classList.toggle('active');
        const icon = toggleBtn.querySelector('i');
        icon.classList.toggle('fa-chevron-down');
        icon.classList.toggle('fa-chevron-up');
    }

    function showError(modal, message) {
        const oldErrors = modal.querySelectorAll('.alert-error');
        oldErrors.forEach(error => error.remove());

        const errorElement = document.createElement('div');
        errorElement.className = 'alert-error';
        errorElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        modal.querySelector('.modal-body').prepend(errorElement);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Фильтрация тестов
    const filterSelect = document.getElementById('testFilter');
    const testCards = document.querySelectorAll('.test-card');

    filterSelect.addEventListener('change', function() {
        const selectedValue = this.value;
        testCards.forEach(card => {
            const isPublished = card.getAttribute('data-published') === 'true';
            card.classList.toggle('hidden',
                (selectedValue === 'published' && !isPublished) ||
                (selectedValue === 'unpublished' && isPublished) ||
                (selectedValue === 'draft' && isPublished)
            );
        });
    });

    // Закрытие модальных окон
    closeModalButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });

    modalOverlay.addEventListener('click', () => {
        document.querySelectorAll('.modal.active').forEach(modal => closeModal(modal));
    });

    // Функция фильтрации групп
    function filterGroups() {
        const searchTerm = document.getElementById('groupSearch').value.toLowerCase();
        const educationLevel = document.getElementById('educationLevelFilter').value;
        const course = document.getElementById('courseFilter').value;

        document.querySelectorAll('.group-item').forEach(item => {
            const groupName = item.querySelector('.form-check-label').textContent.toLowerCase();
            const itemEducationLevel = item.getAttribute('data-education-level');
            const itemCourse = item.getAttribute('data-course');

            const matchesSearch = groupName.includes(searchTerm);
            const matchesEducationLevel = !educationLevel || itemEducationLevel === educationLevel;
            const matchesCourse = !course || itemCourse === course;

            const shouldShow = matchesSearch && matchesEducationLevel && matchesCourse;
            item.style.display = shouldShow ? 'block' : 'none';
        });

        // Обновляем видимость институтов (скрываем если нет видимых групп)
        document.querySelectorAll('.institute-card').forEach(card => {
            const visibleGroups = card.querySelectorAll('.group-item[style="display: block"], .group-item:not([style*="display: none"])');
            const hasVisibleGroups = visibleGroups.length > 0;
            card.style.display = hasVisibleGroups ? 'block' : 'none';
        });
    }

    // Инициализация поиска и фильтров
    function initializeFiltering() {
        const groupSearch = document.getElementById('groupSearch');
        const educationLevelFilter = document.getElementById('educationLevelFilter');
        const courseFilter = document.getElementById('courseFilter');

        if (groupSearch) {
            groupSearch.addEventListener('input', filterGroups);
        }
        if (educationLevelFilter) {
            educationLevelFilter.addEventListener('change', filterGroups);
        }
        if (courseFilter) {
            courseFilter.addEventListener('change', filterGroups);
        }
    }

    // Инициализация уже выполняется при клике на кнопку публикации
    // Дополнительная инициализация при загрузке страницы
    initializeGroupSelection();
    initializeFiltering();
});

// Функция для инициализации фильтров из URL параметров
function initializeFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const filterType = urlParams.get('filter'); // my или all
    const statusFilter = urlParams.get('status'); // published, unpublished или all

    // Устанавливаем фильтр по автору
    const authorFilter = document.getElementById('authorFilter');
    if (authorFilter && filterType) {
        authorFilter.value = filterType;
    }

    // Устанавливаем фильтр по статусу
    const testFilter = document.getElementById('testFilter');
    if (testFilter && statusFilter) {
        if (statusFilter === 'published') {
            testFilter.value = 'published';
        } else if (statusFilter === 'unpublished') {
            testFilter.value = 'unpublished';
        } else {
            testFilter.value = 'all';
        }

        // Применяем фильтрацию
        applyTestFilter(testFilter.value);
    }
}

// Функция для применения фильтрации тестов
function applyTestFilter(selectedValue) {
    const testCards = document.querySelectorAll('.test-card');
    testCards.forEach(card => {
        const isPublished = card.getAttribute('data-published') === 'true';
        const shouldHide =
            (selectedValue === 'published' && !isPublished) ||
            (selectedValue === 'unpublished' && isPublished) ||
            (selectedValue === 'draft' && isPublished);

        if (shouldHide) {
            card.classList.add('hidden');
            card.style.display = 'none';
        } else {
            card.classList.remove('hidden');
            card.style.display = 'block';
        }
    });
}