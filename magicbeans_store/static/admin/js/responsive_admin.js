/**
 * АДАПТИВНАЯ АДМИНКА MAGIC BEANS - ИНТЕРАКТИВНОСТЬ
 * Умное изменение размеров столбцов и мобильная адаптивность
 */

document.addEventListener('DOMContentLoaded', function() {

    // ======================================================================
    // ИЗМЕНЯЕМЫЕ СТОЛБЦЫ ТАБЛИЦ
    // ======================================================================

    function initResizableColumns() {
        const tables = document.querySelectorAll('.results table');

        tables.forEach(table => {
            const headers = table.querySelectorAll('th');

            headers.forEach((header, index) => {
                // Создаем точную зону для изменения размера (только правый край)
                const resizer = document.createElement('div');
                resizer.className = 'column-resizer';
                resizer.style.cssText = `
                    position: absolute;
                    right: -2px;
                    top: 0;
                    width: 8px;
                    height: 100%;
                    background: transparent;
                    cursor: col-resize;
                    z-index: 100;
                    border-radius: 2px;
                `;

                header.style.position = 'relative';
                header.appendChild(resizer);

                let isResizing = false;
                let startX = 0;
                let startWidth = 0;
                let minWidth = 100; // Минимальная ширина
                let maxWidth = 500; // Максимальная ширина

                // Визуальная обратная связь при наведении
                resizer.addEventListener('mouseenter', function() {
                    this.style.background = 'rgba(65, 118, 144, 0.3)';
                    this.style.borderLeft = '2px solid #417690';
                });

                resizer.addEventListener('mouseleave', function() {
                    if (!isResizing) {
                        this.style.background = 'transparent';
                        this.style.borderLeft = 'none';
                    }
                });

                resizer.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation(); // Предотвращаем всплытие события

                    isResizing = true;
                    startX = e.clientX;

                    // Получаем текущую ширину более надежно
                    const rect = header.getBoundingClientRect();
                    startWidth = rect.width;

                    // Устанавливаем фиксированную ширину для начала изменения
                    header.style.width = startWidth + 'px';

                    document.addEventListener('mousemove', doResize);
                    document.addEventListener('mouseup', stopResize);

                    // Визуальная обратная связь
                    resizer.style.background = '#417690';
                    resizer.style.borderLeft = '2px solid #fff';
                    header.style.userSelect = 'none';
                    document.body.style.cursor = 'col-resize';

                    // Добавляем класс для всей таблицы
                    table.classList.add('resizing');
                });

                function doResize(e) {
                    if (!isResizing) return;

                    e.preventDefault();

                    const deltaX = e.clientX - startX;
                    let newWidth = startWidth + deltaX;

                    // Применяем ограничения плавно
                    newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));

                    // Применяем новую ширину
                    header.style.width = newWidth + 'px';

                    // Синхронизируем ячейки в столбце
                    const cellIndex = Array.from(header.parentNode.children).indexOf(header);
                    const rows = table.querySelectorAll('tbody tr');

                    requestAnimationFrame(() => {
                        rows.forEach(row => {
                            const cell = row.children[cellIndex];
                            if (cell) {
                                cell.style.width = newWidth + 'px';
                                cell.style.minWidth = newWidth + 'px';
                                cell.style.maxWidth = newWidth + 'px';
                            }
                        });
                    });
                }

                function stopResize() {
                    if (!isResizing) return;

                    isResizing = false;

                    // Убираем визуальные эффекты
                    resizer.style.background = 'transparent';
                    resizer.style.borderLeft = 'none';
                    header.style.userSelect = 'auto';
                    document.body.style.cursor = 'auto';
                    table.classList.remove('resizing');

                    document.removeEventListener('mousemove', doResize);
                    document.removeEventListener('mouseup', stopResize);

                    // Сохраняем настройки в localStorage
                    setTimeout(() => saveColumnWidths(table), 100);
                }
            });

            // Загружаем сохраненные настройки
            loadColumnWidths(table);
        });
    }

    // ======================================================================
    // СОХРАНЕНИЕ И ЗАГРУЗКА РАЗМЕРОВ СТОЛБЦОВ
    // ======================================================================

    function saveColumnWidths(table) {
        const tableName = getTableIdentifier(table);
        const widths = [];

        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            widths.push(header.style.width || 'auto');
        });

        localStorage.setItem(`admin_column_widths_${tableName}`, JSON.stringify(widths));
    }

    function loadColumnWidths(table) {
        const tableName = getTableIdentifier(table);
        const savedWidths = localStorage.getItem(`admin_column_widths_${tableName}`);

        if (savedWidths) {
            const widths = JSON.parse(savedWidths);
            const headers = table.querySelectorAll('th');

            headers.forEach((header, index) => {
                if (widths[index] && widths[index] !== 'auto') {
                    header.style.width = widths[index];

                    // Применяем к ячейкам столбца
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cell = row.children[index];
                        if (cell) {
                            cell.style.width = widths[index];
                        }
                    });
                }
            });
        }
    }

    function getTableIdentifier(table) {
        // Создаем уникальный идентификатор таблицы на основе URL и заголовков
        const url = window.location.pathname;
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim()).join('_');
        return btoa(url + '_' + headers).replace(/[^a-zA-Z0-9]/g, '');
    }

    // ======================================================================
    // МОБИЛЬНЫЕ ФИЛЬТРЫ
    // ======================================================================

    function initMobileFilters() {
        const sidebar = document.getElementById('changelist-sidebar');
        if (!sidebar) return;

        // Создаем кнопку открытия фильтров
        const filterToggle = document.createElement('button');
        filterToggle.className = 'filter-toggle';
        filterToggle.innerHTML = '🔍 Фильтры';
        filterToggle.style.display = 'none';

        // Вставляем кнопку перед результатами
        const results = document.querySelector('.results');
        if (results) {
            results.parentNode.insertBefore(filterToggle, results);
        }

        // Обработчик открытия/закрытия
        filterToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            this.innerHTML = sidebar.classList.contains('open') ? '✖ Закрыть' : '🔍 Фильтры';
        });

        // Закрытие при клике вне фильтров
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 &&
                !sidebar.contains(e.target) &&
                !filterToggle.contains(e.target) &&
                sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                filterToggle.innerHTML = '🔍 Фильтры';
            }
        });

        // Показываем/скрываем кнопку в зависимости от размера экрана
        function toggleFilterButton() {
            if (window.innerWidth <= 768) {
                filterToggle.style.display = 'block';
            } else {
                filterToggle.style.display = 'none';
                sidebar.classList.remove('open');
            }
        }

        window.addEventListener('resize', toggleFilterButton);
        toggleFilterButton();
    }

    // ======================================================================
    // ИНИЦИАЛИЗАЦИЯ ВСЕХ ФУНКЦИЙ
    // ======================================================================

    // Инициализируем основные функции
    initResizableColumns();
    initMobileFilters();

    console.log('✅ Адаптивная админка Magic Beans загружена (упрощенная версия)!');
});

// ======================================================================
// ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
// ======================================================================

// Функция для сброса всех настроек столбцов
window.resetColumnWidths = function() {
    const tables = document.querySelectorAll('.results table');
    tables.forEach(table => {
        const tableName = getTableIdentifier(table);
        localStorage.removeItem(`admin_column_widths_${tableName}`);

        // Сбрасываем стили
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.style.width = 'auto';
        });

        const cells = table.querySelectorAll('td');
        cells.forEach(cell => {
            cell.style.width = 'auto';
        });
    });

    alert('Настройки столбцов сброшены!');
    location.reload();
};

// Функция получения идентификатора таблицы (дублируем для внешнего использования)
function getTableIdentifier(table) {
    const url = window.location.pathname;
    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim()).join('_');
    return btoa(url + '_' + headers).replace(/[^a-zA-Z0-9]/g, '');
}
