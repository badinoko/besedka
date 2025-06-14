/**
 * ===============================================================
 * УНИФИЦИРОВАННЫЕ АНИМАЦИИ ДЛЯ ПРОЕКТА "БЕСЕДКА"
 * ===============================================================
 * Инициализация AOS и других анимационных библиотек
 * Обработка событий для реинициализации анимаций после AJAX
 * ===============================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    // =============================================================================
    // ИНИЦИАЛИЗАЦИЯ AOS АНИМАЦИЙ
    // =============================================================================
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out',
            once: true,
            offset: 50,
            delay: 100
        });

        // Логирование для отладки
        console.log('AOS анимации инициализированы');
    }

    // =============================================================================
    // ОБРАБОТКА AJAX ОБНОВЛЕНИЙ КОНТЕНТА
    // =============================================================================
    document.addEventListener('contentUpdated', function(e) {
        console.log('Контент обновлен, переинициализация анимаций...');

        // Переинициализация AOS для новых элементов
        if (typeof AOS !== 'undefined') {
            setTimeout(() => {
                AOS.refresh();
                console.log('AOS анимации переинициализированы');
            }, 100);
        }

        // Переинициализация других анимационных библиотек если есть
        // Например, если используется Animate.css или другие
        initializeCustomAnimations();

        // Переинициализация Masonry после AJAX обновления
        setTimeout(() => {
            initializeMasonry();
        }, 150);
    });

    // =============================================================================
    // КАСТОМНЫЕ АНИМАЦИИ
    // =============================================================================
    function initializeCustomAnimations() {
        // Анимация появления карточек
        const cards = document.querySelectorAll('.unified-card');
        cards.forEach((card, index) => {
            if (!card.classList.contains('animated')) {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';

                setTimeout(() => {
                    card.style.transition = 'all 0.6s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                    card.classList.add('animated');
                }, index * 100);
            }
        });

        // Анимация счетчиков в hero-секциях
        animateCounters();
    }

    // =============================================================================
    // АНИМАЦИЯ СЧЕТЧИКОВ
    // =============================================================================
    function animateCounters() {
        const counters = document.querySelectorAll('.stat-number');

        counters.forEach(counter => {
            if (counter.classList.contains('counted')) return;

            const target = parseInt(counter.textContent);
            if (isNaN(target)) return;

            let start = 0;
            const increment = target / 50; // 50 шагов анимации
            const timer = setInterval(() => {
                start += increment;
                counter.textContent = Math.floor(start);

                if (start >= target) {
                    counter.textContent = target;
                    counter.classList.add('counted');
                    clearInterval(timer);
                }
            }, 30);
        });
    }

    // =============================================================================
    // АНИМАЦИИ HOVER ЭФФЕКТОВ
    // =============================================================================
    function initializeHoverEffects() {
        // Анимация кнопок
        const buttons = document.querySelectorAll('.hero-btn, .hero-btn-secondary');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px) scale(1.02)';
            });

            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });

        // Анимация карточек
        const cards = document.querySelectorAll('.unified-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                const image = this.querySelector('.card-image');
                if (image) {
                    image.style.transform = 'scale(1.05)';
                }
            });

            card.addEventListener('mouseleave', function() {
                const image = this.querySelector('.card-image');
                if (image) {
                    image.style.transform = 'scale(1)';
                }
            });
        });
    }

    // =============================================================================
    // ПЛАВНАЯ ПРОКРУТКА ДЛЯ ЯКОРНЫХ ССЫЛОК
    // =============================================================================
    function initializeSmoothScroll() {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');

        anchorLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;

                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // =============================================================================
    // ИНИЦИАЛИЗАЦИЯ MASONRY ДЛЯ ВСЕХ РАЗДЕЛОВ
    // =============================================================================
    function initializeMasonry() {
        if (typeof Masonry === 'undefined') {
            console.warn('Masonry library is not loaded. Skipping Masonry initialization.');
            return;
        }

        document.querySelectorAll('.unified-masonry').forEach(grid => {
            // Проверяем, не была ли инициализация уже выполнена
            if (grid.dataset.masonryInitialized === 'true') {
                return;
            }

            try {
                const msnry = new Masonry(grid, {
                    itemSelector: '[class^="col-"], [class*=" col-"]',
                    percentPosition: true,
                    transitionDuration: '0.3s',
                });

                // Пересчёт после загрузки всех изображений для правильного выравнивания
                if (typeof imagesLoaded !== 'undefined') {
                    imagesLoaded(grid, () => {
                        msnry.layout();
                    });
                }

                // Адаптация при изменении размера окна
                window.addEventListener('resize', () => {
                    msnry.layout();
                });

                grid.dataset.masonryInitialized = 'true';
                console.log('Masonry initialized for grid:', grid);
            } catch (e) {
                console.error('Failed to initialize Masonry:', e);
            }
        });
    }

    // =============================================================================
    // ИНИЦИАЛИЗАЦИЯ ВСЕХ ЭФФЕКТОВ
    // =============================================================================
    initializeCustomAnimations();
    initializeHoverEffects();
    initializeSmoothScroll();
    initializeMasonry();

    // Для совместимости с галереей - триггер события готовности
    const event = new CustomEvent('animationsReady');
    document.dispatchEvent(event);
});

// =============================================================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// =============================================================================

/**
 * Функция для принудительного обновления всех анимаций
 */
window.refreshAllAnimations = function() {
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }

    // Удаляем маркеры анимаций для повторного запуска
    document.querySelectorAll('.animated, .counted').forEach(el => {
        el.classList.remove('animated', 'counted');
    });

    // Переинициализируем
    setTimeout(() => {
        initializeCustomAnimations();
    }, 100);
};

/**
 * Функция для добавления анимации появления к элементу
 */
window.addFadeInAnimation = function(element, delay = 0) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';

    setTimeout(() => {
        element.style.transition = 'all 0.6s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, delay);
};
