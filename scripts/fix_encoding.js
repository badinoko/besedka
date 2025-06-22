// ИСПРАВЛЕНИЕ ПРОБЛЕМ С КОДИРОВКОЙ В ROCKET.CHAT
print('🔧 ИСПРАВЛЯЮ ПРОБЛЕМЫ С КОДИРОВКОЙ...');

// 1. Настройки языка и кодировки
db.rocketchat_settings.updateOne(
    {_id: 'Language'},
    {$set: {value: 'ru', _updatedAt: new Date()}},
    {upsert: true}
);
print('✅ Язык установлен: русский');

// 2. Настройки по умолчанию для пользователей - русский язык
db.rocketchat_settings.updateOne(
    {_id: 'Accounts_Default_User_Preferences_language'},
    {$set: {value: 'ru', _updatedAt: new Date()}},
    {upsert: true}
);
print('✅ Язык по умолчанию: русский');

// 3. Исправляем кодировку для полей ввода
db.rocketchat_settings.updateOne(
    {_id: 'UTF8_Names_Validation'},
    {$set: {value: true, _updatedAt: new Date()}},
    {upsert: true}
);
print('✅ UTF-8 валидация включена');

// 4. Исправляем настройки сообщений
db.rocketchat_settings.updateOne(
    {_id: 'Message_AllowedMaxSize'},
    {$set: {value: 5000, _updatedAt: new Date()}},
    {upsert: true}
);
print('✅ Максимальный размер сообщения: 5000 символов');

// 5. Разрешаем все Unicode символы
db.rocketchat_settings.updateOne(
    {_id: 'UTF8_Names_Slugify'},
    {$set: {value: false, _updatedAt: new Date()}},
    {upsert: true}
);
print('✅ UTF-8 slugify отключен');

// 6. Проверяем и исправляем кодировку для пользователя owner
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
    print('✅ Язык пользователя owner установлен: русский');
}

print('🎉 КОДИРОВКА ИСПРАВЛЕНА! Все должно работать с русскими символами!');
