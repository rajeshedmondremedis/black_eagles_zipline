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
        const targetId = this.getAttribute('data-tab') || this.getAttribute('data-target');

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

  // 3. Spotlight Search Palette (Ctrl+K / Cmd+K)
  const spotlightModalEl = document.getElementById('spotlightModal');
  const spotlightInput = document.getElementById('spotlightInput');
  const spotlightResults = document.getElementById('spotlightResults');
  let spotlightModal = null;

  if (spotlightModalEl && window.bootstrap) {
    spotlightModal = new bootstrap.Modal(spotlightModalEl);

    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        spotlightModal.show();
        setTimeout(() => spotlightInput && spotlightInput.focus(), 250);
      }
    });

    const triggerBtn = document.getElementById('spotlightTriggerBtn');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', function () {
        spotlightModal.show();
        setTimeout(() => spotlightInput && spotlightInput.focus(), 250);
      });
    }

    if (spotlightInput && spotlightResults) {
      let debounceTimer = null;
      spotlightInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        if (query.length < 2) {
          spotlightResults.innerHTML = `
            <div class="text-center text-muted py-4 small">
              <i class="bi bi-keyboard fs-3 d-block mb-1 text-secondary"></i>
              Type at least 2 characters to search bookings...
            </div>
          `;
          return;
        }

        debounceTimer = setTimeout(() => {
          fetch(`/admin-panel/api/search/?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
              if (!data.results || data.results.length === 0) {
                spotlightResults.innerHTML = `
                  <div class="text-center text-muted py-4 small">
                    <i class="bi bi-search fs-3 d-block mb-1 text-secondary"></i>
                    No reservations found matching "<strong>${query}</strong>"
                  </div>
                `;
                return;
              }

              let html = '<div class="list-group list-group-flush">';
              data.results.forEach(item => {
                const isConfirmed = item.status === 'CONFIRMED';
                const badgeClass = isConfirmed ? 'badge-status-confirmed' : 'badge-status-cancelled';
                html += `
                  <a href="${item.url}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center p-3 rounded-3 mb-2" style="background: var(--c-card-bg); border: 1px solid var(--c-border); color: var(--c-primary-text); text-decoration: none;">
                    <div>
                      <div class="d-flex align-items-center gap-2 mb-1">
                        <strong class="text-orange">${item.reference}</strong>
                        <span class="badge-status ${badgeClass}" style="font-size: 0.68rem; padding: 0.2rem 0.5rem;">${item.status}</span>
                      </div>
                      <div class="text-white fw-bold">${item.name} <span class="text-muted small">(${item.mobile})</span></div>
                      <div class="small text-muted"><i class="bi bi-calendar-event me-1"></i> ${item.date} • ${item.slot} (${item.slot_time}) • ${item.members} Pax</div>
                    </div>
                    <i class="bi bi-chevron-right text-muted"></i>
                  </a>
                `;
              });
              html += '</div>';
              spotlightResults.innerHTML = html;
            })
            .catch(() => {
              spotlightResults.innerHTML = '<div class="text-danger text-center py-3 small">Search request failed.</div>';
            });
        }, 220);
      });
    }
  }

  // 4. Auto-dismiss standard alerts after 5 seconds
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
