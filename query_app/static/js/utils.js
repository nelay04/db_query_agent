// static/js/utils.js

/**
 * Displays a custom toast notification.
 * @param {string} message - The message to display.
 * @param {'success'|'error'} [type='success'] - The type of toast (e.g., 'success', 'error').
 */
function showCustomToast(message, type = 'success') {
  const toastContainer = document.getElementById('customToastContainer');
  if (!toastContainer) {
    console.error('Toast container not found!');
    return;
  }

  const toast = document.createElement('div');
  toast.classList.add('custom-toast');
  toast.classList.add(`custom-toast-${type}`);

  const messageElement = document.createElement('div');
  messageElement.classList.add('custom-toast-message');
  messageElement.textContent = message;

  toast.appendChild(messageElement);
  toastContainer.appendChild(toast);

  // Automatically remove the toast after a few seconds
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

/**
 * Retrieves the CSRF token from the document cookies.
 * @returns {string|null} The CSRF token string, or null if not found.
 */
function getCSRFToken() {
  let cookieValue = null;
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      cookieValue = decodeURIComponent(value);
      break;
    }
  }
  return cookieValue;
}