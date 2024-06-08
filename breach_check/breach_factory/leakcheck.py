"""
This module contains the implementation of LeakCheck class which checks email breaches using mozilla monitor API.
"""
from json import loads as json_loads
from breach_check.breach_factory.base import BaseBreachBackend, ResultSchema
from breach_check.logger import logger
from breach_check.http import AsyncRequests


class LeakCheck(BaseBreachBackend):
    """
    Checks email breaches using leakcheck public API.
    """

    def __init__(self, http_client: AsyncRequests, *args, **kwargs) -> None:
        super().__init__(http_client, *args, **kwargs)
        self._api_url = 'https://leakcheck.io/api/public'

    async def check_email_breaches(self, email: str) -> dict:
        res_data = {
            'email': email,
            'breaches': [],
            'fields':[],
            'total': None
        }

        payload = {
            'check': email
        }
        response = await self._http_client.request(
            url=self._api_url,
            method='GET',
            params=payload
        )

        status_code = response.get('status')
        res_body = json_loads(response.get('res_body', '{}'))
        is_success = res_body.get('success', False)
        breach_sources = res_body.get('sources', [])
        total = res_body.get('found', -1)

        if status_code == 200 and is_success:
            logger.warning('Breaches found for %s', email)
            res_data['breaches'] = breach_sources
            res_data['fields'] = res_body.get('fields', [])
            res_data['total'] = total

            breaches = list(filter(
                lambda domain: domain.strip() if domain else '',
                [breach.get('name', '').strip()
                 for breach in breach_sources]
            ))

            self.result_schemas.append(ResultSchema(
                email=email,
                breaches=breaches,
                total=total
            ))

        elif status_code == 200:
            logger.info('No breaches found for %s', email)
            res_data['total'] = 0

        elif status_code == 429:
            logger.warning('Rate Limited')

        else:
            logger.error('Failed with status code: %s', str(status_code))
            logger.error('Response: %s\nResponse Body: %s', str(response), str(res_body))

        return res_data
