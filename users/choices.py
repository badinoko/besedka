"""
Выбор базовых аватарок для пользователей
"""

DEFAULT_AVATARS = [
    # Растения и природа
    ('plant_1.svg', '🌱 Росток'),
    ('plant_2.svg', '🌿 Листок'),
    ('plant_3.svg', '🌳 Дерево'),
    ('plant_4.svg', '🌺 Цветок'),
    ('plant_5.svg', '🌻 Подсолнух'),
    ('plant_6.svg', '🌹 Роза'),
    ('plant_7.svg', '🌵 Кактус'),
    ('plant_8.svg', '🍄 Гриб'),

    # Животные
    ('animal_1.svg', '🐱 Кот'),
    ('animal_2.svg', '🐶 Собака'),
    ('animal_3.svg', '🐰 Кролик'),
    ('animal_4.svg', '🐸 Лягушка'),
    ('animal_5.svg', '🦋 Бабочка'),
    ('animal_6.svg', '🐝 Пчела'),
    ('animal_7.svg', '🐧 Пингвин'),
    ('animal_8.svg', '🦊 Лиса'),

    # Абстрактные
    ('abstract_1.svg', '🔵 Синий круг'),
    ('abstract_2.svg', '🟢 Зеленый круг'),
    ('abstract_3.svg', '🟡 Желтый круг'),
    ('abstract_4.svg', '🟣 Фиолетовый круг'),
    ('abstract_5.svg', '🔶 Ромб'),
    ('abstract_6.svg', '⭐ Звезда'),
    ('abstract_7.svg', '💎 Кристалл'),
    ('abstract_8.svg', '🌈 Радуга'),

    # Символы
    ('symbol_1.svg', '⚡ Молния'),
    ('symbol_2.svg', '🔥 Огонь'),
    ('symbol_3.svg', '💧 Капля'),
    ('symbol_4.svg', '🌙 Луна'),
    ('symbol_5.svg', '☀️ Солнце'),
    ('symbol_6.svg', '❄️ Снежинка'),
]

def get_avatar_choices():
    """Возвращает список выборов аватарок для форм"""
    return [('', 'Загрузить свой аватар')] + [(f'/static/avatars/{filename}', name) for filename, name in DEFAULT_AVATARS]

def get_random_avatar():
    """Возвращает случайный аватар"""
    import random
    filename, _ = random.choice(DEFAULT_AVATARS)
    return f'/static/avatars/{filename}'
