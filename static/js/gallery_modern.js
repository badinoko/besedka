/**
 * СОВРЕМЕННАЯ ГАЛЕРЕЯ - JavaScript функциональность v20250609080
 * Включает: систему лайков с анимацией, AJAX запросы, Masonry layout
 */

class ModernGallery {
    constructor() {
        this.masonryInstance = null;
        this.likeAnimationTimeout = null;
        this.init();
    }

    init() {
        this.initMasonry();
        // Отключаем систему лайков на странице "Мои фотографии"
        // this.initLikeSystem();
        this.initSearchForm();
        this.initScrollAnimations();
        this.initImageLazyLoading();
    }

    /**
     * Инициализация layout галереи
     */
    initMasonry() {
        // Проверяем, есть ли галерея на странице
        const grid = document.querySelector('.gallery-masonry');
        if (!grid) return;

        // Инициализируем Masonry для адаптивной сетки
        try {
            this.masonryInstance = new Masonry(grid, {
                itemSelector: '.gallery-card',
                percentPosition: true,
                gutter: 20
            });

            console.log('Masonry initialized successfully');

            // Обновляем layout после загрузки изображений
            window.addEventListener('load', () => {
                setTimeout(() => {
                    if (this.masonryInstance) {
                        this.masonryInstance.layout();
                    }
                }, 500);
            });
        } catch (error) {
            console.error('Failed to initialize Masonry:', error);
        }
    }

    /**
     * Система лайков с анимацией
     * ОТКЛЮЧЕНА для страницы "Мои фотографии"
     * ДОСТУПНА только на детальной странице фото
     */
    initLikeSystem() {
        // Проверяем, находимся ли мы на детальной странице
        const isDetailPage = window.location.pathname.includes('/photo/') &&
                            !window.location.pathname.includes('/edit/') &&
                            !window.location.pathname.includes('/delete/');

        if (!isDetailPage) {
            // Не инициализируем лайки вне детальной страницы
            console.log('Like system disabled - not on detail page');
            return;
        }

        document.addEventListener('click', (e) => {
            const likeBtn = e.target.closest('.like-btn');
            if (!likeBtn || likeBtn.disabled) return;

            e.preventDefault();
            e.stopPropagation(); // Предотвращаем всплытие
            this.handleLike(likeBtn);
        });
    }

    /**
     * Обработка лайка
     */
    async handleLike(likeBtn) {
        const photoId = likeBtn.dataset.photoId;
        const likeUrl = likeBtn.dataset.url;

        if (!photoId || !likeUrl) {
            console.error('Missing photo ID or URL');
            return;
        }

        // Блокируем кнопку на время запроса
        likeBtn.disabled = true;

        try {
            const response = await fetch(likeUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'ok') {
                this.updateLikeButton(likeBtn, data);
                this.animateLike(likeBtn, data.action === 'liked');

                // Показываем сообщение об успехе
                if (data.message) {
                    window.showNotification(data.message, 'success');
                }
            } else {
                console.error('Like error:', data.error || data.message);
                window.showNotification('Ошибка при обработке лайка', 'error');
            }
        } catch (error) {
            console.error('Like request failed:', error);
            window.showNotification('Ошибка сети. Попробуйте позже.', 'error');
        } finally {
            // Разблокируем кнопку
            setTimeout(() => {
                likeBtn.disabled = false;
            }, 500);
        }
    }

    /**
     * Обновление кнопки лайка
     */
    updateLikeButton(likeBtn, data) {
        const likeCount = likeBtn.querySelector('.like-count');
        if (likeCount) {
            likeCount.textContent = data.likes_count;
        }

        // Обновляем состояние кнопки (для необратимых лайков)
        if (data.action === 'liked') {
            likeBtn.classList.add('liked');
        }
    }

    /**
     * Анимация лайка
     */
    animateLike(likeBtn, isLiked) {
        // Анимация кнопки
        likeBtn.style.transform = 'scale(1.2)';
        setTimeout(() => {
            likeBtn.style.transform = 'scale(1)';
        }, 200);

        // Анимация частиц только при лайке
        if (isLiked) {
            this.createLikeParticles(likeBtn);
        }

        // Добавляем класс для CSS анимации (необратимые лайки)
        likeBtn.classList.add('animation');
        setTimeout(() => {
            likeBtn.classList.remove('animation');
            // Для необратимых лайков - класс liked остается навсегда
            if (isLiked) {
                likeBtn.classList.add('liked');
            }
        }, 600);
    }

    /**
     * Создание анимации частиц
     */
    createLikeParticles(likeBtn) {
        const particles = likeBtn.querySelector('.like-particles');
        if (!particles) return;

        // Создаем несколько частиц
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.innerHTML = '❤️';
                particle.style.position = 'absolute';
                particle.style.fontSize = '12px';
                particle.style.pointerEvents = 'none';
                particle.style.zIndex = '1000';

                // Случайное позиционирование
                const angle = (Math.PI * 2 * i) / 5;
                const distance = 30 + Math.random() * 20;
                const x = Math.cos(angle) * distance;
                const y = Math.sin(angle) * distance;

                particle.style.left = '50%';
                particle.style.top = '50%';
                particle.style.transform = `translate(-50%, -50%)`;

                particles.appendChild(particle);

                // Анимация частицы
                particle.animate([
                    {
                        transform: `translate(-50%, -50%) scale(0)`,
                        opacity: 1
                    },
                    {
                        transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px)) scale(1)`,
                        opacity: 1
                    },
                    {
                        transform: `translate(calc(-50% + ${x * 2}px), calc(-50% + ${y * 2}px)) scale(0)`,
                        opacity: 0
                    }
                ], {
                    duration: 800,
                    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
                }).onfinish = () => {
                    particle.remove();
                };
            }, i * 100);
        }
    }

    /**
     * Инициализация формы поиска
     */
    initSearchForm() {
        const searchForm = document.querySelector('.search-form');
        if (!searchForm) return;

        const searchInput = searchForm.querySelector('.search-input');
        const sortSelect = searchForm.querySelector('.sort-select');

        // Автоматическая отправка при изменении сортировки
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                searchForm.submit();
            });
        }

        // Debounced поиск
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (searchInput.value.length >= 3 || searchInput.value.length === 0) {
                        searchForm.submit();
                    }
                }, 500);
            });
        }
    }

    /**
     * Анимации при скролле
     */
    initScrollAnimations() {
        // Параллакс эффект ОТКЛЮЧЕН - мешал прокрутке
        // const hero = document.querySelector('.gallery-hero');
        // if (hero) {
        //     window.addEventListener('scroll', () => {
        //         const scrolled = window.pageYOffset;
        //         const rate = scrolled * -0.5;
        //         hero.style.transform = `translateY(${rate}px)`;
        //     });
        // }

        // Показ/скрытие кнопки "наверх"
        this.initScrollToTop();
    }

    /**
     * Кнопка "наверх"
     */
    initScrollToTop() {
        // Создаем кнопку если её нет
        let scrollTopBtn = document.querySelector('.scroll-top-btn');
        if (!scrollTopBtn) {
            scrollTopBtn = document.createElement('button');
            scrollTopBtn.className = 'scroll-top-btn';
            scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
            scrollTopBtn.style.cssText = `
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, var(--gallery-primary), var(--gallery-secondary));
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                z-index: 1000;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            `;
            document.body.appendChild(scrollTopBtn);
        }

        // Показ/скрытие при скролле
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                scrollTopBtn.style.opacity = '1';
                scrollTopBtn.style.visibility = 'visible';
            } else {
                scrollTopBtn.style.opacity = '0';
                scrollTopBtn.style.visibility = 'hidden';
            }
        });

        // Плавный скролл наверх
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    /**
     * Ленивая загрузка изображений
     */
    initImageLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
        // Пробуем получить из глобальной переменной
        if (typeof csrfToken !== 'undefined') {
            return csrfToken;
        }

        // Пробуем получить из cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }

        // Пробуем получить из meta тега
        if (!cookieValue) {
            const csrfMeta = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfMeta) {
                cookieValue = csrfMeta.getAttribute('content');
            }
        }

        return cookieValue;
    }

    // Удалено: используется глобальная система уведомлений window.showNotification

    /**
     * Обновление layout галереи
     */
    updateMasonryLayout() {
        // CSS Grid не требует обновления layout
        console.log('CSS Grid layout updated');
    }

    /**
     * Уничтожение экземпляра
     */
    destroy() {
        if (this.masonryInstance) {
            this.masonryInstance.destroy();
        }
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    window.modernGallery = new ModernGallery();
});

// Обновление layout при изменении размера окна
window.addEventListener('resize', () => {
    if (window.modernGallery) {
        setTimeout(() => {
            window.modernGallery.updateMasonryLayout();
        }, 300);
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModernGallery;
}
