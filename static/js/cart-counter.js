/**
 * Глобальный менеджер счетчика корзины для всего сайта
 */
window.CartCounter = {
    /**
     * Обновляет счетчик корзины в шапке
     * @param {number} totalItems - общее количество товаров в корзине
     */
    update: function(totalItems) {
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            // Обновляем основной текст, сохраняя скрытый span
            const hiddenSpan = cartBadge.querySelector('.visually-hidden');
            if (hiddenSpan) {
                cartBadge.innerHTML = `${totalItems}${hiddenSpan.outerHTML}`;
            } else {
                cartBadge.textContent = totalItems.toString();
            }

            // Показываем или скрываем бейдж в зависимости от количества
            if (totalItems > 0) {
                cartBadge.style.display = 'flex';
                cartBadge.style.animation = 'badgeAppear 0.3s ease-out';
            } else {
                cartBadge.style.display = 'none';
            }

            console.log(`✅ Счетчик корзины обновлен: ${totalItems} товаров`);
        } else {
            console.warn('⚠️ Элемент .cart-badge не найден в DOM');
        }
    },

    /**
     * Инициализация счетчика при загрузке страницы
     */
    init: function() {
        // Проверяем, что счетчик корзины присутствует
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            console.log('✅ CartCounter инициализирован');
            // Логируем текущее значение
            const currentValue = cartBadge.textContent ? cartBadge.textContent.trim() : '0';
            console.log(`Текущее значение счетчика: "${currentValue}"`);
        } else {
            console.log('ℹ️ Счетчик корзины не найден на данной странице (это нормально для некоторых страниц)');
        }
    }
};

// Автоматическая инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем небольшую задержку для обеспечения полной загрузки DOM
    setTimeout(function() {
        if (typeof window.CartCounter !== 'undefined') {
            window.CartCounter.init();
        }
    }, 100);
});
