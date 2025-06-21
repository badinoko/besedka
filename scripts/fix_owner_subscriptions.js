// ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ПОДПИСОК ДЛЯ ПОЛЬЗОВАТЕЛЯ OWNER
// 21 июня 2025 - Исправление проблемы с отсутствующими каналами

print('🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ПОДПИСОК...');

// Находим пользователя owner
const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('❌ Пользователь owner не найден!');
    quit();
}

print(`✅ Найден пользователь: ${owner.username} (ID: ${owner._id})`);

// РЕАЛЬНЫЕ ID каналов из нашей базы
const channelIds = ['GENERAL', 'vip-chat', 'moderators'];

channelIds.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });

    if (!room) {
        print(`❌ Канал не найден: ${channelId}`);
        return;
    }

    print(`\n🔄 Обрабатываю канал: ${room.name} (ID: ${room._id})`);

    // Проверяем подписку
    let subscription = db.rocketchat_subscription.findOne({
        'u._id': owner._id,
        rid: room._id
    });

    if (!subscription) {
        print(`  ❌ ПОДПИСКА НЕ НАЙДЕНА - СОЗДАЮ НОВУЮ`);

        // СОЗДАЕМ НОВУЮ ПОДПИСКУ
        const newSubscription = {
            _id: new ObjectId(),
            u: {
                _id: owner._id,
                username: owner.username,
                name: owner.name || owner.username
            },
            rid: room._id,
            name: room.name,
            fname: room.fname || room.name,
            t: room.t,
            open: true,
            alert: false,
            unread: 0,
            userMentions: 0,
            groupMentions: 0,
            ts: new Date(),
            lr: new Date(),
            ls: new Date(),
            _updatedAt: new Date()
        };

        const insertResult = db.rocketchat_subscription.insertOne(newSubscription);
        if (insertResult.acknowledged) {
            print(`  ✅ НОВАЯ ПОДПИСКА СОЗДАНА`);
        } else {
            print(`  ❌ ОШИБКА СОЗДАНИЯ ПОДПИСКИ`);
        }

        subscription = newSubscription;
    } else {
        print(`  ✅ Подписка существует`);

        // ОБНОВЛЯЕМ СУЩЕСТВУЮЩУЮ ПОДПИСКУ
        const updateResult = db.rocketchat_subscription.updateOne(
            { _id: subscription._id },
            {
                $set: {
                    open: true,
                    alert: false,
                    unread: 0,
                    ls: new Date(),
                    lr: new Date(),
                    _updatedAt: new Date()
                }
            }
        );

        if (updateResult.modifiedCount > 0) {
            print(`  ✅ ПОДПИСКА ОБНОВЛЕНА`);
        }
    }

    // ДОБАВЛЯЕМ ПОЛЬЗОВАТЕЛЯ В СПИСОК УЧАСТНИКОВ КАНАЛА
    const roomUpdateResult = db.rocketchat_room.updateOne(
        { _id: room._id },
        {
            $addToSet: {
                usernames: owner.username
            },
            $set: {
                _updatedAt: new Date()
            }
        }
    );

    if (roomUpdateResult.modifiedCount > 0) {
        print(`  ✅ Добавлен в список участников канала`);
    } else {
        print(`  ℹ️ Уже в списке участников`);
    }
});

print('\n🎉 ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!');

// ИТОГОВАЯ ПРОВЕРКА
print('\n=== ИТОГОВАЯ ПРОВЕРКА ===');
const finalCheck = db.rocketchat_subscription.find({'u.username': 'owner'}).count();
print(`📊 Всего подписок у owner: ${finalCheck}`);

channelIds.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });
    if (!room) return;

    const subscription = db.rocketchat_subscription.findOne({
        'u._id': owner._id,
        rid: room._id
    });

    if (subscription) {
        print(`✅ ${room.name}: ПОДПИСКА АКТИВНА`);
    } else {
        print(`❌ ${room.name}: ПОДПИСКА ОТСУТСТВУЕТ`);
    }
});

print('\n🚀 ТЕПЕРЬ owner ДОЛЖЕН ВИДЕТЬ ВСЕ 3 КАНАЛА!');
