# 🎨 Стандарты UI/UX проекта "Беседка"

## 📋 Документ версии 5.0 - ФИНАЛЬНЫЕ СТАНДАРТЫ HERO-СЕКЦИЙ (Июнь 2025)

**📋 СВЯЗАННЫЕ ДОКУМЕНТЫ:**
- **[BESEDKA_MASTER_DOCUMENTATION.md](BESEDKA_MASTER_DOCUMENTATION.md)** — главная документация проекта, архитектура, критические победы
- **[BESEDKA_USER_SYSTEM.md](BESEDKA_USER_SYSTEM.md)** — система ролей и полномочий (эталон)
- **[MASTER_COMPLETION_PROMPT.md](MASTER_COMPLETION_PROMPT.md)** — детальный план завершения проекта

Данный документ описывает унифицированные стандарты дизайна и пользовательского интерфейса для всех разделов платформы "Беседка".

---

## ✅ КРИТИЧЕСКАЯ ПОБЕДА - ПОЛНАЯ УНИФИКАЦИЯ ЗАВЕРШЕНА!

### 🎯 УНИФИЦИРОВАННЫЕ РАЗДЕЛЫ (100% готовность):
1. **Галерея** (`gallery_modern.html`) — ЭТАЛОН ✅
2. **Гроурепорты** (`growlogs/list.html`) — ЭТАЛОН ✅
3. **Новости** (`news/home.html`) — УНИФИЦИРОВАНЫ ✅
4. **Магазин** (`store/catalog.html`) — УНИФИЦИРОВАНЫ ✅
5. **Мои фотографии** (`gallery/my_photos.html`) — **ФИНАЛЬНО ИСПРАВЛЕНЫ** ✅
6. **Детальная страница фото** (`gallery/photo_detail.html`) — УНИФИЦИРОВАНЫ ✅
7. **Главная страница** (`pages/home.html`) — УНИФИЦИРОВАНЫ ✅

### 🔧 ПОСЛЕДНЕЕ ИСПРАВЛЕНИЕ: "МОИ ФОТОГРАФИИ"
**Проблема**: Страница содержала inline CSS стили и не соответствовала эталонной структуре
**Решение**: Полная реструктуризация с приведением к стандартам:
- Убраны все inline стили
- Добавлены классы `.photo-badge`, `.action-btn`, `.stat-icon`
- Исправлена структура hero-секции
- Обновлен CSS файл `gallery_modern.css` v20250608013

---

## 🚀 УНИФИЦИРОВАННАЯ СТРУКТУРА СТРАНИЦ

### 📐 БАЗОВАЯ РАЗМЕТКА
Каждая страница следует единой структуре:

```html
{% extends "base.html" %}
{% load static %}
{% load i18n %}
{% load humanize %}

{% block title %}[EMOJI] [НАЗВАНИЕ РАЗДЕЛА]{% endblock %}

{% block extra_css %}
<!-- AOS Animation -->
<link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
<!-- Унифицированные hero-кнопки -->
<link rel="stylesheet" href="{% static 'css/unified_hero_buttons.css' %}?v=20250608">
<!-- Специфичные стили раздела -->
<link rel="stylesheet" href="{% static 'css/[section]_modern.css' %}?v=[version]">
{% endblock %}

{% block content %}
<div class="[section]-page">
    <div class="hero-container">
        <div class="container">
            <!-- КОМПАКТНАЯ ГЕРОЙ СЕКЦИЯ -->
            <div class="[section]-hero" data-aos="fade-up" data-aos-duration="600">
                <!-- Содержимое hero -->
            </div>
        </div>
    </div>

    <div class="content-container">
        <div class="container">
            <!-- ФИЛЬТРЫ -->
            <div class="[section]-filters" data-aos="fade-up" data-aos-delay="300">
                <!-- Содержимое фильтров -->
            </div>

            <!-- ОСНОВНОЙ КОНТЕНТ -->
            <div class="[section]-content">
                <!-- Карточки/список/галерея -->
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<!-- AOS Animation -->
<script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
<!-- Специфичная логика раздела -->
{% endblock %}
```

### 🎯 HERO-СЕКЦИЯ КОМПАКТНАЯ
Точные размеры как в гроурепортах и новостях:

```html
<div class="[section]-hero" data-aos="fade-up" data-aos-duration="600">
    <div class="container">
        <div class="hero-content text-center">
            <h1 class="hero-title">[EMOJI] [НАЗВАНИЕ]</h1>
            <p class="hero-subtitle">[КРАТКОЕ ОПИСАНИЕ]</p>

            <div class="hero-stats">
                <div class="stat-item" data-aos="zoom-in" data-aos-delay="100">
                    <span class="stat-number">{{ count_1 }}</span>
                    <span class="stat-label">Метрика 1</span>
                </div>
                <div class="stat-item" data-aos="zoom-in" data-aos-delay="200">
                    <span class="stat-number">{{ count_2 }}</span>
                    <span class="stat-label">Метрика 2</span>
                </div>
                <!-- Дополнительные счетчики -->
            </div>

            <div class="hero-actions">
                <a href="[URL]" class="hero-btn me-3" data-aos="fade-in" data-aos-delay="150">
                    <i class="fas fa-[icon] me-2"></i>[ГЛАВНОЕ ДЕЙСТВИЕ]
                </a>
                <a href="[URL]" class="hero-btn-secondary" data-aos="fade-in" data-aos-delay="200">
                    <i class="fas fa-[icon] me-2"></i>[ВТОРИЧНОЕ ДЕЙСТВИЕ]
                </a>
            </div>
        </div>
    </div>
</div>
```

### 📏 ФИКСИРОВАННЫЕ РАЗМЕРЫ HERO
```css
.[section]-hero {
    padding: 1rem 0 !important;       /* Компактный размер */
    margin-bottom: 2rem;
    border-radius: 1rem;
}

.[section]-filters {
    padding: 0.5rem !important;       /* Компактные фильтры */
    margin: 0 0 1rem 0 !important;
}
```

---

## 🔲 ФИНАЛЬНЫЕ HERO-КНОПКИ (ЭТАЛОН V23.0)

Этот раздел описывает финальный, утвержденный стандарт для всех кнопок в hero-секциях. Эти стили обеспечивают **3D-эффект "парения"**, **постоянную "живую" анимацию** и консистентность во всех разделах.

### 1. ОБЩИЕ ПАРАМЕТРЫ И 3D-ЭФФЕКТ

Все кнопки (`.hero-btn` и `.hero-btn-secondary`) имеют общие стили для размера, шрифта и, что самое важное, **эффекта "парения"**.

- **Постоянное "парение"**: Кнопки по умолчанию имеют сложную, многослойную тень, которая создает ощущение глубины и отрывает их от фона.
- **Всплытие при наведении**: При наведении курсора тень становится еще глубже и объемнее, а сама кнопка приподнимается на `6px`, создавая явный 3D-эффект.

```css
/* ОБЩИЕ СТИЛИ */
.hero-btn,
.hero-btn-secondary {
    padding: 16px 32px !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    border-radius: 14px !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    /* ... другие общие стили ... */
    position: relative !important;
    overflow: hidden !important;

    /* 🎯 Постоянный эффект "парения" с новой, сильной тенью */
    box-shadow: 0 2.8px 2.2px rgba(0, 0, 0, 0.034),
                0 6.7px 5.3px rgba(0, 0, 0, 0.048),
                0 12.5px 10px rgba(0, 0, 0, 0.06),
                0 22.3px 17.9px rgba(0, 0, 0, 0.072),
                0 41.8px 33.4px rgba(0, 0, 0, 0.086),
                0 100px 80px rgba(0, 0, 0, 0.12) !important;
    transform: translateY(0) !important;
}

/* 🎯 Усиление 3D-эффекта при наведении */
.hero-btn:hover,
.hero-btn-secondary:hover {
    box-shadow: 0 4px 2.2px rgba(0, 0, 0, 0.05),
                0 9.6px 5.3px rgba(0, 0, 0, 0.07),
                0 18.1px 10px rgba(0, 0, 0, 0.09),
                0 32.3px 17.9px rgba(0, 0, 0, 0.11),
                0 60.4px 33.4px rgba(0, 0, 0, 0.13),
                0 145px 80px rgba(0, 0, 0, 0.2) !important;
    transform: translateY(-6px) !important;
}
```

### 2. ОСНОВНАЯ КНОПКА `.hero-btn`

- **Внешний вид**: Цветной градиент, зависящий от раздела.
- **Анимация**: **Постоянное, бесшовное переливание градиента (`shimmer`)**. Анимация работает всегда, а не только при наведении.

```css
/* ОСНОВНАЯ КНОПКА */
.hero-btn {
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    background-size: 250% 100% !important;
    animation: shimmer 5s ease-in-out infinite;
}

/* Бесшовная анимация переливания */
@keyframes shimmer {
    0%   { background-position: 0% center; }
    50%  { background-position: 100% center; }
    100% { background-position: 0% center; }
}

/* 🎨 ЦВЕТОВЫЕ СХЕМЫ */
.gallery-hero .hero-btn { background-image: linear-gradient(135deg, #8A2BE2 0%, #4B0082 50%, #8A2BE2 100%) !important; }
.growlogs-hero .hero-btn { background-image: linear-gradient(135deg, #32CD32 0%, #006400 50%, #32CD32 100%) !important; }
.news-hero .hero-btn { background-image: linear-gradient(135deg, #1E90FF 0%, #00008B 50%, #1E90FF 100%) !important; }
.store-hero .hero-btn { background-image: linear-gradient(135deg, #28a745 0%, #1e7e34 50%, #28a745 100%) !important; }
```

### 3. ВТОРИЧНАЯ КНОПКА `.hero-btn-secondary`

- **Внешний вид**: Полупрозрачная "стеклянная" кнопка с `backdrop-filter`.
- **Анимация**: **Постоянный, бесшовный "скользящий блик" (`glare`)**. Анимация имитирует отражение света, которое плавно проходит по кнопке, а затем возвращается обратно.

```css
/* ВТОРИЧНАЯ КНОПКА */
.hero-btn-secondary {
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

/* Псевдо-элемент для создания блика */
.hero-btn-secondary::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: linear-gradient(
        100deg,
        rgba(255, 255, 255, 0) 20%,
        rgba(255, 255, 255, 0.25) 50%,
        rgba(255, 255, 255, 0) 80%
    );
    background-size: 200% 100%;
    animation: glare 5s ease-in-out infinite;
    animation-delay: 0.5s; /* Рассинхронизация с основной кнопкой */
}

/* Бесшовная анимация блика */
@keyframes glare {
    0% { background-position: 170% 0; }
    50% { background-position: -170% 0; }
    100% { background-position: 170% 0; }
}
```

---

## 📊 АДАПТИВНЫЕ СЧЕТЧИКИ (Финальная версия)

### ✅ Улучшенная видимость для больших чисел
```css
.stat-item {
    text-align: center;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 0.5rem 0.7rem;
    min-width: 100px;
    width: auto;
    max-width: 140px;      /* Адаптивная ширина */
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.stat-number {
    display: block;
    font-size: 1.3rem;     /* Оптимальный размер */
    font-weight: 700;
    color: #ffffff;        /* Белый для контраста */
    line-height: 1;
    margin-bottom: 0.3rem;
    word-break: break-all;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-shadow: 0 1px 3px rgba(0,0,0,0.3);  /* Тень для читаемости */
}

.stat-label {
    font-size: 0.75rem;
    color: #ffffff;
    opacity: 0.95;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    line-height: 1.2;
    word-break: break-word;
    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}
```

---

## 🔄 СИСТЕМА ФИЛЬТРОВ

### 📋 Стандартная структура фильтров
```html
<div class="[section]-filters" data-aos="fade-up" data-aos-delay="300">
    <div class="filter-tabs">
        <button class="filter-tab active" data-filter="all">
            <i class="fas fa-[icon]"></i>
            Все
        </button>
        <button class="filter-tab" data-filter="category1">
            <i class="fas fa-[icon]"></i>
            Категория 1
        </button>
        <!-- Дополнительные фильтры -->
    </div>
</div>
```

### 🎨 Стили фильтров
```css
.[section]-filters {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 0.5rem !important;
    margin: 0 0 1rem 0 !important;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
}

.filter-tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 1.5rem;
    color: #2d3748;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}

.filter-tab:hover {
    background: rgba(111, 66, 193, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(111, 66, 193, 0.3);
}

.filter-tab.active {
    background: linear-gradient(135deg, [primary-color], [secondary-color]);
    color: white;
    box-shadow: 0 4px 15px rgba(111, 66, 193, 0.4);
}
```

---

## 🃏 КАРТОЧКИ И ЭЛЕМЕНТЫ

### 📱 Карточки фотографий/товаров
```html
<div class="gallery-card" data-aos="fade-up">
    <a href="[url]" data-pswp-width="[width]" data-pswp-height="[height]">
        <div class="photo-container">
            <img src="[image]" class="photo-image" alt="[alt]">
            <!-- Бейджи -->
            <div class="photo-badge private-badge">
                <i class="fas fa-eye-slash"></i> Приватное
            </div>
            <div class="photo-badge growlog-badge">
                <i class="fas fa-seedling"></i> Гроу-репорт
            </div>
        </div>
    </a>
    <div class="card-info">
        <!-- Информация о карточке -->
        <div class="card-footer">
            <div class="photo-stats">
                <div class="stat-icon">
                    <i class="fas fa-heart"></i>
                    <span>{{ likes_count }}</span>
                </div>
                <div class="stat-icon">
                    <i class="fas fa-comment"></i>
                    <span>{{ comments_count }}</span>
                </div>
            </div>
            <div class="card-actions">
                <a href="[url]" class="action-btn view-btn">
                    <i class="fas fa-eye"></i> Смотреть
                </a>
                <a href="[url]" class="action-btn edit-btn">
                    <i class="fas fa-edit"></i> Править
                </a>
                <a href="[url]" class="action-btn delete-btn">
                    <i class="fas fa-trash"></i> Удалить
                </a>
            </div>
        </div>
    </div>
</div>
```

### 🎨 CSS для карточек и кнопок действий
```css
.photo-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    padding: 4px 8px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
    z-index: 5;
}

.private-badge {
    background: rgba(0,0,0,0.8);
    color: white;
}

.growlog-badge {
    background: rgba(40, 167, 69, 0.9);
    color: white;
    top: 40px;
}

.action-btn {
    padding: 6px 12px;
    border-radius: 8px;
    text-decoration: none;
    font-size: 0.8rem;
    font-weight: 500;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
}

.view-btn {
    background: linear-gradient(135deg, #6f42c1, #553c9a);
    color: white;
}

.edit-btn {
    background: linear-gradient(135deg, #17a2b8, #138496);
    color: white;
}

.delete-btn {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
}
```

---

## 📱 АДАПТИВНОСТЬ И АНИМАЦИИ

### 🎬 AOS Анимации
Стандартные анимации для всех элементов:

```html
<!-- Hero-секция -->
<div data-aos="fade-up" data-aos-duration="600">

<!-- Счетчики -->
<div data-aos="zoom-in" data-aos-delay="100">
<div data-aos="zoom-in" data-aos-delay="200">
<div data-aos="zoom-in" data-aos-delay="300">

<!-- Кнопки -->
<a data-aos="fade-in" data-aos-delay="150">
<a data-aos="fade-in" data-aos-delay="200">

<!-- Фильтры -->
<div data-aos="fade-up" data-aos-delay="300">

<!-- Карточки -->
<div data-aos="fade-up" data-aos-delay="[динамическая]">
```

### 📐 Медиа-запросы
```css
/* Планшеты */
@media (max-width: 768px) {
    .gallery-card {
        flex: 0 0 calc(50% - 20px);
        max-width: calc(50% - 20px);
    }
    .hero-title {
        font-size: 1.8rem;
    }
    .filter-tabs {
        justify-content: center;
        gap: 0.3rem;
    }
}

/* Мобильные */
@media (max-width: 576px) {
    .gallery-card {
        flex: 0 0 calc(100% - 20px);
        max-width: calc(100% - 20px);
    }
    .hero-title {
        font-size: 1.5rem;
    }
    .hero-stats {
        gap: 0.5rem;
    }
    .stat-item {
        min-width: 80px;
        padding: 0.4rem 0.6rem;
    }
}
```

---

## 📂 ФАЙЛОВАЯ СТРУКТУРА CSS

### 🗂️ Основные файлы стилей:
1. **`unified_hero_buttons.css`** — унифицированные кнопки для всех разделов
2. **`gallery_modern.css`** — стили галереи и "Мои фото"
3. **`project.css`** — базовые стили проекта
4. **`chat_modal.css`** — стили чата

### 📋 Версионирование CSS
Всегда используется версионирование для принудительного обновления кеша:
```html
<link rel="stylesheet" href="{% static 'css/file.css' %}?v=20250608">
```

### ⚠️ КРИТИЧЕСКИ ВАЖНО
1. **НЕ использовать inline стили** в шаблонах
2. **ВСЕГДА подключать** unified_hero_buttons.css
3. **НЕ дублировать** стили кнопок в локальных CSS
4. **ИСПОЛЬЗОВАТЬ** компактные размеры hero-секций
5. **ОБНОВЛЯТЬ версии** CSS после изменений

---

## 🎯 ИСТОРИЯ ИЗМЕНЕНИЙ

### Версия 5.0 (Июнь 2025) - ФИНАЛЬНЫЕ HERO-КНОПКИ
✅ **ПОЛНАЯ ПОЛИРОВКА ЗАВЕРШЕНА:**
- **3D-эффект**: Реализованы сложные, многослойные тени для постоянного эффекта "парения" и его усиления при наведении.
- **Постоянные анимации**: Обе кнопки теперь имеют "живую" анимацию по умолчанию, призывающую к действию.
- **Бесшовность**: Анимации на обеих кнопках сделаны бесшовными (движение туда-обратно), устранен эффект "перезапуска".
- **Синхронизация**: Скорости анимаций синхронизированы, устранен баг с одновременным срабатыванием.

✅ **ОБНОВЛЕННЫЕ ФАЙЛЫ:**
- `static/css/unified_hero_buttons.css` v20250609070 — финальная версия стилей.
- `BESEDKA_UI_STANDARDS.md` v5.0 — полное обновление документации.

✅ **РЕШЕННЫЕ ПРОБЛЕМЫ:**
- Белый фон на странице "Мои фото"
- Ошибки в консоли AOS
- Некорректные размеры hero-секции
- Отсутствие стилей для бейджей и кнопок

✅ **ТЕХНИЧЕСКИЕ УЛУЧШЕНИЯ:**
- PhotoSwipe интеграция для лайтбокса
- Masonry для адаптивной сетки фотографий
- Улучшенная фильтрация по типам фото
- Корректная пагинация

### Версия 3.0 (Июнь 2025) - УНИФИКАЦИЯ HERO-КНОПОК
- Создана система унифицированных hero-кнопок
- Автоматические цветовые схемы по разделам
- Анимации переливания и затенения
- Обновлены все разделы с новыми кнопками

---

## 📋 ЧЕКЛИСТ ДЛЯ НОВЫХ РАЗДЕЛОВ

При создании нового раздела убедитесь:
- [ ] Подключен `unified_hero_buttons.css`
- [ ] Используется компактная hero-секция (padding: 1rem 0)
- [ ] Применены AOS анимации
- [ ] Добавлены адаптивные счетчики
- [ ] Используются классы `.hero-btn` и `.hero-btn-secondary`
- [ ] Фильтры имеют глаз morphism эффект
- [ ] Карточки содержат правильную структуру
- [ ] Медиа-запросы для мобильных устройств
- [ ] Версионирование CSS файлов

---

## 🚀 ЗАКЛЮЧЕНИЕ

Система UI/UX проекта "Беседка" достигла полной унификации. Все 7 основных разделов теперь следуют единым стандартам дизайна, обеспечивая консистентный пользовательский опыт на всей платформе.

**Ключевые достижения:**
- ✅ Полная унификация всех разделов
- ✅ Система hero-кнопок с анимациями
- ✅ Адаптивные и читаемые счетчики
- ✅ Современные фильтры с glassmorphism
- ✅ Отзывчивый дизайн для всех устройств

Проект готов к финальному этапу развертывания в продакшн.
