
mkdir crypto-rates-paprika
cd crypto-rates-paprika
git init

"""Модуль работы с CoinPaprika API."""

import requests

API_URL = "https://api.coinpaprika.com/v1/tickers"

# Список популярных монет: id в CoinPaprika -> (название, тикер)
COINS = {
    "btc-bitcoin":          ("Bitcoin",  "BTC"),
    "eth-ethereum":         ("Ethereum", "ETH"),
    "usdt-tether":          ("Tether",   "USDT"),
    "bnb-binance-coin":     ("BNB",      "BNB"),
    "sol-solana":           ("Solana",   "SOL"),
    "xrp-xrp":              ("XRP",      "XRP"),
    "ada-cardano":          ("Cardano",  "ADA"),
    "doge-dogecoin":        ("Dogecoin", "DOGE"),
    "ton-the-open-network": ("Toncoin",  "TON"),
}

AUTO_OPTIONS = {"Выкл": 0, "30 секунд": 30, "1 минута": 60, "5 минут": 300}


def fetch_prices(timeout: float = 15.0) -> dict:
    """Возвращает {id: {"usd": цена, "usd_24h_change": изменение}}.

    CoinPaprika отдаёт весь рынок одним запросом; здесь мы оставляем
    только нужные монеты и приводим ответ к формату, который ожидает
    интерфейс. Ключ API не требуется (лимит без ключа — 10 запросов/сек).
    """
    params = {"quotes": "USD"}
    try:
        response = requests.get(API_URL, params=params, timeout=timeout)
        response.raise_for_status()
        tickers = response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("Сервер не ответил вовремя. Проверьте соединение.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Нет соединения с интернетом.")
    except ValueError:
        raise RuntimeError("Сервер вернул некорректный ответ.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ошибка запроса: {e}")

    if not isinstance(tickers, list):
        raise RuntimeError("Неожиданный формат ответа API.")

    # Приводим ответ CoinPaprika к единому виду:
    # {id: {"usd": цена, "usd_24h_change": процент за 24 ч}}
    result = {}
    for item in tickers:
        coin_id = item.get("id")
        if coin_id not in COINS:
            continue
        usd = item.get("quotes", {}).get("USD", {})
        result[coin_id] = {
            "usd": usd.get("price"),
            "usd_24h_change": usd.get("percent_change_24h"),
        }

    if not result:
        raise RuntimeError("API не вернул данные по нужным монетам.")
    return result
python -c "from api import fetch_prices; print(fetch_prices())"
git add api.py
git commit -m "feat: модуль запросов курсов к CoinPaprika API"

