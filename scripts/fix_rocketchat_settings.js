// Скрипт исправления настроек Rocket.Chat через mongosh
print("🚀 Исправление настроек Rocket.Chat...");

// Настройки для обновления
const updates = [
    { _id: 'Site_Url', value: 'http://127.0.0.1:3000' },
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannels', value: true },
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced', value: false },
    { _id: 'Accounts_Default_User_Preferences_openChannelsOnLogin', value: 'general' },
    { _id: 'Show_Setup_Wizard', value: false },
    { _id: 'First_Channel_After_Login', value: false },
    { _id: 'Accounts_TwoFactorAuthentication_Enabled', value: false },
    { _id: 'Accounts_RequirePasswordConfirmation', value: false },
    { _id: 'Restrict_access_inside_any_Iframe', value: false }
];

// Применяем обновления
updates.forEach(update => {
    const result = db.rocketchat_settings.updateOne(
        { _id: update._id },
        {
            $set: {
                value: update.value,
                _updatedAt: new Date()
            }
        },
        { upsert: true }
    );

    if (result.acknowledged) {
        print(`✅ ${update._id}: ${update.value}`);
    } else {
        print(`❌ Ошибка обновления ${update._id}`);
    }
});

print("🎉 Исправления завершены!");
print("💡 Перезапустите Rocket.Chat контейнер для применения изменений:");
print("   docker-compose -f docker-compose.local.yml restart rocketchat");
