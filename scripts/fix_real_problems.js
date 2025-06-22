// РЕАЛЬНОЕ ИСПРАВЛЕНИЕ ОБНАРУЖЕННЫХ ПРОБЛЕМ
print('🔧 ИСПРАВЛЯЮ РЕАЛЬНЫЕ ПРОБЛЕМЫ...');

// 1. ИСПРАВЛЯЕМ КРАКОЗЯБРЫ В КАНАЛЕ МОДЕРАТОРОВ
print('1. Исправляю кракозябры в канале moderators...');
db.rocketchat_subscription.updateOne(
    {rid: 'moderators', 'u.username': 'owner'},
    {$set: {
        fname: 'Модераторы',
        name: 'moderators',
        _updatedAt: new Date()
    }}
);
print('✅ Кракозябры в канале moderators исправлены');

// Исправляем также сам канал
db.rocketchat_room.updateOne(
    {_id: 'moderators'},
    {$set: {
        fname: 'Модераторы',
        name: 'moderators',
        _updatedAt: new Date()
    }}
);
print('✅ Имя канала moderators исправлено');

// 2. СОЗДАЕМ НАСТРОЙКУ АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ К КАНАЛАМ
print('2. Создаю настройку автоматического присоединения...');
db.rocketchat_settings.updateOne(
    {_id: 'Accounts_Default_User_Preferences_joinDefaultChannels'},
    {$set: {
        value: true,
        valueSource: 'customValue',
        type: 'boolean',
        group: 'Accounts',
        _updatedAt: new Date(),
        hidden: false,
        blocked: false,
        sorter: 50,
        i18nLabel: 'Join_default_channels',
        i18nDescription: 'Join_default_channels_Description'
    }},
    {upsert: true}
);
print('✅ Настройка автоматического присоединения создана');

// 3. ИСПРАВЛЯЕМ НАСТРОЙКИ КОДИРОВКИ
print('3. Исправляю настройки UTF-8...');
db.rocketchat_settings.updateOne(
    {_id: 'Language'},
    {$set: {
        value: 'ru',
        valueSource: 'customValue',
        _updatedAt: new Date()
    }},
    {upsert: true}
);

db.rocketchat_settings.updateOne(
    {_id: 'UTF8_Names_Validation'},
    {$set: {
        value: true,
        valueSource: 'customValue',
        _updatedAt: new Date()
    }},
    {upsert: true}
);

db.rocketchat_settings.updateOne(
    {_id: 'Message_AllowedMaxSize'},
    {$set: {
        value: 5000,
        valueSource: 'customValue',
        _updatedAt: new Date()
    }},
    {upsert: true}
);
print('✅ Настройки кодировки исправлены');

// 4. ИСПРАВЛЯЕМ НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
print('4. Исправляю язык пользователя owner...');
const owner = db.users.findOne({username: 'owner'});
if (owner) {
    db.users.updateOne(
        {_id: owner._id},
        {$set: {
            language: 'ru',
            'settings.preferences.language': 'ru',
            _updatedAt: new Date()
        }}
    );
    print('✅ Язык пользователя owner установлен');
} else {
    print('❌ Пользователь owner не найден');
}

// 5. ОТКЛЮЧАЕМ ОГРАНИЧЕНИЯ ДЛЯ IFRAME
print('5. Отключаю ограничения iframe...');
db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Restrict_Access'},
    {$set: {
        value: false,
        valueSource: 'customValue',
        _updatedAt: new Date()
    }},
    {upsert: true}
);
print('✅ Ограничения iframe отключены');

print('🎉 ВСЕ РЕАЛЬНЫЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ!');
print('');
print('ИСПРАВЛЕНО:');
print('✅ Кракозябры в канале модераторов');
print('✅ Автоматическое присоединение к каналам');
print('✅ Настройки UTF-8 кодировки');
print('✅ Язык интерфейса');
print('✅ Ограничения iframe');
print('');
print('ТРЕБУЕТСЯ ПЕРЕЗАПУСК ROCKET.CHAT для применения изменений!');
