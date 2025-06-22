# 🚑 План стабилизации Rocket.Chat и MongoDB

**Версия:** 1.0  •  Дата: 21 июня 2025 г.

Этот документ фиксирует пошаговый рецепт, исключающий повторные появления Setup Wizard, пропажу каналов и «двойную Mongo». Следуя ему, вы наконец перестанете проходить настройку Rocket.Chat по 30 раз подряд.

---

## 1. Где действительно лежат данные
- Все пользователи, каналы, OAuth-настройки и сообщения Rocket.Chat хранятся **только** в MongoDB (`/data/db`).
- Если у контейнера Mongo нет **именованного** volume, данные пишутся во внутренний слой контейнера и теряются при его удалении.

## 2. Почему запускается «две Mongo»
1. В стандартном compose-файле присутствуют сервисы `mongo` и `mongo-init-replica`.
2. `mongo-init-replica` нужен **один раз** — инициализировать реплика-сет `rs0`.
3. Если его не останавливать, получится два процесса `mongod`, оба слушают `27017`. В гонке за портом база повреждается или поднимается «не та» Mongo.

## 3. Почему база «обнуляется»
- Запуск `docker-compose down -v` уничтожает volume → новая чистая Mongo.
- Docker Desktop для Windows удаляет «anonymous volumes», если они не названы в `volumes:`.
- Одновременный старт двух `mongod` повреждает `oplog`; после краша Rocket.Chat видит пустую БД и предлагает Setup Wizard.

## 4. Шаги к устойчивой конфигурации

### Шаг 1. Один контейнер Mongo + named volume
```yaml
db:
  image: mongo:6.0
  command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
  restart: unless-stopped
  volumes:
    - rocketchat-mongo:/data/db
volumes:
  rocketchat-mongo:
```

### Шаг 2. Одноразовая инициализация реплики
```bash
# выполнить единожды
docker exec -it <mongo_container> mongosh --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"db:27017"}]})'
```

### Шаг 3. Жёсткая последовательность перезапуска
```bash
# 1. Остановить Python
 taskkill /f /im python.exe
# 2. Остановить чат и Mongo
 docker-compose -f docker-compose.local.yml stop rocketchat db
# 3. Запустить Mongo и дождаться PRIMARY
 docker-compose -f docker-compose.local.yml up -d db
 docker logs -f db   # убедиться в "PRIMARY rs0"
# 4. Запустить Rocket.Chat
 docker-compose -f docker-compose.local.yml up -d rocketchat
# 5. Запустить Django (только Daphne)
 daphne -b 127.0.0.1 -p 8001 config.asgi:application
```

### Шаг 4. Никогда не удалять volume
Используйте `docker-compose down` (без `-v`). Volume `rocketchat-mongo` сохранит данные между перезапусками.

### Шаг 5. Синхронизировать URI во всех скриптах
- `MONGO_URL`: `mongodb://db:27017/rocketchat?replicaSet=rs0`
- Скрипты `pymongo` обязаны пользоваться тем же URI.

## 5. Итог: один рецепт — и никаких Setup Wizard
1. **Один контейнер Mongo.**
2. **Именованный volume.**
3. **Rocket.Chat стартует только после готовности PRIMARY.**
4. **Ни одного `down -v` в разработке.**
5. **Совпадающие реплика-сеты во всех переменных.**

После внедрения этих пяти пунктов база не будет обнуляться, каналы и роли сохранятся, а Setup Wizard навсегда исчезнет из рабочего процесса. 
