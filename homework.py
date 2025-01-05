import logging
import sys
import time
from http import HTTPStatus

import requests
from telebot import TeleBot, apihelper

from constants import (
    PRACTICUM_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    RETRY_PERIOD,
    HOMEWORK_VERDICTS,
    ENDPOINT,
    HEADERS
)
from exceptions import (
    HttpStatusNotOkError,
    NotDictTypeDataError,
    NotListTypeDataError,
    KeyNotFoundError,
    ApiConnectionError,
    JsonTypeError,
    UnknownHomeworkError,
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
            sys.exit(1)


def send_message(bot, message):
    """The function is responsible for sending messages to the user."""
    try:
        logger.debug('Start of message sending')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except apihelper.ApiException as error:
        logger.error(f'Error while sending the message: {error}')
        return False
    except requests.exceptions.RequestException as requests_error:
        logger.error(f'Requests library error: {requests_error}')
        return False
    except Exception as global_error:
        logger.error(f'Error while sending the message: {global_error}')
        return False
    else:
        logger.debug('Message sent successfully')
        return True


def get_api_answer(timestamp):
    """The function is responsible for retrieving information from the API."""
    data = {'params': {'from_date': timestamp},
            'headers': HEADERS, 'url': ENDPOINT}
    try:
        response = requests.get(**data)

    except requests.RequestException as error:
        raise ApiConnectionError(f'Error {error} while making'
                                 f'a request to the API: {error}')

    if response.status_code != HTTPStatus.OK:
        raise HttpStatusNotOkError('Error while making a request to the API:'
                                   f'{requests.status_codes}')

    try:
        data = response.json()
    except ValueError as error:
        raise JsonTypeError('JSON decoding error:'
                            f'{error}. Answer: {response.text}')

    logger.debug('The function get_api_answer executed successfully.')
    return data


def check_response(response):
    """Checks that the API response matches the expected structure."""
    if not isinstance(response, dict):
        raise NotDictTypeDataError('The API response must'
                                   f' be a dictionary, now: {type(response)}')

    if 'homeworks' not in response:
        raise KeyNotFoundError('The API response is'
                               ' missing the key "homeworks".')

    if not isinstance(response['homeworks'], list):
        homework = response['homeworks']
        raise NotListTypeDataError(f'The key "homeworks"'
                                   ' must contain a list,'
                                   f' now: {type(homework)}')

    if 'current_date' not in response:
        raise KeyNotFoundError('The API response is'
                               ' missing the key ‘current_date.')

    if len(response['homeworks']) == 0:
        return False

    logger.debug('The structure of the API response is valid.')

    return response['homeworks'][0]


def parse_status(homework):
    """A function to generate a string with the homework check status."""
    if not isinstance(homework, dict):
        raise NotDictTypeDataError('The argument ‘homework’'
                                   ' must be a dictionary,'
                                   f' now: {type(homework)}')

    if 'homework_name' not in homework:
        raise KeyNotFoundError('The API response'
                               'is missing the key "homeworks".')

    if 'status' not in homework:
        raise KeyNotFoundError('The API response is missing the key "status".')

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_VERDICTS:
        raise UnknownHomeworkError('Unknown homework status:'
                                   f' {homework_status}')

    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}": {verdict}'


def process_response(response, previous_message, bot):
    """Response checking."""
    if not check_response(response):
        logger.debug('The ‘homeworks’ list is empty.')
        return None, None

    homework = check_response(response)
    message = parse_status(homework)

    if message != previous_message:
        if send_message(bot, message):
            return message, response.get('current_date')
    return previous_message, None


def main():
    """The main logic of the bot’s operation."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = None
    previous_error_message = None
    response = get_api_answer(timestamp)

    while True:
        try:

            response = get_api_answer(timestamp)
            previous_message, new_timestamp = (
                process_response(response, previous_message, bot))

        except Exception as error:
            error_message = f'Program error: {error}'
            logger.error(error_message)
            if error_message != previous_error_message:
                try:
                    if send_message(bot, error_message):
                        previous_error_message = error_message

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
