let deleteSlug = null; // Для хранения slug теста

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-btn").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            deleteSlug = this.getAttribute("data-slug");
            showPopup();
        });
    });

    document.getElementById("confirmDelete").addEventListener("click", function () {
        deleteTest();
    });

    document.getElementById("cancelDelete").addEventListener("click", function () {
        hidePopup();
    });
});

function showPopup() {
    document.getElementById("deletePopup").style.display = "block";
}

function hidePopup() {
    document.getElementById("deletePopup").style.display = "none";
}

function deleteTest() {
    fetch(`/delete-test/${deleteSlug}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Обновляем страницу после удаления
        } else {
            alert("Ошибка: " + data.error);
        }
    });
}

// Функция для получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    document.cookie.split(';').forEach(cookie => {
        let trimmed = cookie.trim();
        if (trimmed.startsWith(name + '=')) {
            cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
        }
    });
    return cookieValue;
}


function toggleMenu() {
    let sidebar = document.getElementById('sidebar');
    sidebar.style.display = (sidebar.style.display === 'block') ? 'none' : 'block';
}