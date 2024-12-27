import logging
from logging.handlers import RotatingFileHandler
import time

import requests
from telebot import TeleBot

from constants import PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, RETRY_PERIOD, HEADERS, HOMEWORK_VERDICTS, ENDPOINT, timestamp, OK


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Функция отвечает за проверку переменных."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for key in tokens:
        if key is None:
            logger.critical(f'Отсутствует обязательная переменная окружения: {key}')
            raise EnvironmentError(f'Отсутствует обязательная переменная окружения: {key}')


def send_message(bot, message):
    """Функция отвечает за отправку сообщений пользователю."""
    @bot.message_handler(commands=['check'])
    def send_message_bot(bot, message):
        """Функция отвечает за отправку сообщений пользователю."""
        chat = message.chat
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'Проект: , статус: ')
        logger.info('Сообщение успешно отправлено')


def get_api_answer(timestamp):
    """Функция отвечает за получение информации от API."""
    PARAMS = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=PARAMS)
    if response is None:
        logger.debug('Пустой список работ.')
    if response.status_code != OK:
        logger.critical('API не работает!')
        raise Exception('API не работает!')

    return response.json()

def check_response(response):
    """Функция проверяет ответ API на соответствие ожидаемой структуре."""
    if not isinstance(response, dict):
        logger.error('Ответ API должен быть словарем.')
        raise TypeError('Ответ API должен быть словарем.')
    if type(response.get('homeworks')) != list:
        logger.error('Данные пришли не в списке.')
        raise TypeError('Данные пришли не в списке.')
    expected_keys = ['homeworks', 'current_date']
    for key in expected_keys:
        if key not in response:
            logger.error(f'В ответе API отсутствует ключ: {key}')
    if len(response.get('homeworks')) == 0:
        response = None

    return response


def parse_status(homework):
    """Функция отвечает за парсинг статуса проекта."""
    verdict = homework.get('homeworks')[0].get('status')
    try:
        homework_name = homework.get('homeworks')[0].get('lesson_name')
    except IndexError:
        logger.info('У вас нет домашней работы')
        homework_name = None
        verdict = None
    if homework_name is not None:
        return f'Изменился статус проверки работы "{homework_name}". {HOMEWORK_VERDICTS.get(verdict)}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    check_tokens()
    answer_API = get_api_answer(timestamp)
    try:
        response = check_response(answer_API)
        homework = parse_status(response)
    except AttributeError:
        logger.info('У вас нет домашнего задания')

    while True:
        try:
            bot.polling()
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
