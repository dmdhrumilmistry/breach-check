from breach_check.logger import logger
from datetime import datetime
from json import dumps as json_dumps, JSONDecodeError
from os.path import isfile


def generate_unique_filename():
    current_time = datetime.now()
    timestamp = current_time.strftime(
        "%Y%m%d%H%M%S")  # YearMonthDayHourMinuteSecond
    unique_filename = f"output_{timestamp}.json"
    return unique_filename


def extract_emails(file_path: str) -> list[str] | None:
    if not isfile(file_path):
        logger.error(f'Input File with Emails Not Found: {file_path}')
        return

    with open(file_path, 'r') as f:
        emails = [email.strip() for email in f.read().splitlines()]

    return emails


def write_json_file(file_path: str, json_data) -> bool:
    if isfile(file_path):
        logger.warning(f'{file_path} data will be overwritten')

    try:
        json_data = json_dumps(json_data)
    except JSONDecodeError:
        logger.error('Invalid JSON Data')
        return False
    except Exception as e:
        logger.error(f'Exception: {e}')
        return False

    with open(file_path, 'w') as f:
        f.write(json_data)
        logger.info(f'data written to {file_path} successfully')

    return True
