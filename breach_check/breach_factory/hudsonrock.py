"""
This module contains the implementation of MozillaMonitor class which checks email breaches using mozilla monitor API.
"""
from json import loads as json_loads
from breach_check.breach_factory.base import BaseBreachBackend
from breach_check.logger import logger
from breach_check.http import AsyncRequests
from breach_check.breach_factory.base import ResultSchema


class HudsonRock(BaseBreachBackend):
    """
    Checks email for info stealer breaches using hudson rock public API.
    """

    def __init__(self, http_client: AsyncRequests, *args, **kwargs) -> None:
        super().__init__(http_client, *args, **kwargs)
        # 50 requests/10sec
        self._api_url = 'https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email'

    async def check_email_breaches(self, email: str) -> dict:
        res_data = {
            'email': email,
            'breaches': [],
            'fields':[],
            'total': None
        }

        payload = {
            'email': email
        }
        response = await self._http_client.request(
            url=self._api_url,
            method='GET',
            params=payload
        )

        status_code = response.get('status')

        match status_code:
            case 200:
                res_body = json_loads(response.get('res_body', '{}'))
                fields_compromised = []
                stolen_data = res_body.get('stealers', [])
                total = len(stolen_data)

                logger.warning('Breaches found for %s', email)
                res_data['breaches'] = stolen_data
                res_data['fields'] = fields_compromised
                res_data['total'] = total

                # get malware paths
                breaches = list(map(lambda stolen_data: f'malware: {stolen_data.get("malware_path","")}', stolen_data))

                self.result_schemas.append(ResultSchema(
                    email=email,
                    breaches=breaches,
                    total=total
                ))

            case 400:
                logger.info('No breaches found for %s', email)
                res_data['total'] = 0

            case 429:
                logger.warning('Rate Limited')

            case _:
                logger.error('Failed with status code: %s', str(status_code))
                logger.error('Response: %s\nResponse Body: %s', str(response), str(response.get("res_body", {})))

        return res_data
