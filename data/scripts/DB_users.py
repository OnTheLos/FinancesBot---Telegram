import sqlite3


db = sqlite3.connect('data/database/users.db')
cursor = db.cursor()


def check_user(id):
    # Проверка есть ли юзер в базе активных юзеров
    cursor.execute("SELECT * FROM usersinfo WHERE active = ?", (id,))
    result = cursor.fetchone()

    # Если есть, то возвращает True
    if result:
        return True

    else:

        # Проверка есть ли юзер в базе неактивных юзеров
        cursor.execute("SELECT * FROM usersinfo WHERE inactive = ?", (id,))
        b = cursor.fetchone()
        db.commit()

        # Если есть, то добавляет айди в базу активных и убирает из базы неактивных и возвращает True
        if b:
            cursor.execute("INSERT INTO usersinfo (active) VALUES (?)", (id,))
            cursor.execute("UPDATE usersinfo SET inactive = NULL WHERE inactive = ?", (id,)) 
            db.commit()

            return True
        
        # Если нет, то это новый пользователь и его айди добавляется в базу и возвращает False
        else:
            cursor.execute("INSERT INTO usersinfo (active) VALUES (?)", (id,))
            db.commit()

            return False
        

def set_inactive_user(id):
    cursor.execute("INSERT INTO usersinfo (inactive) VALUES (?)", (id,))
    cursor.execute("UPDATE usersinfo SET active = NULL WHERE active = ?", (id,))
    db.commit()   


def get_active_users():
    cursor.execute("SELECT active FROM usersinfo WHERE active IS NOT NULL")
    users = cursor.fetchall()

    flat_list = [item for sublist in users for item in sublist]

    return flat_list


def get_users_txt(a):   # a = 'active'/'inactive'
    cursor.execute(f"SELECT {a} FROM usersinfo WHERE {a} IS NOT NULL")
    b = cursor.fetchall()

    with open(f'{a}_users.txt', 'w') as file:
        for value in b:
            file.write(str(value[0]) + '\n')

    return True
