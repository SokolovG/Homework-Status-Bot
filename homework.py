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
    ApiError,
    JsonError,
    UnknownHomework
)


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
    """The function is responsible for checking variables."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for key in tokens:
        if key is None:
            logger.critical(
                'A required environment variable is missing.: '
                f'{key}'
            )
            raise TokenNoFound(
                'A required environment variable is missing.: '
                f'{key}'
            )


def send_message(bot, message):
    """The function is responsible for sending messages to the user."""
    try:
        logger.debug('Start of message sending')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Error while sending the message: {error}')
    else:
        logger.debug('Message sent successfully')


def get_api_answer(timestamp):
    """The function is responsible for retrieving information from the API."""
    PARAMS = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=PARAMS)

    except requests.RequestException as error:
        logger.error(f'Error while making a request to the API: {error}.'
                     f' URL: {ENDPOINT}, params: {PARAMS}')
        raise ApiError('Error while making a request to the API')

    try:
        data = response.json()
    except ValueError as error:
        logger.error('JSON decoding error:'
                     f'{error}. Answer: {response.text}')
        raise JsonError('Answer is not in JSON format.')

    if response.status_code != HTTPStatus.OK:
        logger.critical('Error while making a request to the API:'
                        f'{requests.status_codes}')
        raise HttpStatusNotOkError('Received HTTP status other than 200.')

    logger.debug('The function get_api_answer executed successfully.')
    return data


def check_response(response):
    """Checks that the API response matches the expected structure."""
    if not isinstance(response, dict):
        logger.error('The API response must be a dictionary.')
        raise NotDictTypeData('The API response must be a dictionary.')

    if 'homeworks' not in response:
        logger.error('The API response is missing the key "homeworks".')
        raise KeyNotFound('The API response is missing the key "homeworks".')

    if not isinstance(response['homeworks'], list):
        logger.error('The key "homeworks" must contain a list.')
        raise NotListTypeData('The key "homeworks" must contain a list.')

    if 'current_date' not in response:
        logger.error('The API response is missing the key ‘current_date.')
        raise KeyNotFound('The API response is missing the key ‘current_date.')

    if len(response['homeworks']) == 0:
        return False

    logger.debug('The structure of the API response is valid.')

    return response['homeworks'][0]


def parse_status(homework):
    """A function to generate a string with the homework check status."""
    if not isinstance(homework, dict):
        raise NotDictTypeData('The argument ‘homework’ must be a dictionary.')

    if 'homework_name' not in homework:
        raise KeyNotFound('The API response is missing the key "homeworks".')

    if 'status' not in homework:
        raise KeyNotFound('The API response is missing the key "status".')

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_VERDICTS:
        raise UnknownHomework(f'Unknown homework status: {homework_status}')

    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}": {verdict}'


def main():
    """The main logic of the bot’s operation."""
    check_tokens()  # Checking for the presence of tokens
    bot = TeleBot(token=TELEGRAM_TOKEN)  # Bot creating.
    timestamp = int(time.time())
    previous_message = None
    previous_error_message = None
    response = get_api_answer(timestamp)

    while True:
        try:

            response = get_api_answer(timestamp)
            if not check_response(response):
                logger.debug('The ‘homeworks’ list is empty.')
                send_message(bot, 'You have no homework.')
                time.sleep(RETRY_PERIOD)

            homework = check_response(response)
            message = parse_status(homework)

            if message != previous_message:
                send_message(bot, message)
                previous_message = message
                timestamp = response.get('current_date', timestamp)

        except Exception as error:
            error_message = f'Program error: {error}'
            logger.error(error_message)
            if error_message != previous_error_message:
                try:
                    send_message(bot, error_message)
                    previous_error_message = error_message
                except Exception as telegram_error:
                    logger.error(
                        'Error while sending error message to Telegram:'
                        f' {telegram_error}'
                    )
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
