// Скрипт исправления iframe интеграции Rocket.Chat
// Исправляет X-Frame-Options и другие настройки для корректной работы в iframe

print("=== ИСПРАВЛЕНИЕ IFRAME ИНТЕГРАЦИИ ===");

try {
    // Подключение к базе данных
    db = db.getSiblingDB('rocketchat');

    // 1. Разрешаем iframe интеграцию
    print("1. Настройка X-Frame-Options...");
    db.rocketchat_settings.updateOne(
        { _id: 'X_Frame_Options' },
        {
            $set: {
                value: 'SAMEORIGIN',
                packageValue: 'SAMEORIGIN',
                type: 'string',
                group: 'General',
                section: 'Iframe_Integration',
                i18nLabel: 'X_Frame_Options',
                i18nDescription: 'X_Frame_Options_Description',
                enableQuery: '{\"_id\":\"Accounts_iframe_enabled\",\"value\":true}',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );
    print("✅ X-Frame-Options настроен на SAMEORIGIN");

    // 2. Включаем iframe поддержку
    print("2. Включение iframe поддержки...");
    db.rocketchat_settings.updateOne(
        { _id: 'Accounts_iframe_enabled' },
        {
            $set: {
                value: true,
                packageValue: false,
                type: 'boolean',
                group: 'Accounts',
                section: 'Iframe',
                i18nLabel: 'Accounts_iframe_enabled',
                i18nDescription: 'Accounts_iframe_enabled_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );
    print("✅ Iframe поддержка включена");

    // 3. Настройка iframe URL
    print("3. Настройка iframe URL...");
    db.rocketchat_settings.updateOne(
        { _id: 'Accounts_iframe_url' },
        {
            $set: {
                value: 'http://127.0.0.1:8001',
                packageValue: '',
                type: 'string',
                group: 'Accounts',
                section: 'Iframe',
                i18nLabel: 'Accounts_iframe_url',
                i18nDescription: 'Accounts_iframe_url_Description',
                enableQuery: '{\"_id\":\"Accounts_iframe_enabled\",\"value\":true}',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );
    print("✅ Iframe URL настроен");

    // 4. Разрешаем встраивание для всех доменов
    print("4. Настройка Content Security Policy...");
    db.rocketchat_settings.updateOne(
        { _id: 'Content_Security_Policy' },
        {
            $set: {
                value: "frame-ancestors 'self' http://127.0.0.1:8001 http://localhost:8001; frame-src 'self' *",
                packageValue: '',
                type: 'string',
                group: 'General',
                section: 'Content_Security_Policy',
                i18nLabel: 'Content_Security_Policy',
                i18nDescription: 'Content_Security_Policy_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );
    print("✅ CSP настроен для iframe");

    // 5. Отключаем ограничение на встраивание
    print("5. Отключение embed ограничений...");
    db.rocketchat_settings.updateOne(
        { _id: 'Iframe_Restrict_Access' },
        {
            $set: {
                value: false,
                packageValue: true,
                type: 'boolean',
                group: 'General',
                section: 'Iframe_Integration',
                i18nLabel: 'Iframe_Restrict_Access',
                i18nDescription: 'Iframe_Restrict_Access_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );
    print("✅ Embed ограничения отключены");

    // 6. Включаем layout embedded по умолчанию
    print("6. Настройка layout embedded...");
    db.rocketchat_settings.updateOne(
        { _id: 'Layout_Show_Setup_Wizard' },
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
    print("✅ Setup Wizard отключен");

    // 7. Разрешаем API доступ для интеграции
    print("7. Настройка API доступа...");
    db.rocketchat_settings.updateOne(
        { _id: 'API_Enable_Rate_Limiter' },
        {
            $set: {
                value: false,
                packageValue: true,
                type: 'boolean',
                group: 'General',
                section: 'REST_API',
                i18nLabel: 'API_Enable_Rate_Limiter',
                i18nDescription: 'API_Enable_Rate_Limiter_Description',
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );
    print("✅ API rate limiter отключен");

    print("\n=== ПРОВЕРКА НАСТРОЕК ===");

    // Проверяем результат
    const iframeSettings = db.rocketchat_settings.find({
        _id: { $in: ['X_Frame_Options', 'Accounts_iframe_enabled', 'Content_Security_Policy'] }
    });

    iframeSettings.forEach(function(setting) {
        print(`${setting._id}: ${setting.value}`);
    });

    print("\n=== ИСПРАВЛЕНИЕ ЗАВЕРШЕНО ===");
    print("Перезапустите Rocket.Chat контейнер для применения настроек:");
    print("docker restart magic_beans_new-rocketchat-1");

} catch (error) {
    print("ОШИБКА: " + error.message);
}
