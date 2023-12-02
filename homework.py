import os
import sys
import telegram
import requests
import time
import logging
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


logging.basicConfig(
    filename="logfile.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def check_tokens():
    "Проверка наличия переменных"
    required_variables = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if all(required_variables):
        return True
    else:
        for var in required_variables:
            if not var:
                logging.critical(f"Отсутствует переменная окружения: {var}")
        return False


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f"Сообщение успешно отправлено в Telegram: {message}")
    except Exception as e:
        logging.error(f"Сбой при отправке сообщения в Telegram: {e}")


def get_api_answer(timestamp):
    """Получение апи ответа"""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
        response.raise_for_status()
        if response.status_code != 200:
            logging.error(f"Ошибка: код ответа {response.status_code} от API")
            raise ValueError()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к API: {e}")


def check_response(response):
    """Проверка ответа"""
    if not isinstance(response, dict):
        raise TypeError("Response должен быть словарем")

    if not isinstance(response.get("homeworks"), list):
        raise TypeError("Homeworks должен быть списком")

    if "homeworks" not in response:
        raise KeyError("Нет такого ключа")


def parse_status(homework):
    """Парсинг статусов работ"""
    status = homework.get("status")
    homework_name = homework.get("homework_name")

    if status in HOMEWORK_VERDICTS and homework_name:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error(f"Неожиданный статус работы: {status}")
        raise KeyError("Отсутствует ключ 'homework_name'")


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        sys.exit(1)
    while True:
        try:
            response = get_api_answer(timestamp)
            if response is not None:
                check_response(response)
                updates = response.get("homeworks")
                if updates:
                    for homework in updates:
                        status = parse_status(homework)
                        if status:
                            send_message(bot, f"{status}")
                else:
                    logging.debug("Нет новых статусов в ответе API.")
            else:
                logging.error("Не удалось получить данные от API.")
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.exception(message)
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
