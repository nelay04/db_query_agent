// static/js/sidebar.js

document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('backdrop');
  const reopenSidebarBtn = document.getElementById('reopenSidebarBtn');
  const desktopToggleIcon = document.getElementById('desktopToggleIcon');

  // Mobile: Open Sidebar
  const openSidebarBtn = document.getElementById('openSidebarBtn');
  if (openSidebarBtn) {
    openSidebarBtn.addEventListener('click', () => {
      sidebar.classList.add('open');
      backdrop.classList.remove('hidden');
    });
  }

  // Mobile: Close Sidebar
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.add('hidden');
    });
  }

  // Mobile: Backdrop click
  if (backdrop) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.add('hidden');
    });
  }

  // Desktop: Collapse Sidebar
  const toggleDesktopSidebarBtn = document.getElementById('toggleDesktopSidebarBtn');
  if (toggleDesktopSidebarBtn) {
    toggleDesktopSidebarBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      reopenSidebarBtn.classList.toggle('hidden', !isCollapsed);
      desktopToggleIcon.classList.toggle('fa-arrow-left', !isCollapsed);
      desktopToggleIcon.classList.toggle('fa-arrow-right', isCollapsed);
    });
  }

  // Desktop: Reopen Sidebar
  if (reopenSidebarBtn) {
    reopenSidebarBtn.addEventListener('click', () => {
      sidebar.classList.remove('collapsed');
      reopenSidebarBtn.classList.add('hidden');
      desktopToggleIcon.classList.add('fa-arrow-left');
      desktopToggleIcon.classList.remove('fa-arrow-right');
    });
  }

  // DB Settings Form Submission
  const dbSettingsForm = document.getElementById('dbSettingsForm');
  if (dbSettingsForm) {
    dbSettingsForm.addEventListener('submit', function (e) {
      e.preventDefault();

      const form = e.target;
      const formData = {
        user_email: form.user_email.value,
        db_type: form.dbType.value,
        db_host: form.host.value,
        db_port: form.port.value,
        db_user_name: form.userName.value,
        db_password: form.password.value,
        db_database: form.database.value,
        db_table_name: form.tableName.value,
      };

      const saveSettingsBtn = form.querySelector('button[type="submit"]');
      saveSettingsBtn.disabled = true;
      saveSettingsBtn.textContent = 'Saving...';

      // Using global functions from utils.js
      fetch('/api/db_config/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify(formData),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showCustomToast(data.message || 'Success', 'success');
          } else {
            showCustomToast(data.message || 'Something went wrong', 'error');
          }
        })
        .catch((error) => {
          console.error('Error:', error);
          showCustomToast('Network error. Please try again.', 'error');
        })
        .finally(() => {
          saveSettingsBtn.disabled = false;
          saveSettingsBtn.textContent = 'Save Settings';
        });
    });
  }
});