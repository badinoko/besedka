// Обновление OAuth credentials на актуальные из Django

// Обновляем Client ID и Secret на актуальные из Django
const oauthUpdates = [
    { _id: 'Accounts_OAuth_Custom-Besedka-id', value: 'BesedkaRocketChat2025' },
    { _id: 'Accounts_OAuth_Custom-Besedka-secret', value: 'SecureSecretKey2025BesedkaRocketChatSSO' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_label_text', value: 'Войти через Беседку' },
    { _id: 'Accounts_OAuth_Custom-Besedka', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_users', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-show_button', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_claim', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-Besedka-groups_claim', value: 'groups' },
    { _id: 'Accounts_OAuth_Custom-Besedka-access_token_param', value: 'access_token' }
];

print('🔄 Обновляю OAuth credentials...');

oauthUpdates.forEach(setting => {
    const result = db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value } },
        { upsert: true }
    );
    print(`✅ ${setting._id}: ${setting.value}`);
});

// Проверяем что обновилось
print('\n📋 ПРОВЕРКА РЕЗУЛЬТАТОВ:');
print('Client ID: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-id' }).value);
print('Кнопка включена: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-show_button' }).value);
print('Текст кнопки: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-button_label_text' }).value);
print('Merge users: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-merge_users' }).value);

print('\n🎉 Обновление завершено! Обновите страницу Rocket.Chat.');
