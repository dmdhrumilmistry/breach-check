"""
This module contains the BreachChecker class which is used to check if an email address has been involved in any data breaches.
"""
from asyncio import ensure_future, gather
from enum import Enum
from re import compile

from aiohttp.client_exceptions import ClientProxyConnectionError
from rich.progress import Progress, TaskID

from breach_check.http import AsyncRequests
from breach_check.logger import logger, console
from breach_check.breach_factory.base import ResultSchema
from breach_check.breach_factory.leakcheck import LeakCheck
from breach_check.breach_factory.hudsonrock import HudsonRock

class BreachCheckerBackendChoices(Enum):
    """
    Enum for breach checker backend choices.
    """
    LEAKCHECK = 'leakcheck'
    HUDSONROCK = 'hudsonrock'

class BreachChecker:
    """
    Wrapper for checking email breaches using breach factory.
    """

    def __init__(self, *args, rate_limit: int = 60, headers: dict | None = None, proxy: str | None = None, ssl: bool | None = True, allow_redirects: bool | None = True, backend:str='leakcheck',**kwargs) -> None:
        """
        Initialize the BreachCheck object.

        Args:
            rate_limit (int): The rate limit for making HTTP requests. Defaults to 60.
            delay (float | None): The delay between consecutive HTTP requests. Defaults to None.
            headers (dict | None): The headers to be included in the HTTP requests. Defaults to None.
            proxy (str | None): The proxy server to be used for making HTTP requests. Defaults to None.
            ssl (bool | None): Whether to use SSL for making HTTP requests. Defaults to True.
            allow_redirects (bool | None): Whether to allow HTTP redirects. Defaults to True.
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        if not headers:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }

        self.progress = Progress(console=console)
        self.progress_task_id: TaskID | None = None

        self._http_client = AsyncRequests(
            rate_limit=rate_limit, 
            headers=headers,
            proxies=proxy,
            ssl=ssl,
            allow_redirects=allow_redirects
        )

        breachfactory = None
        match backend:
            case BreachCheckerBackendChoices.HUDSONROCK:
                breachfactory = HudsonRock
            case BreachCheckerBackendChoices.LEAKCHECK:
                breachfactory = LeakCheck
            case _:
                raise ValueError('Invalid Backend Choice!')
            
        self._breach_factory = breachfactory(self._http_client)
        self.result_schemas:list[ResultSchema] = []
        

    async def mass_check(self, emails: list[str] | None = None):
        """
        Perform a mass check for breaches using a list of emails.

        Args:
            emails (list[str] | None): A list of email addresses to check for breaches. Defaults to None.

        Returns:
            list: A list of results from the breach check.

        """
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
            self.result_schemas = self._breach_factory.result_schemas
            return results
        except Exception as e:
            logger.error(
                f'[*] Exception occurred while gathering results: {e}',
                stack_info=True
            )
            return []

    async def check(self, email: str | None = None) -> dict:
        """
        Check if an email has been involved in any data breaches.

        Args:
            email (str, optional): The email address to check. Defaults to None.

        Returns:
            dict: A dictionary containing the email, breaches, and total number of breaches.

        Raises:
            ConnectionRefusedError: If the server refuses the connection.
            ClientProxyConnectionError: If there is an error with the proxy connection.
        """
        if not email:
            logger.warning('email param cannot be None')
            return {}

        
        res_data = {}
        try:
            email_validator = compile(r"^[^@\s']+@[^@\s']+\.[^@\s']+$")
            if email_validator.match(email):
                res_data = await self._breach_factory.check_email_breaches(email)
            else:
                logger.warning('%s is not a valid email', email)

            # advance progress bar
            if self.progress_task_id is not None:
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
            logger.error('Proxy Connection Error: %s', str(e))
