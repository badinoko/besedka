print("🚀 Прямая инициализация Rocket.Chat (мастер настройки) через MongoDB...");

// Основные поля мастера
var settings = [
    // Организация
    {_id: "Organization_Name", value: "Besedka"},
    {_id: "Organization_Type", value: "Community"},
    {_id: "Organization_Size", value: "1-50"},
    {_id: "Country", value: "Russia"},
    // Сайт
    {_id: "Site_Name", value: "Besedka"},
    {_id: "Language", value: "ru"},
    // Завершение мастера
    {_id: "Show_Setup_Wizard", value: "completed"},
    // Отключить cloud registration
    {_id: "Register_Server", value: false}
];

// Применяем все настройки
settings.forEach(function(setting) {
    db.getCollection('rocketchat_settings').updateOne(
        {_id: setting._id},
        {$set: { value: setting.value }},
        {upsert: true}
    );
});

print("✅ Все ключевые поля мастера Rocket.Chat записаны напрямую в базу.");
print("‼️ Перезапустите Rocket.Chat для применения изменений.");
