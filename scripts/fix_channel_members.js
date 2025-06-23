// ИСПРАВЛЕНИЕ УЧАСТНИКОВ КАНАЛОВ
print("=== ДОБАВЛЕНИЕ OWNER В УЧАСТНИКИ КАНАЛОВ ===");

const user = db.users.findOne({username: "owner"});
if (!user) {
    print("❌ Пользователь owner не найден!");
    quit();
}
print("✅ Пользователь найден:", user.username);

const channels = db.rocketchat_room.find({t: "c"}).toArray();
print("📋 Найдено каналов:", channels.length);

channels.forEach(function(channel) {
    print("");
    print("🔧 ИСПРАВЛЯЮ КАНАЛ:", channel.name);

    // Создаем массив usernames если его нет
    if (!channel.usernames) {
        channel.usernames = [];
    }

    // Добавляем owner в участники если его там нет
    if (!channel.usernames.includes("owner")) {
        const result = db.rocketchat_room.updateOne(
            { _id: channel._id },
            {
                $addToSet: { usernames: "owner" },
                $inc: { usersCount: 1 },
                $set: { "_updatedAt": new Date() }
            }
        );

        if (result.modifiedCount > 0) {
            print("   ✅ Добавлен в участники");
        } else {
            print("   ❌ Ошибка добавления");
        }
    } else {
        print("   ℹ️ Уже участник");
    }
});

print("");
print("🔍 ПРОВЕРКА РЕЗУЛЬТАТА:");
const updatedChannels = db.rocketchat_room.find({t: "c"}).toArray();

updatedChannels.forEach(function(channel) {
    print("📍 " + channel.name + ":");
    print("   Участников: " + (channel.usersCount || 0));
    if (channel.usernames && channel.usernames.includes("owner")) {
        print("   ✅ owner ЕСТЬ в участниках");
    } else {
        print("   ❌ owner НЕТ в участниках");
    }
});

print("");
print("🎉 ГОТОВО! Теперь кнопка 'Join the Channel' должна исчезнуть");

// Fix Rocket.Chat users, channels and subscriptions according to BESEDKA_USER_SYSTEM.md

print("=== FIXING ROCKET.CHAT USERS AND SUBSCRIPTIONS ===");

// 1. Ensure all Django users exist in Rocket.Chat
const usersToCreate = [
  {username: 'admin', roles: ['user', 'admin'], name: 'Модератор', email: 'admin@besedka.com'},
  {username: 'store_owner', roles: ['user'], name: 'Владелец магазина', email: 'store.owner@magicbeans.com'},
  {username: 'store_admin', roles: ['user'], name: 'Администратор магазина', email: 'store.admin@magicbeans.com'},
  {username: 'test_user', roles: ['user'], name: 'Тестовый пользователь', email: 'test.user@besedka.com'}
];

usersToCreate.forEach(userData => {
  const existingUser = db.users.findOne({username: userData.username});
  if (!existingUser) {
    const userId = ObjectId();
    db.users.insertOne({
      _id: userId,
      username: userData.username,
      name: userData.name,
      emails: [{address: userData.email, verified: true}],
      type: 'user',
      status: 'online',
      active: true,
      roles: userData.roles,
      _updatedAt: new Date(),
      createdAt: new Date()
    });
    print(`Created user: ${userData.username}`);
  } else {
    print(`User exists: ${userData.username}`);
  }
});

// 2. Clear existing subscriptions for controlled setup
db.subscriptions.deleteMany({'u.username': {$in: ['owner','admin','store_owner','store_admin','test_user']}});
print("Cleared existing subscriptions");

// 3. Create proper channel subscriptions according to roles
const subscriptions = [
  // owner - all channels
  {username: 'owner', channels: ['GENERAL', 'vip', 'moderators']},
  // admin (moderator role) - general + moderators
  {username: 'admin', channels: ['GENERAL', 'moderators']},
  // store roles - only general
  {username: 'store_owner', channels: ['GENERAL']},
  {username: 'store_admin', channels: ['GENERAL']},
  {username: 'test_user', channels: ['GENERAL']}
];

subscriptions.forEach(userSub => {
  const user = db.users.findOne({username: userSub.username});
  if (user) {
    userSub.channels.forEach(channelId => {
      const channel = db.rocketchat_room.findOne({_id: channelId});
      if (channel) {
        db.subscriptions.insertOne({
          _id: ObjectId(),
          rid: channelId,
          u: {_id: user._id, username: user.username, name: user.name || user.username},
          t: channel.t,
          ts: new Date(),
          ls: new Date(),
          open: true,
          alert: false,
          unread: 0,
          userMentions: 0,
          groupMentions: 0,
          _updatedAt: new Date()
        });
        print(`Subscribed ${userSub.username} to ${channelId}`);
      }
    });
  }
});

// 4. Verify subscriptions
print("\n=== VERIFICATION ===");
db.subscriptions.aggregate([
  { $match: {'u.username': {$in:['owner','admin','store_owner','store_admin','test_user']}} },
  { $group: {_id:'$u.username', channels:{$addToSet:'$rid'}} }
]).forEach(printjson);

print("\n=== FIX COMPLETED ===");
