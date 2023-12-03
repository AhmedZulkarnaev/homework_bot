import os
import sys
import time
import logging

from urllib.error import HTTPError
import telegram
import requests
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

script_path = os.path.abspath(__file__)
log_filename = os.path.join(os.path.dirname(script_path), 'program.log')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def check_tokens():
    """Проверка наличия переменных."""
    required_variables = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    missing_variables = [var_name for var_name, var in zip(
        ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'],
        required_variables) if not var]

    if missing_variables:
        logger.critical(
            f"Отсутствуют переменные окружения: {', '.join(missing_variables)}"
        )
        return False
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
    else:
        logger.debug("Сообщение успешно отправлено в Telegram")


def get_api_answer(timestamp):
    """Получение апи ответа."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
        if response.status_code != 200:
            raise HTTPError(f"Неверный код состояния: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.debug(f"Ошибка при запросе к API: {e}")


def check_response(response):
    """Проверка ответа."""
    if not isinstance(response, dict):
        raise TypeError()

    if "homeworks" not in response:
        raise KeyError()

    if not isinstance(response.get("homeworks"), list):
        raise TypeError()

    if "current_date" not in response:
        raise KeyError()

    if not isinstance(response.get("current_date"), int):
        raise TypeError()


def parse_status(homework):
    """Парсинг статусов работ."""
    status = homework.get("status")
    homework_name = homework.get("homework_name")

    if status in HOMEWORK_VERDICTS and homework_name:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    raise ValueError("Проблема со значением переменной 'status'")


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        sys.exit(1)
    while True:
        try:
            response = get_api_answer(timestamp)
            if response:
                check_response(response)
                updates = response.get("homeworks")
                if updates:
                    status = parse_status(updates[0])
                    if status:
                        send_message(bot, f"{status}")
                else:
                    logger.debug("Нет новых статусов в ответе API.")
            else:
                logger.error("Не удалось получить данные от API.")
        except HTTPError as http_error:
            logger.error(f"Ошибка HTTP при запросе к API: {http_error}")
        except requests.RequestException as request_exception:
            logger.error(f"Ошибка запроса к API: {request_exception}")
        except Exception as error:
            logger.error(f"Сбой в работе программы: {error}")
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s: %(levelname)s - %(funcName)s - %(message)s',
        filename='my_logging.log')
    main()
