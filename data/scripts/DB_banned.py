import sqlite3
from datetime import datetime


db = sqlite3.connect('data/database/banned.db')
cursor = db.cursor()


def get_banned():
    cursor.execute("SELECT id FROM banned_users")
    result = cursor.fetchall()

    id_list = [row[0] for row in result]

    return id_list

def set_ban(id):
    cursor.execute("INSERT INTO banned_users (id, date) VALUES (?, ?)", (id, datetime.now(),))
    db.commit()

    return True


def set_unban(id):
    value = 'unbanned' + str(id)

    cursor.execute("UPDATE banned_users SET id=? WHERE id=?", (value, id,))
    db.commit()
    
    return True