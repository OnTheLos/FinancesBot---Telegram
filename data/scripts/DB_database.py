import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from .DB_currencies import cur_rate


db = sqlite3.connect('data/database/database.db')
cursor = db.cursor()

# Создание таблицы для нового юзера
def create_table(id):

    table = 'a' + str(id)   # Определение названия таблицы - "a[user_id]"

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table} (
                   date TEXT, 
                   operation TEXT,
                   sum INTEGER,
                   currency TEXT,
                   category TEXT,
                   balance INTEGER,
                   comment TEXT,
                   in_categories TEXT,
                   sp_categories TEXT,
                   main_currency TEXT)''')
    
    cursor.execute(f'INSERT INTO {table} (date, balance) VALUES (?, ?)', (datetime.now(), 0))
    
    db.commit()


# Создание таблицы для нового юзера с категориями
def create_table_with_categories(id):

    table = 'a' + str(id)    # Определение названия таблицы - "a[user_id]"

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table} (
                   date TEXT, 
                   operation TEXT,
                   sum INTEGER,
                   currency TEXT,
                   category TEXT,
                   balance INTEGER,
                   comment TEXT,
                   in_categories TEXT,
                   sp_categories TEXT,
                   main_currency TEXT)''')
    
    # Определение категорий
    incomes = ["Зарплата"]
    spends = ["Продукты", "Кафе", "Транспорт", "Подписки", "Покупки", "Здоровье", "Подарки"]   

    # Внесение категорий доходов
    for i in incomes:
        cursor.execute(f'INSERT INTO {table} (date, balance, in_categories) VALUES (?, ?, ?)', (datetime.now(), 0, i))
    
    # Внесение категорий трат
    for i in spends:
        cursor.execute(f'INSERT INTO {table} (date, balance, sp_categories) VALUES (?, ?, ?)', (datetime.now(), 0, i))
    
    db.commit()


# Проверка, есть ли в БД таблица с определённым юзером
def check_db(id):
    
    table = 'a' + str(id) 

    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    a = cursor.fetchone()

    if a:
        return True
    else:
        return False
    

def get_info(id, a):
    table = 'a' + str(id)
    try:
        cursor.execute(f"SELECT {a} FROM {table} WHERE {a} IS NOT NULL ORDER BY ROWID DESC LIMIT 1")
        b = cursor.fetchone()

        return b[0]
    except:
        return False


def get_categories(id, type):
    table = 'a' + str(id)

    if type == '+' or type == 'in':     # Доход
        cursor.execute(f'SELECT in_categories FROM {table}')
    elif type == '-' or type == 'sp':   # Трата
        cursor.execute(f'SELECT sp_categories FROM {table}')

    result = [row[0] for row in cursor.fetchall() if row[0] is not None]     # Получение списка категорий

    db.commit()
    return result


def delete_table(id):
    table = 'a' + str(id)

    cursor.execute(f"DROP TABLE {table}")
    db.commit()
    
    return True


def cat_add(id, name, type):
    table = 'a' + str(id)

    cursor.execute(f"SELECT * FROM {table} WHERE in_categories = ? OR sp_categories = ?", (name, name,))  # Проверка есть ли такая категория
    result = cursor.fetchall()

    if not result:
        cursor.execute(f'INSERT INTO {table} (date, {type}categories) VALUES (?, ?)', (datetime.now(), name,))
        db.commit()
        return True
    else:
        return False


def operation_add(id, category, type, sum, comm):
    table = 'a' + str(id)

    cursor.execute(f"SELECT main_currency FROM {table} WHERE main_currency IS NOT NULL ORDER BY ROWID DESC LIMIT 1")
    main_currency = cursor.fetchone()[0]

    if ' ' in sum:
        sum = sum.split(' ')
        cur = sum[1].upper()
        sum = float(sum[0])
    else:
        cur = main_currency
        sum = float(sum)

    cursor.execute(f"SELECT balance FROM {table} WHERE balance IS NOT NULL ORDER BY ROWID DESC LIMIT 1")
    balance = cursor.fetchone()[0]

    if cur != main_currency:
        sum_ = sum * cur_rate[f'{cur}_to_{main_currency}']
    else:
        sum_ = sum

    if type == '+':
        cur_balance = balance + sum_

        cursor.execute(f'INSERT INTO {table} (date, operation, sum, currency, category, balance, comment) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                       (datetime.now(), type, sum, cur, category, cur_balance, comm))        
        db.commit()    
        return True

    elif type == '-':
        cur_balance = balance - sum_

        cursor.execute(f'INSERT INTO {table} (date, operation, sum, currency, category, balance, comment) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                       (datetime.now(), type, sum, cur, category, cur_balance, comm))        
        db.commit()    
        return True
    

# Удаление операции
def delete_operation(id, opid):
    table = 'a' + str(id)

    # Выбор операции
    cursor.execute(f"SELECT operation, sum, currency, balance FROM {table} WHERE rowid=?",(opid,))
    result = cursor.fetchall()   # ([operation, sum, currency, balance])

    cur = get_info(id, 'main_currency')             # Получение основной валюты
    bal = get_info(id, 'balance')                   # Получение текущего баланса


    # Обновление баланса
    if result[0][2] != cur:                                           # Если валюта удаляемой операции не совпадает с основной валютой...
        sum = result[0][1] * cur_rate[f'{result[0][2]}_to_{cur}']     # То сумма операции конвертируется к основной валюте.
    else:                                                             # Если совпадает...
        sum = result[0][1]                                            # Сумма остаётся прежней и присваивается переменной sum.
    
    if result[0][0] == '+':                          # Если операция была доходом...
        new_balance = bal - sum                      # Новый баланс = текущий баланс - сумма операции.
    else:                                            # Если операция была тратой...
        new_balance = bal + sum                      # Новый баланс = текущий баланс + сумма операции.

    cursor.execute(f"INSERT INTO {table} (balance) VALUES (?)", (new_balance,))     # Добавление нового баланса в таблицу 

    # Удаление операции
    cursor.execute(f"UPDATE {table} SET date=NULL, operation=NULL, currency=NULL, sum=NULL, category=NULL, balance=NULL, comment=NULL WHERE rowid={opid}")

    db.commit()
    return True

    

def delete_category(id, category):
    table = 'a' + str(id)

    cursor.execute(f"UPDATE {table} SET date=NULL, operation=NULL, currency=NULL, sum=NULL, category=NULL, balance=NULL, comment=NULL, in_categories=NULL, sp_categories=NULL WHERE category=? OR in_categories=? OR sp_categories=?", (category, category, category,),)
    db.commit()
    return True


# Добавление данных в таблицу
def add_data(id, column, data):
    table = 'a' + str(id)

    cursor.execute(f'INSERT INTO {table} (date, {column}) VALUES (?, ?)', (datetime.now(), data,))

    db.commit()
    return True


def change_sum_currency(id, new_currency):
    table = 'a' + str(id)

    try:
        # Определение нынешней основной валюты
        cursor.execute(f"SELECT main_currency FROM {table} WHERE main_currency IS NOT NULL ORDER BY rowid DESC LIMIT 1")
        now_currency = cursor.fetchone()[0]

        # Получение курса для редактирования сумм операций
        rate = cur_rate[f'{now_currency}_to_{new_currency}']

        # Редактирование сумм операций
        cursor.execute(f"""
            UPDATE {table}
            SET 
                sum = sum * ?,
                currency = ?
            WHERE 
                currency = ?
        """, (rate, new_currency, now_currency))

        # Определение новой основной валюты и баланса
        add_data(id, 'main_currency', new_currency)
        bal = get_info(id, 'balance')
        add_data(id, 'balance', bal * rate)
        db.commit()

    # Отработчик ошибки на слуйчай, если не была определена основная валюта или нет операций
    except:
        add_data(id, 'main_currency', new_currency)
        db.commit()

    return True


# Редактирование названия категории
def edit_cat(id, newname, oldname):
    table = 'a' + str(id)

    cursor.execute(f'''
UPDATE {table}
SET
    category = CASE WHEN category = "{oldname}" THEN "{newname}" ELSE category END,
    in_categories = CASE WHEN in_categories = "{oldname}" THEN "{newname}" ELSE in_categories END,
    sp_categories = CASE WHEN sp_categories = "{oldname}" THEN "{newname}" ELSE sp_categories END
WHERE 
    category = "{oldname}" OR in_categories = "{oldname}" OR sp_categories = "{oldname}"''')

    db.commit()
    return True


def get_all_operations(id):
    table = 'a' + str(id)

    cursor.execute(f'SELECT rowid, * FROM {table} WHERE operation IS NOT NULL ORDER BY ROWID DESC')
    a = cursor.fetchall()

    db.commit()
    return a


# Получение истории операций
def get_history(id, category, operation, period, page):
    table = 'a' + str(id)
    
    # Определение периода
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'alltime':
        date = datetime(1970, 1, 1, 0, 0, 0)   
    elif period == 'week':
        date = today - timedelta(days=today.weekday())
    elif period == 'month':
        date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Определение типа операции
    if operation == 'income':
        operation = '+'
    elif operation == 'spends':
        operation = '-'

    # Определение страницы
    if page != 'all':     
        limit = 10  
        offset = (page - 1) * limit
    else:
        limit = 99999
        offset = 0

    # Определение условий(категория/тип операции) для дальнейшей выборки операций из таблицы
    category_condition = f"category = '{category}'" if category != "all" else "category IS NOT NULL"
    operation_condition = f"operation = '{operation}'" if operation != "all" else "operation IS NOT NULL"

    # Получение операций из таблицы
    cursor.execute(f"SELECT rowid, * FROM {table} WHERE date > '{date}' AND {category_condition} AND {operation_condition} AND sum IS NOT NULL ORDER BY ROWID DESC LIMIT {limit} OFFSET {offset}")

    # Возврат операций
    result = cursor.fetchall()
    return result


def get_operation(id, opid):
    table = 'a' + str(id)

    try:
        cursor.execute(f'SELECT rowid, * FROM {table} WHERE rowid={opid} AND sum IS NOT NULL')
        result = cursor.fetchall()
        db.commit()

        # Создание сообщения
        msg = '' 
        for i in result:
            # Определение смайлика       
            if i[2] == '+':
                msg += '🟢'
            else: msg += '🔴'

            # Определение даты
            date = str(i[1])[8:10] + '.' + str(i[1])[5:7] + '.' + str(i[1])[2:4]

            # Определение суммы
            summa = '{:.2f}'.format(i[3]).rstrip('0').rstrip('.')

            # Создание самого сообщения
            msg += f'<b> {i[2]}{summa} {i[4]}▫️<i>{i[5]}</i></b>▫️{date} [<code>{i[0]}</code>]\n'       
            if i[7] is not None:                # Если в операции есть комментарий...
                msg += f"<i>{i[7]}</i>\n"       # То он добавляется к сообщению

        return msg

    except:
        return False
    

def get_database_xlsx(id):
    table = 'a' + str(id)
    query = f"SELECT rowid, * FROM {table}"

    # Чтение данных из SQLite в DataFrame
    df = pd.read_sql_query(query, db)

    df = df.drop(['in_categories', 'sp_categories', 'main_currency'], axis=1, errors='ignore')

    # Сохранение данных в Excel-файл
    df.to_excel(f'temp/{table}.xlsx', index=False)


def check_data(id, column):
    table = 'a' + str(id) 

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL")
        a = cursor.fetchone()[0]

        return bool(a)
    
    except:
        return False
    

def start_get_last_operations(id, type, amount):
    table = 'a' + str(id)
    try:
        cursor.execute(f"SELECT rowid, * FROM {table} WHERE operation = ? ORDER BY rowid DESC LIMIT ?",
                    (type, amount))
        
        a = cursor.fetchall()

        dic = {
            '+': '🟢',
            '-': '🔴'
        }
        
        text = ''
        for i in a:
            summa = '{:.2f}'.format(i[3]).rstrip('0').rstrip('.')
            text += ''.join(f'<b>{dic[i[2]]} {i[2]}{summa} {i[4]}▫️{i[5]}▫️{i[1][8:10]}.{i[1][5:7]}\n</b>')

        return text
    
    except:
        return False



      







