document.addEventListener('DOMContentLoaded', function() {
    // Элементы
    const selectAllCheckbox = document.getElementById('selectAll');
    const notificationCheckboxes = document.querySelectorAll('.notification-checkbox');
    const markSelectedReadBtn = document.getElementById('markSelectedRead');
    const deleteSelectedBtn = document.getElementById('deleteSelected');
    const markAllReadBtn = document.getElementById('markAllRead');
    const filterTabs = document.querySelectorAll('.filter-tab');
    const notificationCards = document.querySelectorAll('.notification-item');

    // Функция обновления счетчиков
    function updateAllCounters(serverUnreadCount = null, serverTotalCount = null) {
        console.log('[DEBUG] updateAllCounters called with:', {
            serverUnreadCount: serverUnreadCount,
            serverTotalCount: serverTotalCount
        });

        // Считаем только ВИДИМЫЕ карточки (не скрытые фильтрами)
        const visibleCards = document.querySelectorAll('.notification-item:not([style*="display: none"])');
        const visibleUnreadCards = document.querySelectorAll('.notification-item.unread:not([style*="display: none"])');

        const unreadOnPage = visibleUnreadCards.length;
        const totalOnPage = visibleCards.length;

        console.log('[DEBUG] Page counts:', {
            visibleCards: totalOnPage,
            visibleUnreadCards: unreadOnPage
        });

        // 🔔 СЧЕТЧИК В ШАПКЕ - НЕПРОЧИТАННЫЕ УВЕДОМЛЕНИЯ
        const currentUnreadForBadge = serverUnreadCount !== null ? serverUnreadCount : unreadOnPage;
        console.log('[DEBUG] Badge update - currentUnreadForBadge:', currentUnreadForBadge);

        // Обновляем счетчик в навигации
        updateNotificationBadge(currentUnreadForBadge);

        // 📊 СЧЕТЧИКИ НА СТРАНИЦЕ
        const unreadCountElement = document.getElementById('unread-count');
        const allCountElement = document.getElementById('all-count');
        const totalCountDisplay = document.getElementById('total-count-display');

        if (unreadCountElement) {
            unreadCountElement.textContent = serverUnreadCount !== null ? serverUnreadCount : unreadOnPage;
        }

        if (allCountElement) {
            allCountElement.textContent = serverTotalCount !== null ? serverTotalCount : totalOnPage;
        }

        if (totalCountDisplay) {
            totalCountDisplay.textContent = serverTotalCount !== null ? serverTotalCount : totalOnPage;
        }

        console.log('[DEBUG] Updated page counters:', {
            unread: serverUnreadCount !== null ? serverUnreadCount : unreadOnPage,
            total: serverTotalCount !== null ? serverTotalCount : totalOnPage
        });
    }

    // Функция обновления счетчика в навигации
    function updateNotificationBadge(count) {
        console.log('[DEBUG] updateNotificationBadge called with count:', count);

        // Ищем счетчик в шапке
        let badge = document.querySelector('.nav-counter-badge.notifications-badge');
        if (!badge) {
            badge = document.querySelector('.notifications-badge');
        }
        if (!badge) {
            badge = document.querySelector('[class*="notifications-badge"]');
        }

        console.log('[DEBUG] Badge element found:', badge);

        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'flex';
                console.log('[DEBUG] Badge updated - showing count:', count);
            } else {
                badge.style.display = 'none';
                console.log('[DEBUG] Badge hidden - count is 0');
            }
        } else {
            console.warn('[DEBUG] Badge element not found');
        }
    }

    // Функция показа уведомлений (Toast)
    function showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container');
        const toastId = 'toast-' + Date.now();

        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);

        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 3000
        });

        toast.show();

        // Удаляем элемент после скрытия
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }

    // Функция пометки одного уведомления как прочитанного
    function markSingleNotificationRead(notificationId, buttonElement = null, cardElement = null, callback = null) {
        console.log('[DEBUG] markSingleNotificationRead called:', {
            notificationId,
            hasButton: !!buttonElement,
            hasCard: !!cardElement,
            hasCallback: !!callback
        });

        fetch(`/users/cabinet/notifications/${notificationId}/mark-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('[DEBUG] markSingleNotificationRead response:', data);

            if (data.success) {
                // Обновляем визуальное состояние карточки
                const card = cardElement || document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (card) {
                    card.classList.remove('unread');
                    card.classList.add('read');
                    card.dataset.read = 'true';

                    // Удаляем бейдж "Новое"
                    const newBadge = card.querySelector('.badge.bg-warning');
                    if (newBadge) {
                        newBadge.remove();
                    }
                }

                // Скрываем кнопку "Прочитано"
                if (buttonElement) {
                    buttonElement.style.display = 'none';
                }

                // Обновляем счетчики
                updateAllCounters(data.unread_notifications_count, data.total_notifications_count);

                // Выполняем callback, если есть
                if (callback) {
                    callback();
                } else {
                    showToast('Уведомление помечено как прочитанное', 'success');
                }
            } else {
                showToast('Ошибка при пометке уведомления', 'error');
            }
        })
        .catch(error => {
            console.error('[DEBUG] Error in markSingleNotificationRead:', error);
            showToast('Ошибка при пометке уведомления', 'error');
        });
    }

    // Обработчик для кнопки "Прочитать все"
    function markAllAsRead() {
        fetch('/users/cabinet/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('[DEBUG] markAllAsRead response:', data);

            if (data.success) {
                // Обновляем все уведомления на странице
                document.querySelectorAll('.notification-item').forEach(item => {
                    item.classList.remove('unread');
                    item.classList.add('read');
                    item.dataset.read = 'true';

                    // Удаляем бейджи "Новое"
                    const newBadge = item.querySelector('.badge.bg-warning');
                    if (newBadge) {
                        newBadge.remove();
                    }

                    // Скрываем кнопки "Прочитано"
                    const readBtn = item.querySelector('.mark-read-btn');
                    if (readBtn) {
                        readBtn.style.display = 'none';
                    }
                });

                // ИСПРАВЛЕНИЕ: Используем правильные ключи ответа
                const unreadCount = data.unread_count || data.unread_notifications_count || 0;
                const totalCount = data.total_count || data.total_notifications_count || 0;

                // Обновляем счетчик в навигации
                updateNotificationBadge(unreadCount);

                // Обновляем счетчики на странице
                updateAllCounters(unreadCount, totalCount);

                showToast(data.message || 'Все уведомления помечены как прочитанные', 'success');
            } else {
                showToast('Ошибка при пометке уведомлений', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка при отметке всех уведомлений как прочитанных:', error);
            showToast('Ошибка при пометке уведомлений', 'error');
        });
    }

    // Обработчики событий
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', markAllAsRead);
    }

    // Обработчик клика по кнопкам "Прочитано"
    document.addEventListener('click', function(e) {
        if (e.target.closest('.mark-read-btn')) {
            e.stopPropagation(); // Останавливаем всплытие события
            const button = e.target.closest('.mark-read-btn');
            const notificationId = button.dataset.notificationId;
            markSingleNotificationRead(notificationId, button);
        }
    });

    // УМНАЯ КЛИКАБЕЛЬНОСТЬ УВЕДОМЛЕНИЙ
    document.querySelectorAll('.notification-item.clickable').forEach(card => {
        card.addEventListener('click', function(e) {
            // Исключаем клики по интерактивным элементам внутри карточки
            if (e.target.closest('.notification-checkbox, .btn, a, button, input')) {
                console.log('[DEBUG] Click ignored - clicked on interactive element:', e.target);
                return;
            }

            const notificationId = this.dataset.notificationId;
            const actionUrl = this.dataset.actionUrl;
            const isRead = this.dataset.read === 'true';

            console.log('[DEBUG] Card clicked:', {
                notificationId,
                actionUrl,
                isRead,
                hasActionUrl: actionUrl && actionUrl !== 'None' && actionUrl !== '#'
            });

            // Добавляем визуальную обратную связь
            this.classList.add('clicking');
            setTimeout(() => {
                this.classList.remove('clicking');
            }, 150);

            if (!isRead) {
                // Если не прочитано, сначала помечаем как прочитанное
                console.log('[DEBUG] Marking notification as read before action');
                markSingleNotificationRead(notificationId, null, this, () => {
                    // После успешной пометки как прочитанное, выполняем переход
                    if (actionUrl && actionUrl !== 'None' && actionUrl !== '#') {
                        console.log('[DEBUG] Redirecting to:', actionUrl);
                        window.location.href = actionUrl;
                    } else {
                        console.log('[DEBUG] No action URL, just marked as read');
                        showToast('Уведомление помечено как прочитанное', 'success');
                    }
                });
            } else {
                // Если уже прочитано и есть actionUrl, просто переходим
                if (actionUrl && actionUrl !== 'None' && actionUrl !== '#') {
                    console.log('[DEBUG] Already read, redirecting to:', actionUrl);
                    window.location.href = actionUrl;
                } else {
                    console.log('[DEBUG] Already read, no action URL');
                    showToast('Уведомление уже прочитано', 'info');
                }
            }
        });

        // Добавляем hover эффект для лучшей обратной связи
        card.addEventListener('mouseenter', function() {
            if (this.classList.contains('clickable')) {
                this.style.cursor = 'pointer';
            }
        });
    });

    // ФУНКЦИЯ УДАЛЕНИЯ ОДНОГО УВЕДОМЛЕНИЯ
    function deleteSingleNotification(notificationId, buttonElement = null) {
        console.log('[DEBUG] deleteSingleNotification called:', notificationId);

        fetch(`/users/cabinet/notifications/delete/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('[DEBUG] deleteSingleNotification response:', data);

            if (data.success) {
                // Удаляем карточку из DOM
                const card = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (card) {
                    card.style.transition = 'all 0.3s ease';
                    card.style.opacity = '0';
                    card.style.transform = 'translateX(-100%)';

                    setTimeout(() => {
                        card.remove();
                        // Обновляем счетчики после удаления
                        updateAllCounters(data.unread_notifications_count, data.total_notifications_count);

                        // Проверяем, остались ли уведомления
                        const remainingNotifications = document.querySelectorAll('.notification-item');
                        if (remainingNotifications.length === 0) {
                            location.reload(); // Перезагружаем страницу для показа пустого состояния
                        }
                    }, 300);
                }

                showToast('Уведомление удалено', 'success');
            } else {
                showToast('Ошибка при удалении уведомления', 'error');
            }
        })
        .catch(error => {
            console.error('[DEBUG] Error in deleteSingleNotification:', error);
            showToast('Ошибка при удалении уведомления', 'error');
        });
    }

    // ФУНКЦИЯ УДАЛЕНИЯ ВЫБРАННЫХ УВЕДОМЛЕНИЙ
    function deleteSelectedNotifications() {
        const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
        const notificationIds = Array.from(selectedCheckboxes).map(cb => cb.dataset.notificationId);

        if (notificationIds.length === 0) {
            showToast('Выберите уведомления для удаления', 'error');
            return;
        }

        console.log('[DEBUG] deleteSelectedNotifications called:', notificationIds);

        fetch('/users/cabinet/notifications/delete-multiple/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                notification_ids: notificationIds
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('[DEBUG] deleteSelectedNotifications response:', data);

            if (data.success) {
                // Удаляем карточки из DOM
                notificationIds.forEach(id => {
                    const card = document.querySelector(`[data-notification-id="${id}"]`);
                    if (card) {
                        card.style.transition = 'all 0.3s ease';
                        card.style.opacity = '0';
                        card.style.transform = 'translateX(-100%)';

                        setTimeout(() => {
                            card.remove();
                        }, 300);
                    }
                });

                // Обновляем счетчики
                setTimeout(() => {
                    updateAllCounters(data.unread_notifications_count, data.total_notifications_count);

                    // Проверяем, остались ли уведомления
                    const remainingNotifications = document.querySelectorAll('.notification-item');
                    if (remainingNotifications.length === 0) {
                        location.reload(); // Перезагружаем страницу для показа пустого состояния
                    }
                }, 300);

                // Сбрасываем выбор
                selectAllCheckbox.checked = false;
                updateBulkActionButtons();

                showToast(`Удалено уведомлений: ${data.deleted_count}`, 'success');
            } else {
                showToast('Ошибка при удалении уведомлений', 'error');
            }
        })
        .catch(error => {
            console.error('[DEBUG] Error in deleteSelectedNotifications:', error);
            showToast('Ошибка при удалении уведомлений', 'error');
        });
    }

    // ФУНКЦИЯ ПОМЕТКИ ВЫБРАННЫХ КАК ПРОЧИТАННЫХ
    function markSelectedAsRead() {
        const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
        const notificationIds = Array.from(selectedCheckboxes).map(cb => cb.dataset.notificationId);

        if (notificationIds.length === 0) {
            showToast('Выберите уведомления для пометки', 'error');
            return;
        }

        console.log('[DEBUG] markSelectedAsRead called:', notificationIds);

        fetch('/users/cabinet/notifications/read-multiple/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                notification_ids: notificationIds
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('[DEBUG] markSelectedAsRead response:', data);

            if (data.success) {
                // Обновляем визуальное состояние карточек
                notificationIds.forEach(id => {
                    const card = document.querySelector(`[data-notification-id="${id}"]`);
                    if (card) {
                        card.classList.remove('unread');
                        card.classList.add('read');
                        card.dataset.read = 'true';

                        // Удаляем бейдж "Новое"
                        const newBadge = card.querySelector('.badge.bg-warning');
                        if (newBadge) {
                            newBadge.remove();
                        }

                        // Скрываем кнопку "Прочитано"
                        const readBtn = card.querySelector('.mark-read-btn');
                        if (readBtn) {
                            readBtn.style.display = 'none';
                        }
                    }
                });

                // Обновляем счетчики
                updateAllCounters(data.unread_notifications_count, data.total_notifications_count);

                // Сбрасываем выбор
                selectAllCheckbox.checked = false;
                updateBulkActionButtons();

                showToast(`Помечено как прочитанные: ${data.updated_count} уведомлений`, 'success');
            } else {
                showToast('Ошибка при пометке уведомлений', 'error');
            }
        })
        .catch(error => {
            console.error('[DEBUG] Error in markSelectedAsRead:', error);
            showToast('Ошибка при пометке уведомлений', 'error');
        });
    }

    // ФУНКЦИЯ ОБНОВЛЕНИЯ СОСТОЯНИЯ КНОПОК МАССОВЫХ ДЕЙСТВИЙ
    function updateBulkActionButtons() {
        const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
        const hasSelected = selectedCheckboxes.length > 0;

        if (markSelectedReadBtn) {
            markSelectedReadBtn.disabled = !hasSelected;
        }
        if (deleteSelectedBtn) {
            deleteSelectedBtn.disabled = !hasSelected;
        }
    }

    // ОБРАБОТЧИКИ СОБЫТИЙ ДЛЯ КНОПОК УДАЛЕНИЯ
    document.addEventListener('click', function(e) {
        // Удаление одного уведомления
        if (e.target.closest('.delete-single-btn')) {
            e.stopPropagation(); // Останавливаем всплытие события
            const button = e.target.closest('.delete-single-btn');
            const notificationId = button.dataset.notificationId;

            // Показываем модальное окно подтверждения
            const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
            document.getElementById('deleteModalText').textContent = 'Вы уверены, что хотите удалить это уведомление?';

            // Устанавливаем обработчик подтверждения
            const confirmBtn = document.getElementById('confirmDelete');
            confirmBtn.onclick = function() {
                deleteSingleNotification(notificationId, button);
                modal.hide();
            };

            modal.show();
        }
    });

    // ОБРАБОТЧИКИ ДЛЯ МАССОВЫХ ДЕЙСТВИЙ
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', function() {
            const selectedCount = document.querySelectorAll('.notification-checkbox:checked').length;
            if (selectedCount === 0) {
                showToast('Выберите уведомления для удаления', 'error');
                return;
            }

            // Показываем модальное окно подтверждения
            const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
            document.getElementById('deleteModalText').textContent = `Вы уверены, что хотите удалить ${selectedCount} уведомлений?`;

            // Устанавливаем обработчик подтверждения
            const confirmBtn = document.getElementById('confirmDelete');
            confirmBtn.onclick = function() {
                deleteSelectedNotifications();
                modal.hide();
            };

            modal.show();
        });
    }

    if (markSelectedReadBtn) {
        markSelectedReadBtn.addEventListener('click', markSelectedAsRead);
    }

    // ОБРАБОТЧИКИ ДЛЯ ЧЕКБОКСОВ
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.notification-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButtons();
        });
    }

    // Обработчик для отдельных чекбоксов
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('notification-checkbox')) {
            e.stopPropagation(); // Останавливаем всплытие события
            updateBulkActionButtons();

            // Обновляем состояние "Выбрать все"
            const allCheckboxes = document.querySelectorAll('.notification-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');

            if (selectAllCheckbox) {
                selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
                selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
            }
        }
    });

    // Обработчик кликов по чекбоксам для предотвращения клика по карточке
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('notification-checkbox')) {
            e.stopPropagation(); // Останавливаем всплытие события
        }
    });

    // Обработчик кликов по всем кнопкам и ссылкам в карточках для предотвращения клика по карточке
    document.addEventListener('click', function(e) {
        if (e.target.closest('.notification-actions .btn, .notification-actions a')) {
            e.stopPropagation(); // Останавливаем всплытие события
        }
    });

    // ФИЛЬТРЫ УВЕДОМЛЕНИЙ
    if (filterTabs.length > 0) {
        filterTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Убираем активный класс со всех вкладок
                filterTabs.forEach(t => t.classList.remove('active'));
                // Добавляем активный класс к текущей вкладке
                this.classList.add('active');

                const filter = this.dataset.filter;
                console.log('[DEBUG] Filter applied:', filter);

                // Фильтруем уведомления
                notificationCards.forEach(card => {
                    let shouldShow = true;

                    switch (filter) {
                        case 'all':
                            shouldShow = true;
                            break;
                        case 'unread':
                            shouldShow = card.dataset.read === 'false';
                            break;
                        case 'system':
                            shouldShow = card.dataset.type === 'system';
                            break;
                        case 'social':
                            shouldShow = card.dataset.type === 'social';
                            break;
                        case 'orders':
                            shouldShow = card.dataset.type === 'order';
                            break;
                        default:
                            shouldShow = true;
                    }

                    card.style.display = shouldShow ? 'block' : 'none';
                });

                // Обновляем счетчики после фильтрации
                updateAllCounters();
            });
        });
    }

    // Инициализация счетчиков при загрузке страницы
    updateAllCounters();
});
