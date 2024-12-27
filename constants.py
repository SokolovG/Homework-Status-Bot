import os
import time
from http import HTTPStatus

from dotenv import load_dotenv


load_dotenv()
PRACTICUM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
RETRY_PERIOD = 600
timestamp = 1730451600
# timestamp = int(time.time())
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
NOT_FOUND = HTTPStatus.NOT_FOUND
OK = HTTPStatus.OK
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
