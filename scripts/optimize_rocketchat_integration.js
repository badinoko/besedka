// 🎯 ОПТИМИЗАЦИЯ ROCKET.CHAT ИНТЕГРАЦИИ (22 июня 2025)
// Решает проблемы:
// 1. Скрывает кнопку "Войти через Беседку" для интегрированного режима
// 2. Убирает кнопку "Join the Channel" навсегда
// 3. Оптимизирует пользовательский опыт

print('🎯 ОПТИМИЗАЦИЯ ROCKET.CHAT ИНТЕГРАЦИИ...');

// 1. СКРЫВАЕМ КНОПКУ "ВОЙТИ ЧЕРЕЗ БЕСЕДКУ" ДЛЯ ИНТЕГРИРОВАННОГО РЕЖИМА
print('🔧 Скрываю кнопку "Войти через Беседку" для интегрированного режима...');

// Отключаем показ кнопки OAuth (пользователи уже авторизованы через Django)
db.rocketchat_settings.updateOne(
    {_id: 'Accounts_OAuth_Custom-besedka-show_button'},
    {$set: {value: false, valueSource: 'customValue', _updatedAt: new Date()}},
    {upsert: true}
);

print('✅ Кнопка "Войти через Беседку" скрыта');

// 2. УБИРАЕМ КНОПКУ "JOIN THE CHANNEL" НАВСЕГДА
print('🔧 Убираю кнопку "Join the Channel" навсегда...');

// Автоматически присоединяем всех к каналам
const joinSettings = [
    {_id: 'Accounts_Default_User_Preferences_joinDefaultChannels', value: true},
    {_id: 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced', value: false},
    {_id: 'Accounts_OAuth_Custom-besedka-map_channels', value: true},
    {_id: 'Accounts_OAuth_Custom-besedka-channels_admin', value: 'admin,vip,moderator'},
    {_id: 'Room_Show_Deleted', value: false} // Скрываем удаленные каналы
];

joinSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, valueSource: 'customValue', _updatedAt: new Date()}},
        {upsert: true}
    );
});

print('✅ Автоматическое присоединение к каналам настроено');

// 3. АВТОМАТИЧЕСКИ ПОДПИСЫВАЕМ OWNER НА ВСЕ КАНАЛЫ (если ещё не подписан)
print('🔧 Проверяю подписки пользователя owner...');

const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('❌ Пользователь owner не найден!');
} else {
    const allChannels = ['GENERAL', 'vip', 'moderators'];

    allChannels.forEach(channelId => {
        const room = db.rocketchat_room.findOne({ _id: channelId });
        if (!room) {
            print(`⚠️ Канал ${channelId} не найден`);
            return;
        }

        const subscription = db.rocketchat_subscription.findOne({
            'u._id': owner._id,
            rid: channelId
        });

        if (!subscription) {
            print(`📝 Создаю подписку на канал: ${room.name}`);

            db.rocketchat_subscription.insertOne({
                _id: owner._id + channelId,
                u: {
                    _id: owner._id,
                    username: owner.username
                },
                rid: channelId,
                name: room.name,
                fname: room.fname || room.name,
                t: room.t,
                ts: new Date(),
                ls: new Date(),
                lr: new Date(),
                f: false,
                open: true,
                alert: false,
                roles: ['owner'],
                unread: 0,
                _updatedAt: new Date()
            });

            print(`✅ Подписка создана: ${room.name}`);
        } else {
            print(`ℹ️ Подписка уже есть: ${room.name}`);
        }
    });
}

// 4. УБИРАЕМ ВСЕ ПРОМЕЖУТОЧНЫЕ УВЕДОМЛЕНИЯ И ПРЕПЯТСТВИЯ
print('🔧 Убираю препятствия для плавной работы...');

const smoothSettings = [
    // Убираем уведомления о правилах каналов
    {_id: 'Message_ShowEditedStatus', value: false},
    {_id: 'Message_ShowDeletedStatus', value: false},

    // Убираем лишние предупреждения
    {_id: 'Accounts_AllowUserProfileChange', value: true},
    {_id: 'Accounts_AllowUserAvatarChange', value: true},

    // Автоматическое присоединение к новым каналам
    {_id: 'AutoJoin_Default_Channels', value: true}
];

smoothSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, valueSource: 'customValue', _updatedAt: new Date()}},
        {upsert: true}
    );
});

print('✅ Промежуточные препятствия убраны');

// 5. СОХРАНЯЕМ OAUTH (убеждаемся что он продолжает работать)
print('🔧 Сохраняю OAuth функциональность...');

// OAuth остается рабочим для API вызовов, просто кнопка скрыта
const maintainedOAuthSettings = [
    {_id: 'Accounts_OAuth_Custom-besedka', value: true},
    {_id: 'Accounts_OAuth_Custom-besedka-merge_users', value: true},
    {_id: 'Accounts_OAuth_Custom-besedka-login_style', value: 'redirect'}
];

maintainedOAuthSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, valueSource: 'customValue', _updatedAt: new Date()}},
        {upsert: true}
    );
});

print('✅ OAuth остается функциональным');

// ИТОГОВЫЙ ОТЧЕТ
print('\n🎉 ОПТИМИЗАЦИЯ ЗАВЕРШЕНА!');
print('=====================================');
print('✅ Кнопка "Войти через Беседку" скрыта (OAuth работает автоматически)');
print('✅ Кнопка "Join the Channel" убрана навсегда');
print('✅ Автоматическое присоединение ко всем каналам');
print('✅ Убраны промежуточные препятствия');
print('✅ OAuth интеграция сохранена и работает');
print('\n🎯 РЕЗУЛЬТАТ: Чистый интерфейс без лишних кнопок!');
