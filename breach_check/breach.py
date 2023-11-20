from aiohttp.client_exceptions import ClientProxyConnectionError
from asyncio import ensure_future, gather
from breach_check.http import AsyncRequests
from breach_check.logger import logger, console
from json import loads as json_loads
from rich.progress import Progress, TaskID
from re import compile


class BreachChecker:
    def __init__(self, rate_limit: int | None = None, delay: float | None = None, headers: dict | None = None, proxy: str | None = None, ssl: bool | None = True, allow_redirects: bool | None = True, *args, **kwargs) -> None:
        if not headers:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }

        self.progress = Progress(console=console)
        self.progress_task_id: TaskID | None = None

        self._http_client = AsyncRequests(
            rate_limit=rate_limit,
            delay=delay,
            headers=headers,
            proxy=proxy,
            ssl=ssl,
            allow_redirects=allow_redirects
        )
        self._api_url = 'https://monitor.firefox.com/api/v1/scan'

    async def mass_check(self, emails: list[str] | None = None):
        if not emails or len(emails) == 0:
            return []

        self.progress.start()
        self.progress_task_id = self.progress.add_task(
            '[orange] Checking for Breaches:',
            total=len(emails)
        )

        tasks = []
        for email in emails:
            tasks.append(
                ensure_future(
                    self.check(email)
                )
            )

        try:
            results = await gather(*tasks)

            self.progress.stop()
            return results
        except Exception as e:
            logger.error(
                f'[*] Exception occurred while gathering results: {e}',
                stack_info=True
            )
            return []

    async def check(self, email: str | None = None) -> dict:
        if not email:
            logger.warning('email param cannot be None')
            return {}

        res_data = {
            'email': email,
            'breaches': [],
            'total': None
        }
        try:
            email_validator = compile(r"^[^@\s']+@[^@\s']+\.[^@\s']+$")
            if email_validator.match(email):
                json_payload = {
                    'email': email
                }
                response = await self._http_client.request(
                    url=self._api_url,
                    method='POST',
                    json=json_payload,
                )

                status_code = response.get('status')
                res_body = json_loads(response.get('res_body', '{}'))
                is_success = res_body.get('success', False)

                if status_code == 200 and is_success:
                    breaches = res_body.get('breaches', [])
                    total = res_body.get('total', -1)
                    res_data['breaches'] = breaches
                    res_data['total'] = total

                elif status_code == 429:
                    logger.warning('Rate Limited')

                else:
                    logger.error(f'Failed with status code: {status_code}')
                    logger.error(response, res_body)

            else:
                logger.warning(f'{email} is not a valid email')

            # advance progress bar
            if self.progress_task_id != None:
                self.progress.update(self.progress_task_id,
                                     advance=1, refresh=True)
            else:
                logger.error('No Progress Bar Task Found!')

            if self.progress and self.progress.finished:
                self.progress.stop()

            return res_data
        except ConnectionRefusedError:
            logger.error('Connection Failed! Server refused Connection!!')
        except ClientProxyConnectionError as e:
            logger.error(f'Proxy Connection Error: {e}')
