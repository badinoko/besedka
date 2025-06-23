import pymongo

try:
    # Подключение к MongoDB
    client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
    db = client['rocketchat']

    # Получаем все каналы (тип 'c')
    rooms = db.rocketchat_room.find({'t': 'c'}, {'name': 1, 'fname': 1})

    print('=== КАНАЛЫ ROCKET.CHAT ===')
    for room in rooms:
        name = room.get('name', 'N/A')
        fname = room.get('fname', 'N/A')
        print(f'- name: "{name}", fname: "{fname}"')

        # Проверим кодировку fname
        if fname != 'N/A':
            try:
                fname_encoded = fname.encode('utf-8')
                print(f'  UTF-8 bytes: {fname_encoded}')
            except:
                print(f'  ОШИБКА КОДИРОВКИ fname')

    client.close()
    print('\n=== ПРОВЕРКА ЗАВЕРШЕНА ===')

except Exception as e:
    print(f'ОШИБКА: {e}')
