// Очистка ВСЕХ OAuth кешей и коллекций
print("🧹 ПОЛНАЯ ОЧИСТКА OAUTH КЕША...");

// Очищаем все OAuth коллекции
var collections = [
    'rocketchat_oauth_apps',
    'meteor_oauth_pendingRequestTokens',
    'meteor_oauth_pendingCredentials',
    'rocketchat_oauth_auth_codes',
    'rocketchat_oauth_refresh_tokens',
    'rocketchat_oauth_access_tokens'
];

collections.forEach(function(col) {
    try {
        var count = db[col].countDocuments();
        if (count > 0) {
            db[col].deleteMany({});
            print("✅ Очищена коллекция " + col + " (" + count + " записей)");
        } else {
            print("ℹ️ Коллекция " + col + " уже пуста");
        }
    } catch(e) {
        print("⚠️ Ошибка с коллекцией " + col + ": " + e);
    }
});

print("\n🚀 Кеш очищен!");
