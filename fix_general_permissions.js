// Скрипт для исправления прав канала GENERAL
use rocketchat;

print("=== ДИАГНОСТИКА КАНАЛА GENERAL ===");

// Проверяем канал GENERAL
var general = db.rocketchat_room.findOne({_id: "GENERAL"});
if (!general) {
    print("❌ Канал GENERAL не найден!");
    quit();
}

print("✅ Канал GENERAL найден:");
print("   - name: " + general.name);
print("   - fname: " + general.fname);
print("   - ro (только чтение): " + (general.ro || false));
print("   - default: " + (general.default || false));
print("   - sysMes: " + (general.sysMes || false));

// Проверяем работающий канал VIP для сравнения
var vip = db.rocketchat_room.findOne({_id: "vip"});
if (vip) {
    print("📋 Канал VIP (работающий):");
    print("   - ro: " + (vip.ro || false));
    print("   - default: " + (vip.default || false));
    print("   - sysMes: " + (vip.sysMes || false));
}

// Проверяем подписку owner на канал GENERAL
var ownerSub = db.rocketchat_subscription.findOne({rid: "GENERAL", "u.username": "owner"});
if (ownerSub) {
    print("👤 Подписка owner на GENERAL:");
    print("   - roles: " + JSON.stringify(ownerSub.roles || []));
    print("   - blocked: " + (ownerSub.blocked || false));
    print("   - blocker: " + (ownerSub.blocker || false));
} else {
    print("❌ Подписка owner на GENERAL не найдена!");
}

print("");
print("🔧 ПРИМЕНЯЮ ИСПРАВЛЕНИЯ...");

// Исправляем настройки канала GENERAL
var roomUpdate = {
    $set: {
        "sysMes": true,
        "default": true,
        "_updatedAt": new Date()
    }
};

// Убираем флаг только для чтения если есть
if (general.ro) {
    roomUpdate.$unset = {"ro": 1};
    print("✅ Убираю флаг 'только для чтения'");
}

var roomResult = db.rocketchat_room.updateOne({_id: "GENERAL"}, roomUpdate);
print("✅ Обновлены настройки канала: " + roomResult.modifiedCount);

// Исправляем подписку owner
if (ownerSub) {
    var subUpdate = {
        $set: {
            "roles": ["owner"],
            "_updatedAt": new Date()
        }
    };

    if (ownerSub.blocked) {
        subUpdate.$unset = {"blocked": 1};
        print("✅ Разблокировка owner");
    }

    if (ownerSub.blocker) {
        subUpdate.$unset = subUpdate.$unset || {};
        subUpdate.$unset.blocker = 1;
        print("✅ Убираю blocker у owner");
    }

    var subResult = db.rocketchat_subscription.updateOne({_id: ownerSub._id}, subUpdate);
    print("✅ Обновлена подписка owner: " + subResult.modifiedCount);
}

print("");
print("✅ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ!");
print("🔄 Рекомендация: Перезагрузите Rocket.Chat");
print("   docker restart magic_beans_new-rocketchat-1");
