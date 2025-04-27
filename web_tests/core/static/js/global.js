document.addEventListener('DOMContentLoaded', function () {
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  const profileBtn = document.getElementById('profile-btn');
  const profileMenu = document.getElementById('profile-menu');

  menuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('hidden');
    menuToggle.classList.toggle('active'); // используешь 'active' — логично и понятно
  });

  profileBtn.addEventListener('click', () => {
    profileMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', (event) => {
    if (!profileBtn.contains(event.target) && !profileMenu.contains(event.target)) {
      profileMenu.classList.add('hidden');
    }
  });
});
