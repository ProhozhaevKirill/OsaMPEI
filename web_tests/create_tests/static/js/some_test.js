document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModal');
    const publishModal = document.getElementById('publishModal');
    const modalOverlay = document.querySelector('.modal-overlay');
    const closeModalButtons = document.querySelectorAll('.close-modal');

    const deleteButtons = document.querySelectorAll('.delete-btn');
    const confirmDeleteBtn = document.querySelector('.confirm-delete');
    const cancelDeleteBtn = document.querySelector('.cancel-delete');
    let currentTestSlug = null;

    const publishButtons = document.querySelectorAll('.publish-btn');
    const confirmPublishBtn = document.querySelector('.confirm-publish');
    const cancelPublishBtn = document.querySelector('.cancel-publish');

    const editButtons = document.querySelectorAll('.edit-btn');

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

    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            currentTestSlug = this.getAttribute('data-slug');
            openModal(deleteModal);
        });
    });

    confirmDeleteBtn.addEventListener('click', function() {
        if (currentTestSlug) {
            fetch(`/TestsCreate/delete-test/${currentTestSlug}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    showError(deleteModal, data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError(deleteModal, 'Произошла ошибка при удалении теста');
            });
        }
    });

    cancelDeleteBtn.addEventListener('click', function() {
        closeModal(deleteModal);
    });

    editButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const slug = this.getAttribute('data-slug');
            if (slug) {
                window.location.href = `/TestsCreate/edit-test/${slug}/`;
            }
        });
    });

    publishButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            currentTestSlug = this.getAttribute('data-slug');
            openModal(publishModal);
        });
    });

    function initializeGroupSelection() {
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
            });
        });
    }

    // Инициализация при открытии модального окна публикации
    publishModal.addEventListener('click', () => initializeGroupSelection(), { once: true });

    confirmPublishBtn.addEventListener('click', function() {
        const selectedGroups = Array.from(document.querySelectorAll('.group-checkbox:checked'));
        const selectedGroupIds = selectedGroups.map(checkbox => checkbox.value);

        if (!currentTestSlug) {
            showError(publishModal, 'Не выбран тест для публикации');
            return;
        }

        if (selectedGroupIds.length === 0) {
            showError(publishModal, 'Выберите хотя бы одну группу');
            return;
        }

        fetch(`/TestsCreate/publish-test/${currentTestSlug}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                groups: selectedGroupIds,
                action: 'publish'
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
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

    cancelPublishBtn.addEventListener('click', function() {
        closeModal(publishModal);
    });

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
});
