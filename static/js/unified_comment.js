// 🎯 Унифицированная отправка комментариев для всех разделов проекта "Беседка"
// Работает с любой <form class="comment-form" action="..."> внутри детальных страниц.
// Требует кнопки submit внутри формы.

document.addEventListener('DOMContentLoaded', () => {
  document.body.addEventListener('submit', async (e) => {
    const form = e.target.closest('.comment-form');
    if (!form) return;
    e.preventDefault();

    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    const url = form.action;
    const formData = new FormData(form);

    // Получаем CSRF-токен (приоритет: cookie, затем скрытое поле формы)
    const getCookie = (name) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return '';
    };
    let csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
      csrfToken = formData.get('csrfmiddlewaretoken') || '';
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
        body: formData,
        credentials: 'same-origin',
      });

      let data;
      try {
        data = await response.json();
      } catch (parseErr) {
        throw new Error('Ошибка сервера');
      }

      if (!response.ok || !data.success) {
        const errorMsg = (data && (data.errors || data.error || data.message)) ?
          (typeof data.errors === 'object' ? Object.values(data.errors).flat().join(' ') : data.errors) :
          'Ошибка при отправке комментария';
        alert(errorMsg);
        return;
      }

      // Успешно
      // Обновляем список комментариев, если сервер вернул html
      if (data.comments_html) {
        const container = document.getElementById('comments-container');
        if (container) container.innerHTML = data.comments_html;
      }

      // Скроллим к новому/ответному комментарию
      if (data.comment_id) {
        const newCommentEl = document.getElementById(`comment-${data.comment_id}`);
        if (newCommentEl) {
          newCommentEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }

      form.reset();

      // Обновляем счётчик комментариев в hero-секции / мета-статистике
      if (data.comments_count !== undefined) {
        document.querySelectorAll('.js-comments-count').forEach(el => {
          el.textContent = data.comments_count;
        });
      }

      // Скрываем блок информации о ответе и очищаем parent_id
      const parentInput = form.querySelector('input[name="parent_id"]');
      if (parentInput) parentInput.value = '';
      const replyInfo = form.querySelector('#reply-info');
      if (replyInfo) replyInfo.style.display = 'none';
    } catch (err) {
      console.error(err);
      alert('Ошибка сети при отправке комментария');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    }
  });
});

// ==== Универсальная обработка кнопок «Ответить» и отмены ответа ====
// Работает со структурой, где в .comment-form есть скрытое поле input[name="parent_id"]
// и блок #reply-info с <span id="reply-author"> и кнопкой #cancel-reply.

// Делегируем клики на весь документ, чтобы обработчик работал для динамически
// загруженного HTML (например, после AJAX перерисовки списка комментариев).

document.addEventListener('click', (e) => {
  // Кнопка «Ответить»
  const replyBtn = e.target.closest('.reply-btn');
  if (replyBtn) {
    e.preventDefault();
    const commentId = replyBtn.dataset.commentId;
    const author = replyBtn.dataset.author || '';

    const form = document.querySelector('.comment-form');
    if (!form) return;

    // Записываем parent_id
    const parentInput = form.querySelector('input[name="parent_id"]');
    if (parentInput) parentInput.value = commentId;

    // Показываем инфо о том, на чей комментарий отвечаем
    const replyInfo = form.querySelector('#reply-info');
    const replyAuthorSpan = form.querySelector('#reply-author');
    if (replyInfo) replyInfo.style.display = 'block';
    if (replyAuthorSpan) replyAuthorSpan.textContent = author;

    // Скроллим форму в видимую область и фокусируем textarea
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const textarea = form.querySelector('textarea[name="text"], textarea');
    if (textarea) textarea.focus();
    return;
  }

  // Кнопка «Отменить»
  const cancelBtn = e.target.closest('#cancel-reply');
  if (cancelBtn) {
    e.preventDefault();
    const form = cancelBtn.closest('.comment-form');
    if (!form) return;

    const parentInput = form.querySelector('input[name="parent_id"]');
    if (parentInput) parentInput.value = '';

    const replyInfo = form.querySelector('#reply-info');
    if (replyInfo) replyInfo.style.display = 'none';
  }
});

// ==== ПОДГРУЗКА ДОПОЛНИТЕЛЬНЫХ КОММЕНТАРИЕВ ====

document.addEventListener('click', async (e) => {
  const loadMoreBtn = e.target.closest('.load-more-comments');
  if (!loadMoreBtn) return;

  e.preventDefault();
  const objectType = loadMoreBtn.dataset.objectType;
  const objectId = loadMoreBtn.dataset.objectId;
  let nextPage = parseInt(loadMoreBtn.dataset.nextPage || '2', 10);

  if (!objectType || !objectId) return;

  loadMoreBtn.disabled = true;
  loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  try {
    const params = new URLSearchParams({type: objectType, id: objectId, page: nextPage});
    const response = await fetch(`/ajax/comments/?${params.toString()}`, {
      method: 'GET',
      headers: {'X-Requested-With': 'XMLHttpRequest'},
      credentials: 'same-origin',
    });

    // Новый блок: если ответа нет (404/500 и т.д.)
    if (!response.ok) {
      // Если комментариев больше нет или страница не найдена, удаляем кнопку, чтобы не раздражать пользователя
      if (response.status === 404) {
        loadMoreBtn.remove();
      } else {
        alert('Ошибка загрузки комментариев');
        loadMoreBtn.disabled = false;
      }
      return;
    }

    const data = await response.json();

    if (data.success) {
      const container = document.getElementById('comments-container');
      if (container) {
        container.insertAdjacentHTML('beforeend', data.comments_html);
      }
      if (data.has_next) {
        loadMoreBtn.dataset.nextPage = data.next_page;
        loadMoreBtn.disabled = false;
        loadMoreBtn.innerHTML = '<i class="fas fa-comments me-1"></i> Показать ещё';
      } else {
        loadMoreBtn.remove();
      }
    } else {
      alert(data.message || 'Ошибка загрузки');
      loadMoreBtn.disabled = false;
    }
  } catch (err) {
    console.error(err);
    alert('Ошибка сети');
    loadMoreBtn.disabled = false;
  }
});
