import logging
import sys
import time
from http import HTTPStatus

import requests
from telebot import TeleBot

from constants import (
    PRACTICUM_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    RETRY_PERIOD,
    HEADERS,
    HOMEWORK_VERDICTS,
    ENDPOINT,
)
from exceptions import (
    HttpStatusNotOkError,
    TokenNoFound,
    NotDictTypeData,
    NotListTypeData,
    KeyNotFound,
    ListIsEmpty)


# Logging settings.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Handler settings.
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
# Add handler.
logger.addHandler(handler)


def check_tokens():
    """Функция отвечает за проверку переменных."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for key in tokens:
        if key is None:
            logger.critical(
                'Отсутствует обязательная переменная окружения: '
                f'{key}'
            )
            raise TokenNoFound(
                'Отсутствует обязательная переменная окружения: '
                f'{key}'
            )


def send_message(bot, message):
    """Функция отвечает за отправку сообщений пользователю."""
    try:
        logger.debug('Начало отправки сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения: {error}')
    else:
        logger.debug('Сообщение отправлено успешно')


def get_api_answer(timestamp):
    """Функция отвечает за получение информации от API."""
    PARAMS = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=PARAMS)
        response.raise_for_status()
    except requests.RequestException as error:
        logger.error(f'Ошибка при запросе к API: {error}.'
                     f' URL: {ENDPOINT}, Параметры: {PARAMS}')
        raise ValueError('Ошибка при запросе к API')

    try:
        data = response.json()
    except ValueError as error:
        logger.error('Ошибка декодирования JSON:'
                     f' {error}. Ответ: {response.text}')
        raise ValueError('Ответ не в формате JSON')

    if response.status_code != HTTPStatus.OK:
        logger.critical(f'Ошибка при запросе к API: {requests.status_codes}')
        raise HttpStatusNotOkError('Получен http статус отличный от 200')

    logger.debug('Функция get_api_answer отработала удачно')
    return data


def check_response(response):
    """Функция проверяет ответ API на соответствие ожидаемой структуре."""
    if type(response) != dict:
        logger.error('Ответ API должен быть словарем.')
        raise NotDictTypeData('Ответ API должен быть словарем.')

    if type(response.get('homeworks')) != list:
        logger.error('Данные пришли не в списке.')
        raise NotDictTypeData('Данные пришли не в списке.')

    expected_keys = ['homeworks', 'current_date']
    for key in expected_keys:
        if key not in response:
            logger.error(f'В ответе API отсутствует ключ: {key}')
            raise KeyNotFound(f'В ответе API отсутствует ключ: {key}')

    return response


def parse_status(homework):
    """Функция отвечает за парсинг статуса проекта."""
    homeworks = homework.get('homeworks')

    if homeworks is None:
        logger.error(
            'Получены данные без ключа "homeworks" или значение None.'
        )

    try:
        homework_data = homeworks[0]
    except IndexError:
        logger.error('Список "homeworks" пуст.')
        raise ListIsEmpty('Список "homeworks" пуст.')

    if 'lesson_name' not in homework_data or 'status' not in homework_data:
        logger.error('Отсутствуют необходимые ключи в данных homework.')
        raise KeyNotFound('Отсутствуют ключи "lesson_name" или "status".')

    homework_name = homework_data.get('lesson_name')
    verdict = HOMEWORK_VERDICTS.get(homework_data.get('status'))
    logger.debug('Функция parse_status успешно выполнена.')
    return f'Изменился статус работы: "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 1732913297
    previos_message = None
    previos_message_error = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if not homework:
                message = 'У вас нет домашней работы.'
                send_message(bot, message)
                return

            message = parse_status(homework)
            if message != previos_message:
                send_message(bot, message)
                timestamp = response.get('current_date', timestamp)
                previos_message = message

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            try:
                if error != previos_message_error:
                    bot.send_message(TELEGRAM_CHAT_ID, message)
                    previos_message_error = error
            except Exception as e:
                logger.error('Невозможно отправить'
                             f' сообщение в телеграмм. {e}')
                logger.error(f'Сообщение отправлено с ошибкой {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
