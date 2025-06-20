// Скрипт для пропуска Setup Wizard в Rocket.Chat

// Помечаем Setup Wizard как завершенный
db.rocketchat_settings.updateOne(
    { _id: 'Show_Setup_Wizard' },
    { $set: { value: 'completed' } }
);

// Проверяем результат
const result = db.rocketchat_settings.findOne({ _id: 'Show_Setup_Wizard' });
print('Setup Wizard статус: ' + result.value);

// Также проверим, есть ли пользователь admin
const admin = db.users.findOne({ username: 'owner' });
if (admin) {
    print('Пользователь owner найден с _id: ' + admin._id);
} else {
    print('Пользователь owner НЕ найден!');
}

// Проверяем OAuth настройки
const oauthEnabled = db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka' });
if (oauthEnabled && oauthEnabled.value === true) {
    print('OAuth для Беседки включен');
} else {
    print('OAuth для Беседки НЕ включен!');
}
