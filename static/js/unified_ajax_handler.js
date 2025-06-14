document.addEventListener('DOMContentLoaded', function () {
    const ajaxSection = document.querySelector('[data-ajax-section]');
    if (!ajaxSection) {
        console.warn('Unified AJAX handler: data-ajax-section container not found.');
        return;
    }

    // Allow developers to optionally prefix IDs with '#'
    const rawContentTarget = ajaxSection.dataset.contentTarget || 'content-container';
    const rawPaginationTarget = ajaxSection.dataset.paginationTarget || 'pagination-container';
    const contentTargetId = rawContentTarget.replace(/^#/, '');
    const paginationTargetId = rawPaginationTarget.replace(/^#/, '');

    const contentWrapper = document.getElementById(contentTargetId);
    const paginationWrapper = document.getElementById(paginationTargetId);
    const filtersWrapper = document.querySelector('.unified-filters');

    if (!contentWrapper || !paginationWrapper) {
        console.warn('Unified AJAX handler: Missing content or pagination wrapper elements.');
        return;
    }

    // ajaxUrl при необходимости можно указать явно в атрибуте data-ajax-url на контейнере
    const ajaxUrl = ajaxSection.dataset.ajaxUrl || window.location.pathname;

    let isFetching = false; // NEW FLAG: защищаем от множественных запросов

    function fetchContent(url) {
        if (isFetching) {
            return; // Предотвращаем параллельные запросы
        }
        isFetching = true; // Помечаем, что запрос начат
        contentWrapper.style.opacity = '0.5';

        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                contentWrapper.innerHTML = data.cards_html;
                paginationWrapper.innerHTML = data.pagination_html;

                // Обновляем URL в адресной строке без /ajax/filter/ части
                try {
                    const urlObj = new URL(url, window.location.origin);
                    // FORM THE CANONICAL BASE PATH (с завершающим "/")
                    let basePath = ajaxUrl.replace(/\/ajax\/filter\/?$/, '');
                    // Убеждаемся, что путь оканчивается на "/" для предотвращения 301 редиректов Django
                    if (!basePath.endsWith('/')) {
                        basePath += '/';
                    }
                    const newPath = basePath + urlObj.search;
                    window.history.pushState({ path: newPath }, '', newPath);
                } catch (e) {
                    console.warn('Failed to update history:', e);
                }

                // Сообщаем другим скриптам, что контент обновился
                document.dispatchEvent(new CustomEvent('contentUpdated'));

                // Re-initialize animations
                if (typeof AOS !== 'undefined') {
                    AOS.refresh();
                }

                // NEW: плавная прокрутка к секции контента
                // Выполняем прокрутку ТОЛЬКО если пользователь прокрутил страницу достаточно далеко,
                // чтобы hero-секция уже не была видна. Это предотвращает «скачок» интерфейса при нажатии
                // на фильтры, когда страница и так находится в верхней части.
                if (ajaxSection.dataset.scrollTarget) {
                    const scrollElement = document.querySelector(ajaxSection.dataset.scrollTarget);
                    if (scrollElement) {
                        const currentScroll = window.scrollY || window.pageYOffset;
                        // Прокручиваем только если пользователь отходит > 400px от верхушки страницы
                        if (currentScroll > 400) {
                            scrollElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                }
            } else {
                 console.error('AJAX request failed:', data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error fetching content:', error);
            // Optionally, show an error message to the user
        })
        .finally(() => {
            contentWrapper.style.opacity = '1';
            isFetching = false; // Сбрасываем флаг после завершения
        });
    }

    // Event delegation for filters and pagination
    document.body.addEventListener('click', function(event) {
        const target = event.target;

        // Handle filter clicks
        if (target.matches('.filter-tab-link') || target.closest('.filter-tab-link')) {
            event.preventDefault();
            const link = target.closest('.filter-tab-link');
            const filterId = link.dataset.filter;
            const newUrl = `${ajaxUrl}?filter=${encodeURIComponent(filterId)}`;

            // Update active state
            document.querySelectorAll('.filter-tab-link').forEach(el => el.classList.remove('active'));
            link.classList.add('active');

            fetchContent(newUrl);
        }

        // Handle pagination clicks
        if (target.matches('.page-link') || target.closest('.page-link')) {
             event.preventDefault();
            const link = target.closest('.page-link');
            const pageNumber = link.dataset.page;
            const filterId = link.dataset.filter || 'all';
            if (!pageNumber) return;
            const newUrl = `${ajaxUrl}?page=${encodeURIComponent(pageNumber)}${filterId && filterId !== 'all' ? `&filter=${encodeURIComponent(filterId)}` : ''}`;
            fetchContent(newUrl);
        }
    });
});
