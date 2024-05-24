"""
Base class for breach backends.
"""
from ..http import AsyncRequests


class BaseBreachBackend:
    """
    Base class for breach backends.

    Args:
        http_client (AsyncRequests): An instance of the HTTP client used for making requests.

    Attributes:
        _http_client (AsyncRequests): The HTTP client used for making requests.
    """

    def __init__(self, http_client: AsyncRequests) -> None:
        self._http_client = http_client

    async def check_email_breaches(self, email: str):
        """
        Check for breaches using the backend.

        Args:
            email (str): The email address to check for breaches.

        Returns:
            dict: A dictionary containing the results of the breach check.
        """
        raise NotImplementedError

