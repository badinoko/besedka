// Скрипт настройки embedded layout в Rocket.Chat
// Цель: показывать ТОЛЬКО чат без левой навигации и верхних меню

print("=== НАСТРОЙКА EMBEDDED РЕЖИМА ДЛЯ ROCKET.CHAT ===");

try {
    // Подключение к базе данных
    db = db.getSiblingDB('rocketchat');

    // 1. Отключаем левую навигацию в embedded режиме
    print("1. Отключение левой навигации...");
    db.rocketchat_settings.updateOne(
        { _id: 'UI_Show_Setup_Wizard' },
        {
            $set: {
                value: 'completed',
                packageValue: 'pending',
                type: 'string',
                group: 'Layout',
                section: 'Content',
                i18nLabel: 'Show_Setup_Wizard',
                i18nDescription: 'Show_Setup_Wizard_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    // 2. Скрыть верхнее меню в embedded режиме
    print("2. Скрытие верхнего меню...");
    db.rocketchat_settings.updateOne(
        { _id: 'Layout_Sidenav_Footer' },
        {
            $set: {
                value: '<style>.rc-old .sidebar { display: none !important; } .main-content { margin-left: 0 !important; } .rc-old .main-content { padding: 0; } body.embedded .sidebar { display: none !important; }</style>',
                packageValue: '',
                type: 'code',
                group: 'Layout',
                section: 'Content',
                i18nLabel: 'Layout_Sidenav_Footer',
                i18nDescription: 'Layout_Sidenav_Footer_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    // 3. Настройка CSS для скрытия навигации в embedded
    print("3. Добавление CSS для embedded режима...");
    db.rocketchat_settings.updateOne(
        { _id: 'theme-color-rc-color-primary' },
        {
            $set: {
                value: '#1a1a2e',
                packageValue: '#175cc4',
                type: 'color',
                group: 'Layout',
                section: 'Colors',
                i18nLabel: 'Primary_color',
                i18nDescription: 'Primary_color_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    // 4. Настройка для встраивания iframe
    print("4. Настройка iframe integration...");
    db.rocketchat_settings.updateOne(
        { _id: 'Iframe_Integration_send_enable' },
        {
            $set: {
                value: true,
                packageValue: false,
                type: 'boolean',
                group: 'Message',
                section: 'Iframe_Integration',
                i18nLabel: 'Iframe_Integration_send_enable',
                i18nDescription: 'Iframe_Integration_send_enable_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    // 5. Отключение Omnichannel для чистоты интерфейса
    print("5. Отключение Omnichannel...");
    db.rocketchat_settings.updateOne(
        { _id: 'Livechat_enabled' },
        {
            $set: {
                value: false,
                packageValue: false,
                type: 'boolean',
                group: 'Omnichannel',
                section: 'Livechat',
                i18nLabel: 'Livechat_enabled',
                i18nDescription: 'Livechat_enabled_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    // 6. Скрытие аватаров и упрощение интерфейса
    print("6. Упрощение интерфейса...");
    db.rocketchat_settings.updateOne(
        { _id: 'UI_Use_Real_Name' },
        {
            $set: {
                value: false,
                packageValue: false,
                type: 'boolean',
                group: 'Accounts',
                section: 'Avatar',
                i18nLabel: 'UI_Use_Real_Name',
                i18nDescription: 'UI_Use_Real_Name_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    // 7. Настройка embedded layout
    print("7. Настройка embedded layout...");
    db.rocketchat_settings.updateOne(
        { _id: 'Layout_Home_Body' },
        {
            $set: {
                value: '<style>body.embedded .main-content { margin-left: 0 !important; } body.embedded .sidebar { display: none !important; } body.embedded .rc-header { display: none !important; }</style>',
                packageValue: '',
                type: 'code',
                group: 'Layout',
                section: 'Content',
                i18nLabel: 'Layout_Home_Body',
                i18nDescription: 'Layout_Home_Body_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    print("\n=== ПРОВЕРКА НАСТРОЕК ===");

    // Проверяем ключевые настройки
    const keySettings = [
        'UI_Show_Setup_Wizard',
        'Layout_Sidenav_Footer',
        'Livechat_enabled',
        'Iframe_Integration_send_enable'
    ];

    keySettings.forEach(function(settingId) {
        const setting = db.rocketchat_settings.findOne({_id: settingId});
        if (setting) {
            print(`${settingId}: ${setting.value}`);
        } else {
            print(`${settingId}: НЕ НАЙДЕНО`);
        }
    });

    print("\n=== НАСТРОЙКА ЗАВЕРШЕНА ===");
    print("Перезапустите Rocket.Chat для применения изменений:");
    print("docker restart magic_beans_new-rocketchat-1");
    print("\nПроверьте URL: http://127.0.0.1:3000/channel/general?layout=embedded");

} catch (error) {
    print("ОШИБКА: " + error.message);
}
