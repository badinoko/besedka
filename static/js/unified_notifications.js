(function () {
  /**
   * Глобальная функция показа уведомлений.
   * Использует Bootstrap 5 Toast API и контейнер
   * <div id="global-toast-container"> … </div> уже присутствующий в base.html.
   *
   * @param {string} message  Текст уведомления
   * @param {string} [type]   info | success | error (по умолчанию info)
   */
  window.showNotification = function (message, type = 'info') {
    try {
      // Находим или создаём контейнер для toast-уведомлений
      let container = document.getElementById('global-toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'global-toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
      }

      // Определяем Bootstrap цветовую схему по типу уведомления
      const typeMap = {
        success: 'success',
        error: 'danger',
        info: 'info'
      };
      const bsColor = typeMap[type] || 'info';

      // Создаём элемент Toast
      const toastEl = document.createElement('div');
      toastEl.className = `toast align-items-center text-white bg-${bsColor} border-0`;
      toastEl.setAttribute('role', 'alert');
      toastEl.setAttribute('aria-live', 'assertive');
      toastEl.setAttribute('aria-atomic', 'true');

      toastEl.innerHTML = `
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>`;

      container.appendChild(toastEl);

      // Инициализируем и показываем Toast (delay 3000 мс)
      const toast = bootstrap.Toast ? new bootstrap.Toast(toastEl, { delay: 3000 }) : null;
      if (toast) {
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
      } else {
        // Если Bootstrap ещё не загружен, fallback на простое исчезновение
        toastEl.style.opacity = '0';
        setTimeout(() => toastEl.remove(), 3000);
      }
    } catch (e) {
      // В крайних случаях выводим сообщение в консоль
      console.error('Не удалось отобразить уведомление:', e, message);
    }
  };
})();
