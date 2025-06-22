// РАДИКАЛЬНОЕ ОТКЛЮЧЕНИЕ КНОПКИ JOIN НАВСЕГДА
print('🔥 РАДИКАЛЬНОЕ ОТКЛЮЧЕНИЕ КНОПКИ JOIN...');

// 1. Глобальные настройки интерфейса
const interfaceSettings = [
    {_id: 'UI_Allow_room_names_with_special_chars', value: true},
    {_id: 'UI_DisplayRoles', value: true},
    {_id: 'UI_Show_top_navbar_embedded_layout', value: false},
    {_id: 'Hide_System_Messages', value: ['uj', 'ul', 'ru', 'au', 'mute_unmute', 'r', 'ut', 'wm', 'rm', 'subscription-role-added', 'subscription-role-removed', 'room_changed_description', 'room_changed_announcement', 'room_changed_topic', 'room_changed_privacy', 'room_changed_avatar', 'message_pinned', 'message_snippeted', 'thread-created']},
    {_id: 'Layout_Sidenav_Footer', value: ''},
    {_id: 'Message_AllowDirectMessagesToYourself', value: false}
];

interfaceSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, _updatedAt: new Date()}},
        {upsert: true}
    );
});

// 2. Отключаем все ограничения доступа к каналам
const accessSettings = [
    {_id: 'E2E_Enable', value: false},
    {_id: 'E2E_Allow_Unencrypted_Messages', value: true},
    {_id: 'Accounts_AllowAnonymousRead', value: true},
    {_id: 'Accounts_AllowAnonymousWrite', value: false},
    {_id: 'Accounts_AllowInvisibleStatusOption', value: true},
    {_id: 'Accounts_Default_User_Preferences_roomsListExhibitionMode', value: 'category'},
    {_id: 'Accounts_Default_User_Preferences_sidebarViewMode', value: 'medium'},
    {_id: 'Accounts_Default_User_Preferences_sidebarDisplayAvatar', value: true},
    {_id: 'Accounts_Default_User_Preferences_groupByType', value: true},
    {_id: 'Accounts_Default_User_Preferences_sidebarShowFavorites', value: true},
    {_id: 'Accounts_Default_User_Preferences_sendOnEnter', value: 'normal'},
    {_id: 'Accounts_Default_User_Preferences_idleTimeLimit', value: 300},
    {_id: 'Accounts_Default_User_Preferences_desktopNotifications', value: 'mentions'},
    {_id: 'Accounts_Default_User_Preferences_pushNotifications', value: 'mentions'},
    {_id: 'Accounts_Default_User_Preferences_enableAutoAway', value: true},
    {_id: 'Message_GroupingPeriod', value: 300},
    {_id: 'API_Iframe_Restriction_Enabled', value: false},
    {_id: 'Iframe_Restrict_Access', value: false},
    {_id: 'Iframe_X_Frame_Options', value: 'sameorigin'}
];

accessSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, _updatedAt: new Date()}},
        {upsert: true}
    );
});

// 3. Делаем ВСЕ каналы полностью открытыми
print('🔧 Делаю все каналы полностью открытыми...');

db.rocketchat_room.updateMany(
    {},
    {
        $set: {
            ro: false,           // Не только для чтения
            sysMes: false,       // Отключаем системные сообщения
            default: true,       // Канал по умолчанию
            featured: true,      // Рекомендуемый
            _updatedAt: new Date()
        },
        $unset: {
            joinCodeRequired: 1, // Убираем требование кода
            lastMessage: 1       // Убираем кеш последнего сообщения
        }
    }
);

// 4. Обнуляем все права и роли для каналов (делаем их максимально открытыми)
print('🔧 Убираю все ограничения доступа...');

db.rocketchat_room.updateMany(
    {},
    {
        $unset: {
            muted: 1,
            unmuted: 1,
            jitsiTimeout: 1,
            teamId: 1,
            teamMain: 1,
            encrypted: 1
        }
    }
);

// 5. Принудительно устанавливаем каналы как joined для всех
print('🔧 Принудительно помечаю каналы как joined...');

const allChannels = db.rocketchat_room.find({t: 'c'}).toArray();
const owner = db.users.findOne({username: 'owner'});

if (owner) {
    allChannels.forEach(channel => {
        // Обновляем подписку
        db.rocketchat_subscription.updateOne(
            {'u._id': owner._id, rid: channel._id},
            {
                $set: {
                    open: true,
                    alert: false,
                    f: false,
                    ls: new Date(),
                    lr: new Date(),
                    _updatedAt: new Date()
                }
            },
            {upsert: true}
        );
    });
}

print('🎯 ГОТОВО! Все ограничения убраны, каналы максимально открыты!');
