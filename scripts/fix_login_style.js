// Исправление login_style с popup на redirect
// КРИТИЧЕСКИ ВАЖНО для решения проблемы "окно открывается и закрывается"

print("🔧 ИСПРАВЛЕНИЕ login_style: popup → redirect");

// Находим текущую настройку
var current = db.rocketchat_settings.findOne({_id: "Accounts_OAuth_Custom_Besedka_login_style"});
if (current) {
    print("Текущее значение: " + current.value);
} else {
    print("Настройка не найдена");
}

// Принудительно устанавливаем redirect
var result = db.rocketchat_settings.updateOne(
    {_id: "Accounts_OAuth_Custom_Besedka_login_style"},
    {$set: {value: "redirect", type: "string"}},
    {upsert: true}
);

print("Результат обновления:");
print("- Matched: " + result.matchedCount);
print("- Modified: " + result.modifiedCount);
print("- Upserted: " + result.upsertedCount);

// Проверяем результат
var updated = db.rocketchat_settings.findOne({_id: "Accounts_OAuth_Custom_Besedka_login_style"});
if (updated) {
    print("Новое значение: " + updated.value);

    if (updated.value === "redirect") {
        print("✅ УСПЕХ! login_style изменен на redirect");
    } else {
        print("❌ ОШИБКА! login_style не изменился");
    }
} else {
    print("❌ ОШИБКА! Настройка не создана");
}

print("🔧 Готово!");
