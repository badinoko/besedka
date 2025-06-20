// Завершение настройки OAuth mapping и переключателей для провайдера Besedka

print('🔧 Дозаполняю недостающие OAuth настройки...');

// Дополнительные настройки которые пропустил первый скрипт
const additionalSettings = [
    // Переключатели которые должны быть включены
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_users', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-map_channels', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_roles', value: true },

    // Правильный JSON mapping для ролей Django -> Rocket.Chat каналы
    { _id: 'Accounts_OAuth_Custom-Besedka-channels_map', value: JSON.stringify({
        "owner": "admin,vip",
        "moderator": "admin",
        "user": "user"
    })},

    // Роли для синхронизации
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_to_sync', value: 'admin,moderator,vip,user' },

    // Дополнительные поля пользователя
    { _id: 'Accounts_OAuth_Custom-Besedka-username_field', value: 'username' },
    { _id: 'Accounts_OAuth_Custom-Besedka-email_field', value: 'email' },
    { _id: 'Accounts_OAuth_Custom-Besedka-name_field', value: 'full_name' },
    { _id: 'Accounts_OAuth_Custom-Besedka-avatar_field', value: 'avatar_url' },

    // Убеждаемся что кнопка показывается
    { _id: 'Accounts_OAuth_Custom-Besedka-show_button', value: true },

    // Цвета кнопки (стандартные)
    { _id: 'Accounts_OAuth_Custom-Besedka-button_color', value: '#1d74f5' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_text_color', value: '#FFFFFF' }
];

print('📊 Применяю дополнительных настроек:', additionalSettings.length);

additionalSettings.forEach(setting => {
    const existing = db.rocketchat_settings.findOne({_id: setting._id});

    if (existing) {
        // Обновляем существующую настройку
        const result = db.rocketchat_settings.updateOne(
            {_id: setting._id},
            {$set: {value: setting.value}}
        );
        if (result.modifiedCount > 0) {
            print('✅ Обновлено:', setting._id, '→', setting.value);
        } else {
            print('⚠️ Не изменилось:', setting._id, '(уже правильное значение)');
        }
    } else {
        // Создаем новую настройку
        const result = db.rocketchat_settings.insertOne({
            _id: setting._id,
            value: setting.value,
            ts: new Date(),
            _updatedAt: new Date()
        });
        if (result.insertedId) {
            print('🆕 Создано:', setting._id, '→', setting.value);
        }
    }
});

// Проверяем финальное состояние OAuth провайдера
const finalOAuthSettings = db.rocketchat_settings.find({
    _id: {$regex: /^Accounts_OAuth_Custom-Besedka/}
}).toArray();

print('');
print('🎯 ФИНАЛЬНЫЕ OAUTH НАСТРОЙКИ:');
print('Всего настроек провайдера Besedka:', finalOAuthSettings.length);

// Показываем ключевые настройки
const keySettings = [
    'Accounts_OAuth_Custom-Besedka',
    'Accounts_OAuth_Custom-Besedka-id',
    'Accounts_OAuth_Custom-Besedka-secret',
    'Accounts_OAuth_Custom-Besedka-button_label_text',
    'Accounts_OAuth_Custom-Besedka-merge_users',
    'Accounts_OAuth_Custom-Besedka-map_channels',
    'Accounts_OAuth_Custom-Besedka-merge_roles',
    'Accounts_OAuth_Custom-Besedka-show_button'
];

keySettings.forEach(key => {
    const setting = finalOAuthSettings.find(s => s._id === key);
    if (setting) {
        print('✅', key.replace('Accounts_OAuth_Custom-Besedka-', ''), '→', setting.value);
    } else {
        print('❌ НЕ НАЙДЕНО:', key);
    }
});

print('');
print('🎉 Дополнительная настройка OAuth завершена!');
print('🔄 Обновите страницу Rocket.Chat админки для отображения изменений');
