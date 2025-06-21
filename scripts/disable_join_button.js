// ОТКЛЮЧЕНИЕ КНОПКИ "JOIN CHANNEL"

print('🚫 ОТКЛЮЧАЮ ПРИНУДИТЕЛЬНУЮ КНОПКУ "JOIN CHANNEL"...');

// Настройки для отключения кнопки Join
const settingsToDisable = [
    // Отключаем необходимость присоединения к публичным каналам
    'Accounts_Default_User_Preferences_joinDefaultChannels',
    'AutoTranslate_Enabled',
    'Accounts_RegistrationForm_LinkChannelToUser',

    // Настройки каналов
    'Accounts_Default_User_Preferences_viewMode',
    'Accounts_Default_User_Preferences_hideUsernames',
    'Accounts_Default_User_Preferences_hideFlexTab',

    // Разрешения на автоматическое присоединение
    'Channel_Allow_Anonymous_Read',
    'Channel_Allow_Anonymous_Write'
];

const settingsToEnable = [
    // Включаем автоматическое присоединение к default каналам
    'Accounts_Default_User_Preferences_joinDefaultChannels'
];

// Отключаем ненужные настройки
settingsToDisable.forEach(settingId => {
    const result = db.rocketchat_settings.updateOne(
        { _id: settingId },
        {
            $set: {
                value: false,
                _updatedAt: new Date()
            }
        }
    );

    if (result.matchedCount > 0) {
        print(`✅ Отключено: ${settingId}`);
    } else {
        print(`ℹ️ Настройка не найдена: ${settingId}`);
    }
});

// Включаем нужные настройки
settingsToEnable.forEach(settingId => {
    const result = db.rocketchat_settings.updateOne(
        { _id: settingId },
        {
            $set: {
                value: true,
                _updatedAt: new Date()
            }
        }
    );

    if (result.matchedCount > 0) {
        print(`✅ Включено: ${settingId}`);
    }
});

// СПЕЦИАЛЬНАЯ НАСТРОЙКА: Делаем каналы доступными без присоединения
print('\n🔧 НАСТРОЙКА КАНАЛОВ ДЛЯ ПРЯМОГО ДОСТУПА...');

const channelsToUpdate = ['GENERAL', 'vip', 'moderators'];

channelsToUpdate.forEach(channelId => {
    const result = db.rocketchat_room.updateOne(
        { _id: channelId },
        {
            $set: {
                // Публичный канал без необходимости присоединения
                t: 'c',              // Channel type
                ro: false,           // Не только для чтения
                default: true,       // Default канал
                featured: true,      // Рекомендуемый канал
                _updatedAt: new Date()
            }
        }
    );

    if (result.matchedCount > 0) {
        print(`✅ Канал настроен для прямого доступа: ${channelId}`);
    }
});

print('\n🎯 ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА: Убираем ограничения доступа...');

// Убираем любые ограничения на просмотр истории
const historySettings = [
    'Message_ShowEditedStatus',
    'Message_ShowDeletedStatus',
    'Message_AllowEditing',
    'Message_AllowEditing_BlockEditInMinutes',
    'Message_KeepHistory'
];

historySettings.forEach(settingId => {
    db.rocketchat_settings.updateOne(
        { _id: settingId },
        {
            $set: {
                value: true,
                _updatedAt: new Date()
            }
        }
    );
});

print('✅ Настройки истории сообщений обновлены');

print('\n🚫 ГОТОВО! КНОПКА "JOIN CHANNEL" ОТКЛЮЧЕНА!');
print('📱 Обновите страницу чата для применения изменений.');
