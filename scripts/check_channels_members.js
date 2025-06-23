// Проверка участников каналов
print("=== ПРОВЕРКА УЧАСТНИКОВ КАНАЛОВ ===");

const channels = db.rocketchat_room.find({t: "c"}).toArray();

channels.forEach(function(channel) {
    print("");
    print("🏠 КАНАЛ: " + channel.name + " (ID: " + channel._id + ")");
    print("   Тип: " + channel.t);
    print("   Участников: " + (channel.usersCount || 0));

    if (channel.usernames) {
        print("   Список участников:");
        channel.usernames.forEach(function(username) {
            print("     - " + username);
        });
    } else {
        print("   ❌ НЕТ МАССИВА usernames!");
    }

    // Проверим есть ли owner в участниках
    if (channel.usernames && channel.usernames.includes("owner")) {
        print("   ✅ owner ЕСТЬ в участниках");
    } else {
        print("   ❌ owner НЕТ в участниках!");
    }
});
