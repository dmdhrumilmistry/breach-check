"""
This module contains the implementation of MozillaMonitor class which checks email breaches using mozilla monitor API.
"""
from json import loads as json_loads
from breach_check.breach_factory.base import BaseBreachBackend, ResultSchema
from breach_check.logger import logger
from breach_check.http import AsyncRequests


class MozillaMonitor(BaseBreachBackend):
    """
    Checks email breaches using mozilla monitor API.
    """

    def __init__(self, http_client: AsyncRequests, *args, **kwargs) -> None:
        logger.warning(
            'MozillaMonitor is deprecated since it API is no longer available. Please use other breach backends.')
        super().__init__(http_client, *args, **kwargs)
        self._api_url = 'https://monitor.firefox.com/api/v1/scan'

    async def check_email_breaches(self, email: str) -> dict:
        res_data = {
            'email': email,
            'breaches': [],
            'total': None
        }

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
        breach_sources = response.get('',[])
        is_success = res_body.get('success', False)

        if status_code == 200 and is_success:
            breaches = res_body.get('breaches', [])
            total = res_body.get('total', -1)
            res_data['breaches'] = breaches
            res_data['total'] = total

            breaches = list(filter(
                lambda domain: domain.strip() if domain else '',
                [breach.get('Domain', '').strip()
                 for breach in breach_sources]
            ))

            self.result_schemas.append(ResultSchema(
                email=email,
                breaches=breaches,
                total=total,
            ))

        elif status_code == 429:
            logger.warning('Rate Limited')

        else:
            logger.error('Failed with status code: %s', str(status_code))
            logger.error(response, res_body)

        return res_data
