document.addEventListener('DOMContentLoaded', function() {
    // Элементы модальных окон
    const deleteModal = document.getElementById('deleteModal');
    const publishModal = document.getElementById('publishModal');
    const modalOverlay = document.querySelector('.modal-overlay');
    const closeModalButtons = document.querySelectorAll('.close-modal');
    
    // Элементы для удаления теста
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const confirmDeleteBtn = document.querySelector('.confirm-delete');
    const cancelDeleteBtn = document.querySelector('.cancel-delete');
    let currentTestSlug = null;
    
    // Элементы для публикации теста
    const publishButtons = document.querySelectorAll('.publish-btn');
    const unpublishButtons = document.querySelectorAll('.unpublish-btn');
    const confirmPublishBtn = document.querySelector('.confirm-publish');
    const cancelPublishBtn = document.querySelector('.cancel-publish');
    const testAvailability = document.getElementById('testAvailability');
    const groupsSection = document.getElementById('groupsSection');
    
    // Поиск и фильтрация
    const testSearch = document.getElementById('testSearch');
    const testFilter = document.getElementById('testFilter');
    const groupSearch = document.getElementById('groupSearch');
    const instituteFilter = document.getElementById('instituteFilter');
    
    // Институты и группы
    const instituteCards = document.querySelectorAll('.institute-card');
    const toggleButtons = document.querySelectorAll('.btn-toggle');
    
    // Функции для работы с модальными окнами
    function openModal(modal) {
        modal.classList.add('active');
        modalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeModal(modal) {
        modal.classList.remove('active');
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Обработчики для модального окна удаления
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentTestSlug = this.getAttribute('data-slug');
            openModal(deleteModal);
        });
    });
    
    confirmDeleteBtn.addEventListener('click', function() {
        if (currentTestSlug) {
            fetch(`/delete-test/${currentTestSlug}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при удалении теста');
            });
        }
        closeModal(deleteModal);
    });
    
    cancelDeleteBtn.addEventListener('click', function() {
        closeModal(deleteModal);
    });
    
    // Обработчики для модального окна публикации
    publishButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentTestSlug = this.getAttribute('data-slug');
            openModal(publishModal);
        });
    });
    
    unpublishButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentTestSlug = this.getAttribute('data-slug');
            if (confirm('Вы уверены, что хотите снять тест с публикации? Студенты больше не смогут его проходить.')) {
                fetch(`/unpublish-test/${currentTestSlug}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Произошла ошибка при снятии теста с публикации');
                });
            }
        });
    });
    
    testAvailability.addEventListener('change', function() {
        if (this.value === 'selected') {
            groupsSection.style.display = 'block';
        } else {
            groupsSection.style.display = 'none';
        }
    });
    
    confirmPublishBtn.addEventListener('click', function() {
        if (!currentTestSlug) return;
        
        const timeLimit = document.getElementById('testTimeLimit').value;
        const attempts = document.getElementById('testAttempts').value;
        const startDate = document.getElementById('testStartDate').value;
        const endDate = document.getElementById('testEndDate').value;
        const availableToAll = testAvailability.value === 'all';
        
        let selectedGroups = [];
        if (!availableToAll) {
            document.querySelectorAll('.group-checkbox:checked').forEach(checkbox => {
                selectedGroups.push(checkbox.value);
            });
            
            if (selectedGroups.length === 0) {
                alert('Выберите хотя бы одну группу для публикации теста');
                return;
            }
        }
        
        const data = {
            time_limit: timeLimit,
            attempts: attempts,
            start_date: startDate,
            end_date: endDate,
            available_to_all: availableToAll,
            groups: selectedGroups
        };
        
        fetch(`/publish-test/${currentTestSlug}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Произошла ошибка при публикации теста');
        });
        
        closeModal(publishModal);
    });
    
    cancelPublishBtn.addEventListener('click', function() {
        closeModal(publishModal);
    });
    
    // Обработчики закрытия модальных окон
    closeModalButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    modalOverlay.addEventListener('click', function() {
        document.querySelectorAll('.modal.active').forEach(modal => {
            closeModal(modal);
        });
    });
    
    // Обработчики для институтов и групп
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.institute-card');
            card.classList.toggle('active');
        });
    });
    
    // Поиск тестов
    testSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const filterValue = testFilter.value;
        
        document.querySelectorAll('.test-card').forEach(card => {
            const title = card.querySelector('.test-title a').textContent.toLowerCase();
            const isPublished = card.getAttribute('data-published') === 'true';
            
            const matchesSearch = title.includes(searchTerm);
            let matchesFilter = true;
            
            if (filterValue === 'published' && !isPublished) {
                matchesFilter = false;
            } else if (filterValue === 'unpublished' && isPublished) {
                matchesFilter = false;
            }
            
            if (matchesSearch && matchesFilter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
    
    // Фильтрация тестов
    testFilter.addEventListener('change', function() {
        testSearch.dispatchEvent(new Event('input'));
    });
    
    // Поиск групп
    groupSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const instituteId = instituteFilter.value;
        
        document.querySelectorAll('.group-item').forEach(item => {
            const groupName = item.querySelector('.form-check-label').textContent.toLowerCase();
            const instituteCard = item.closest('.institute-card');
            const currentInstituteId = instituteCard.getAttribute('data-id');
            
            const matchesSearch = groupName.includes(searchTerm);
            const matchesInstitute = instituteId === 'all' || currentInstituteId === instituteId;
            
            if (matchesSearch && matchesInstitute) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Фильтрация по институтам
    instituteFilter.addEventListener('change', function() {
        groupSearch.dispatchEvent(new Event('input'));
    });
    
    // Функция для получения CSRF-токена
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
});