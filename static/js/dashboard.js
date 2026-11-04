/**
 * Black Eagles Zipline - Admin Dashboard Interactions
 * Developed for PL SOFT TECH SOLUTIONS
 */

document.addEventListener('DOMContentLoaded', function () {
  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const dashSidebar = document.querySelector('.dash-sidebar');

  if (sidebarToggle && dashSidebar) {
    sidebarToggle.addEventListener('click', function () {
      dashSidebar.classList.toggle('show');
    });
  }

  // Auto-dismiss standard alerts after 5 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
});
