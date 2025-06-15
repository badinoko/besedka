document.addEventListener('DOMContentLoaded', function() {
    console.log('🔔 Notifications JS loaded for tiles design');

    // Элементы интерфейса
    const selectAllCheckbox = document.getElementById('select-all');
    const markSelectedReadBtn = document.getElementById('mark-selected-read');
    const markAllReadBtn = document.getElementById('mark-all-read');
    const deleteSelectedBtn = document.getElementById('delete-selected');
    const selectedCountSpan = document.getElementById('selected-count');

    // Функция обновления счетчиков (ИСПРАВЛЕНО - используем только серверные данные)
    function updateAllCounters(serverUnreadCount = null, serverTotalCount = null) {
        console.log('🔢 Обновление счетчиков:', {
            serverUnreadCount: serverUnreadCount,
            serverTotalCount: serverTotalCount
        });

        // ВАЖНО: Используем ТОЛЬКО серверные данные, не считаем плитки на странице
        // так как на странице может быть только часть уведомлений (пагинация)

        // Обновляем счетчик в навигации (ТОЛЬКО серверные данные)
        if (serverUnreadCount !== null) {
            updateNotificationBadge(serverUnreadCount);
        }

        // Обновляем счетчики в hero секции (ТОЛЬКО серверные данные)
        const totalStat = document.querySelector('.hero-stat-value'); // Первый - "Всего"
        const unreadStat = document.querySelectorAll('.hero-stat-value')[1]; // Второй - "Непрочитанных"
        const systemStat = document.querySelectorAll('.hero-stat-value')[2]; // Третий - "Системных"

        if (totalStat && serverTotalCount !== null) {
            totalStat.textContent = serverTotalCount;
        }
        if (unreadStat && serverUnreadCount !== null) {
            unreadStat.textContent = serverUnreadCount;
        }

        console.log('📊 Обновлены счетчики hero:', {
            total: serverTotalCount,
            unread: serverUnreadCount
        });
    }

    // Функция обновления состояния кнопок массовых действий
    function updateBulkActionButtons() {
        const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
        const selectedCount = selectedCheckboxes.length;

        if (markSelectedReadBtn) {
            markSelectedReadBtn.disabled = selectedCount === 0;
        }
        if (deleteSelectedBtn) {
            deleteSelectedBtn.disabled = selectedCount === 0;
        }

        if (selectedCountSpan) {
            if (selectedCount === 0) {
                selectedCountSpan.textContent = 'Выберите уведомления для массовых операций';
            } else {
                selectedCountSpan.textContent = `Выбрано: ${selectedCount} уведомлений`;
            }
        }
    }

    // Функция обновления счетчика в навигации (ТОЧНЫЙ селектор)
    function updateNotificationBadge(count) {
        // Ищем ТОЛЬКО badge уведомлений по точному классу
        const notificationBadges = document.querySelectorAll('.notifications-badge');

        notificationBadges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });

        console.log('🔔 Обновлен бейдж уведомлений:', count, 'найдено badges:', notificationBadges.length);
    }

    // Функция показа уведомлений
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Функция пометки одного уведомления как прочитанного
    function markNotificationRead(notificationId, tileElement = null, callback = null) {
        console.log('📖 Помечаем как прочитанное:', notificationId);

        fetch(`/users/cabinet/notifications/${notificationId}/mark-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tile = tileElement || document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (tile) {
                    tile.classList.remove('unread');
                    tile.classList.add('read');

                    // Убираем бейдж "Новое"
                    const newBadge = tile.querySelector('.badge.bg-primary');
                    if (newBadge) {
                        newBadge.remove();
                    }
                }

                updateAllCounters(data.unread_notifications_count, data.total_notifications_count);

                if (callback) {
                    callback();
                } else {
                    showNotification('✅ Уведомление помечено как прочитанное', 'success');
                }
            } else {
                showNotification('❌ Ошибка при пометке уведомления', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка в markNotificationRead:', error);
            showNotification('❌ Ошибка при пометке уведомления', 'error');
        });
    }

    // Функция удаления уведомления
    function deleteNotification(notificationId, tileElement = null) {
        console.log('🗑️ Удаляем уведомление:', notificationId);

        fetch(`/users/cabinet/notifications/delete/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tile = tileElement || document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (tile) {
                    tile.style.transition = 'all 0.3s ease';
                    tile.style.opacity = '0';
                    tile.style.transform = 'translateX(100%)';

                    setTimeout(() => {
                        tile.remove();
                        updateAllCounters(data.unread_notifications_count, data.total_notifications_count);
                        updateBulkActionButtons();
                    }, 300);
                }

                showNotification('✅ Уведомление удалено', 'success');
            } else {
                showNotification('❌ Ошибка при удалении уведомления', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка в deleteNotification:', error);
            showNotification('❌ Ошибка при удалении уведомления', 'error');
        });
    }

    // Обработчик для кнопки "Прочитать все"
    function markAllAsRead() {
        fetch('/users/cabinet/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.querySelectorAll('.notification-tile.unread').forEach(tile => {
                    tile.classList.remove('unread');
                    tile.classList.add('read');

                    const markReadBtn = tile.querySelector('.mark-read-btn');
                    if (markReadBtn) {
                        markReadBtn.style.display = 'none';
                    }
                });

                updateAllCounters(data.unread_notifications_count, data.total_notifications_count);
                showNotification(data.message || 'Все уведомления помечены как прочитанные', 'success');
            } else {
                showNotification('Ошибка при пометке уведомлений', 'error');
            }
        })
        .catch(error => {
            console.error('[DEBUG] Error in markAllAsRead:', error);
            showNotification('Ошибка при пометке уведомлений', 'error');
        });
    }

    // ОБРАБОТЧИКИ СОБЫТИЙ

    // Клик по плитке уведомления (переход по ссылке)
    document.addEventListener('click', function(e) {
        const tile = e.target.closest('.notification-tile');
        if (!tile) return;

        // Игнорируем клики по чекбоксам и кнопкам действий
        if (e.target.closest('.notification-checkbox') ||
            e.target.closest('.notification-actions') ||
            e.target.closest('input[type="checkbox"]')) {
            return;
        }

        const notificationId = tile.dataset.notificationId;
        const actionUrl = tile.dataset.actionUrl;

        console.log('🖱️ Клик по плитке:', { notificationId, actionUrl });

        // Помечаем как прочитанное если не прочитано
        if (tile.classList.contains('unread')) {
            markNotificationRead(notificationId, tile, () => {
                if (actionUrl && actionUrl !== '#' && actionUrl !== 'None' && actionUrl !== '') {
                    console.log('🔗 Переходим по ссылке:', actionUrl);
                    window.location.href = actionUrl;
                }
            });
        } else if (actionUrl && actionUrl !== '#' && actionUrl !== 'None' && actionUrl !== '') {
            console.log('🔗 Переходим по ссылке:', actionUrl);
            window.location.href = actionUrl;
        }
    });

    // Кнопки "Перейти" в плитках
    document.addEventListener('click', function(e) {
        if (e.target.closest('.notification-go-btn')) {
            e.preventDefault();
            e.stopPropagation();

            const btn = e.target.closest('.notification-go-btn');
            const url = btn.dataset.url;
            const tile = btn.closest('.notification-tile');
            const notificationId = tile.dataset.notificationId;

            console.log('🔗 Кнопка "Перейти":', { url, notificationId });

            // Помечаем как прочитанное и переходим
            if (tile.classList.contains('unread')) {
                markNotificationRead(notificationId, tile, () => {
                    if (url && url !== '#' && url !== 'None' && url !== '') {
                        window.location.href = url;
                    }
                });
            } else if (url && url !== '#' && url !== 'None' && url !== '') {
                window.location.href = url;
            }
        }
    });

    // Кнопки удаления в плитках
    document.addEventListener('click', function(e) {
        if (e.target.closest('.notification-delete-btn')) {
            e.preventDefault();
            e.stopPropagation();

            const btn = e.target.closest('.notification-delete-btn');
            const notificationId = btn.dataset.id;
            const tile = btn.closest('.notification-tile');

            deleteNotification(notificationId, tile);
        }
    });

    // Чекбокс "Выбрать все"
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.notification-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = this.checked;
            });
            updateBulkActionButtons();
        });
    }

    // Индивидуальные чекбоксы
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('notification-checkbox')) {
            updateBulkActionButtons();

            // Обновляем состояние "Выбрать все"
            if (selectAllCheckbox) {
                const allCheckboxes = document.querySelectorAll('.notification-checkbox');
                const checkedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
                selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
            }
        }
    });

    // Кнопки массовых действий
    if (markSelectedReadBtn) {
        markSelectedReadBtn.addEventListener('click', function() {
            const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
            const notificationIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

            if (notificationIds.length === 0) {
                showNotification('⚠️ Выберите уведомления для пометки', 'warning');
                return;
            }

            console.log('📖 Помечаем выбранные как прочитанные:', notificationIds);

            fetch('/users/cabinet/notifications/read-multiple/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notification_ids: notificationIds })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    notificationIds.forEach(id => {
                        const tile = document.querySelector(`[data-notification-id="${id}"]`);
                        if (tile) {
                            tile.classList.remove('unread');
                            tile.classList.add('read');

                            // Убираем бейдж "Новое"
                            const newBadge = tile.querySelector('.badge.bg-primary');
                            if (newBadge) {
                                newBadge.remove();
                            }

                            // Снимаем выделение
                            const checkbox = tile.querySelector('.notification-checkbox');
                            if (checkbox) {
                                checkbox.checked = false;
                            }
                        }
                    });

                    updateAllCounters(data.unread_notifications_count, data.total_notifications_count);
                    updateBulkActionButtons();

                    if (selectAllCheckbox) {
                        selectAllCheckbox.checked = false;
                    }

                    showNotification(data.message || '✅ Выбранные уведомления помечены как прочитанные', 'success');
                } else {
                    showNotification('❌ Ошибка при пометке уведомлений', 'error');
                }
            })
            .catch(error => {
                console.error('❌ Ошибка в markSelectedAsRead:', error);
                showNotification('❌ Ошибка при пометке уведомлений', 'error');
            });
        });
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', markAllAsRead);
    }

    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', function() {
            const selectedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
            const notificationIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

            if (notificationIds.length === 0) {
                showNotification('⚠️ Выберите уведомления для удаления', 'warning');
                return;
            }

            // Убран confirm по требованию пользователя - браузерный диалог заменен красивыми уведомлениями

            console.log('🗑️ Удаляем выбранные:', notificationIds);

            fetch('/users/cabinet/notifications/delete-multiple/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notification_ids: notificationIds })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    notificationIds.forEach(id => {
                        const tile = document.querySelector(`[data-notification-id="${id}"]`);
                        if (tile) {
                            tile.style.transition = 'all 0.3s ease';
                            tile.style.opacity = '0';
                            tile.style.transform = 'translateX(100%)';

                            setTimeout(() => {
                                tile.remove();
                            }, 300);
                        }
                    });

                    setTimeout(() => {
                        // ИСПРАВЛЕНО: используем серверные данные вместо подсчета плиток
                        updateAllCounters(data.unread_notifications_count, data.total_notifications_count);
                        updateBulkActionButtons();

                        if (selectAllCheckbox) {
                            selectAllCheckbox.checked = false;
                        }
                    }, 350); // Увеличена задержка для завершения анимации

                    showNotification(data.message || '✅ Выбранные уведомления удалены', 'success');
                } else {
                    showNotification('❌ Ошибка при удалении уведомлений', 'error');
                }
            })
            .catch(error => {
                console.error('❌ Ошибка в deleteSelected:', error);
                showNotification('❌ Ошибка при удалении уведомлений', 'error');
            });
        });
    }

    // Обработчик кликов по плиткам уведомлений
    document.addEventListener('click', function(e) {
        const tile = e.target.closest('.notification-tile');
        if (tile && !e.target.closest('.notification-checkbox') && !e.target.closest('button')) {
            const notificationId = tile.dataset.notificationId;
            const actionUrl = tile.dataset.actionUrl;

            // Помечаем как прочитанное при клике
            if (tile.classList.contains('unread')) {
                markNotificationRead(notificationId, tile, function() {
                    // После пометки как прочитанное переходим по ссылке, если есть
                    if (actionUrl && actionUrl !== '#' && actionUrl !== '') {
                        window.open(actionUrl, '_blank');
                    }
                });
            } else {
                // Если уже прочитанное, просто переходим по ссылке
                if (actionUrl && actionUrl !== '#' && actionUrl !== '') {
                    window.open(actionUrl, '_blank');
                }
            }
        }
    });

    // Инициализация при загрузке страницы
    updateBulkActionButtons();

    // ========= ДОБАВЛЯЕМ ФИЛЬТРАЦИЮ УВЕДОМЛЕНИЙ =========
    const filterButtons = document.querySelectorAll('.hero-filter-btn');

    // Функция фильтрации плиток
    function filterNotifications(filterType) {
        const tiles = document.querySelectorAll('.notification-tile');

        tiles.forEach(tile => {
            let shouldShow = true;

            switch (filterType) {
                case 'all':
                    shouldShow = true;
                    break;
                case 'unread':
                    shouldShow = tile.classList.contains('unread');
                    break;
                case 'system':
                    shouldShow = tile.querySelector('.notification-icon.system') !== null;
                    break;
                case 'personal':
                    // Личные - все уведомления, кроме системных
                    shouldShow = tile.querySelector('.notification-icon.system') === null;
                    break;
                case 'order':
                    shouldShow = tile.querySelector('.notification-icon.order') !== null;
                    break;
                default:
                    shouldShow = true;
            }

            if (shouldShow) {
                tile.style.display = 'flex';
                tile.style.animation = 'fadeIn 0.3s ease';
            } else {
                tile.style.display = 'none';
            }
        });

        // Обновляем состояние кнопок фильтров
        filterButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filterType}"]`).classList.add('active');

        console.log(`🔍 Применен фильтр: ${filterType}`);
    }

    // Обработчики для кнопок фильтров
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterType = this.dataset.filter;
            filterNotifications(filterType);
        });
    });

    console.log('✅ Notifications JS полностью инициализирован');
});

// Глобальные функции
window.markNotificationRead = function(notificationId) {
    const tile = document.querySelector(`[data-notification-id="${notificationId}"]`);

    fetch(`/users/cabinet/notifications/${notificationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && tile) {
            tile.classList.remove('unread');
            tile.classList.add('read');

            const badge = document.querySelector('.notifications-badge');
            if (badge && data.unread_notifications_count !== undefined) {
                if (data.unread_notifications_count > 0) {
                    badge.textContent = data.unread_notifications_count;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    });
};
