/**
 * Black Eagles Zipline - Admin Dashboard Interactions
 * Developed for PL SOFT TECH SOLUTIONS
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle & Backdrop
  const sidebarToggle = document.getElementById('sidebarToggle');
  const dashSidebar = document.querySelector('.dash-sidebar');

  let backdrop = document.querySelector('.sidebar-backdrop');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.className = 'sidebar-backdrop';
    document.body.appendChild(backdrop);
  }

  function openSidebar() {
    if (dashSidebar) dashSidebar.classList.add('show');
    if (backdrop) backdrop.classList.add('show');
  }

  function closeSidebar() {
    if (dashSidebar) dashSidebar.classList.remove('show');
    if (backdrop) backdrop.classList.remove('show');
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (dashSidebar && dashSidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  // 2. Settings Tab Navigation System
  const tabButtons = document.querySelectorAll('.settings-tab-btn');
  const tabPanes = document.querySelectorAll('.settings-pane');

  if (tabButtons.length > 0 && tabPanes.length > 0) {
    tabButtons.forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('data-target');

        tabButtons.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));

        this.classList.add('active');
        const targetPane = document.getElementById(targetId);
        if (targetPane) {
          targetPane.classList.add('active');
        }
      });
    });
  }

  // 3. Auto-dismiss standard alerts after 5 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {
        // Ignored if closed manually
      }
    }, 5000);
  });
});
