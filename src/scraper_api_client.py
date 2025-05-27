import requests
import logging
from typing import Optional

class ScraperAPIClient:
    def __init__(self, api_key: str, country_code: str = "it", render: bool = False, premium: bool = False, session_number: Optional[int] = None):
        self.api_key = api_key
        self.base_url = "http://api.scraperapi.com"
        self.default_params = {
            "api_key": self.api_key,
            "country_code": country_code,
            "render": str(render).lower(),
            "premium": str(premium).lower()
        }
        if session_number is not None:
            self.default_params["session_number"] = str(session_number)

    def get(self, url: str, extra_params: Optional[dict] = None, timeout: int = 30) -> Optional[str]:
        params = self.default_params.copy()
        params["url"] = url
        if extra_params:
            params.update(extra_params)

        try:
            response = requests.get(self.base_url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"ScraperAPI request failed: {e}")
            return None
