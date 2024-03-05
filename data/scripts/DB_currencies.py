import requests
import sqlite3


db = sqlite3.connect('data/database/currencies.db', check_same_thread=False)
cursor = db.cursor()


# Обновление курса одной пары валют
def update_currate(currency, value, date):
    cursor.execute(f"UPDATE curr SET rate=?, date=? WHERE currency=?", (value, date, currency))
    db.commit()


# Получение курса одной пары валют из таблицы
def get_rates(currency):
    cursor.execute(f"SELECT rate FROM curr WHERE currency=?", (currency,))
    result, = cursor.fetchone()
    return result


# Получение даты последнего обновления курса валют
def get_date():
    cursor.execute("SELECT date FROM curr WHERE rowid=1")       # В качестве даты берётся дата первой пары в таблице
    result, = cursor.fetchone()
    return result


# Словарь, хранящий курсы валют
cur_rate = {                                    # RUB
    'RUB_to_UAH': get_rates('RUB_to_UAH'),
    'RUB_to_USD': get_rates('RUB_to_USD'),
    'RUB_to_EUR': get_rates('RUB_to_EUR'),
    'RUB_to_BYN': get_rates('RUB_to_BYN'),
    'RUB_to_KZT': get_rates('RUB_to_KZT'),
                                                # UAH
    'UAH_to_USD': get_rates('UAH_to_USD'),
    'UAH_to_EUR': get_rates('UAH_to_EUR'),
    'UAH_to_RUB': get_rates('UAH_to_RUB'),
    'UAH_to_BYN': get_rates('UAH_to_BYN'),
    'UAH_to_KZT': get_rates('UAH_to_KZT'),
                                                # EUR
    'EUR_to_USD': get_rates('EUR_to_USD'),
    'EUR_to_RUB': get_rates('EUR_to_RUB'),
    'EUR_to_UAH': get_rates('EUR_to_UAH'),
    'EUR_to_BYN': get_rates('EUR_to_BYN'),
    'EUR_to_KZT': get_rates('EUR_to_KZT'),
                                                # USD
    'USD_to_RUB': get_rates('USD_to_RUB'),
    'USD_to_EUR': get_rates('USD_to_EUR'),
    'USD_to_UAH': get_rates('USD_to_UAH'),
    'USD_to_BYN': get_rates('USD_to_BYN'),
    'USD_to_KZT': get_rates('USD_to_KZT'),
                                                # BYN
    'BYN_to_RUB': get_rates('BYN_to_RUB'),
    'BYN_to_USD': get_rates('BYN_to_USD'),
    'BYN_to_EUR': get_rates('BYN_to_EUR'),
    'BYN_to_UAH': get_rates('BYN_to_UAH'),
    'BYN_to_KZT': get_rates('BYN_to_KZT'),
                                                # KZT
    'KZT_to_RUB': get_rates('KZT_to_RUB'),
    'KZT_to_USD': get_rates('KZT_to_USD'),
    'KZT_to_EUR': get_rates('KZT_to_EUR'),
    'KZT_to_BYN': get_rates('KZT_to_BYN'),
    'KZT_to_UAH': get_rates('KZT_to_UAH'),
}


# Обновление курсов валют
def update_currency():
    currencies = list(cur_rate.keys())          # Получение ключей из словаря (к примеру 'RUB_to_UAH')

    # Цикл обновления курса каждой пары валют из словаря
    for name in currencies:
        _from = name.split('_')[0]              # Получение названия основной валюты (в примере 'RUB_to_UAH' это будет RUB)
        _to = name.split('_')[2]                # Получение названия конечной валюты (в примере 'RUB_to_UAH' это будет UAH)

        url = f'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{_from.lower()}.json'    # Ссылка на API для конвертации валют

        try:
            response = requests.get(url)            # Запрос к API

            if response.status_code == 200:
                data = response.json()              # Получение ответа API

                if data:
                    rate = response.json().get(_from.lower(), {}).get(_to.lower())          # Получение курса
                    date = data.get('date')                                                 # Получение даты последнего обновления курса

                    update_currate(name, rate, date)                                        # Обновление курса одной пары валют в таблице
                    cur_rate[name] = rate                                                   # Обновление курса одной пары валют в словаре
                    print(name, rate, date)                                                 # Вывод информации в консоль

                else:
                    print("Данные о курсах валют не найдены.")

        except requests.exceptions.RequestException as e:
            print(f"Произошла ошибка при запросе к API: {e}")

