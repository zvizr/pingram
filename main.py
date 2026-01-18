from typing import Any

import httpx


class Pingram():
    def __init__(self, token: str) -> None:
        self.token = token
        self.client = httpx.Client()
        self.endpoints = {
            'msg': f'https://api.telegram.org/bot{self.token}/sendMessage',
            'photo': f'https://api.telegram.org/bot{self.token}/sendPhoto',
            'doc': f'https://api.telegram.org/bot{self.token}/sendDocument',
            'me': f'https://api.telegram.org/bot{self.token}/getMe',
        }
        
    def _check_key(self, key: str) -> str:
        try:
            return self.endpoints[key]
        except KeyError:
            raise ValueError(f'Endpoint {key} is missing.')
        
    def _get(self, key: str, data: dict | None = None) -> httpx.Response :
        url = self._check_key(key)
        try:
            return self.client.get(url=url, params=data, timeout=10)
        except httpx.RequestError as e:
            raise ConnectionError(f'GET Requst Failed: {e}')
    
    def _post(self, key: str, data: dict[str, Any] | None = None) -> httpx.Response:
        url = self._check_key(key)
        try:
            return self.client.post(url=url, data=data, timeout=10)
        except httpx.RequestError as e:
            raise ConnectionError(f'POST Request Failed: {e}')
    
    def send(self, endpoint: str, payload: dict[str, Any] | None = None) -> str:
        endpoint = endpoint.lower()
        if endpoint == 'msg':
            if isinstance(payload, dict):
                payload = {
                    'chat_id': payload.get('chat_id', ''),
                    'text': payload.get('text', '')
                }
            return self._post('msg', payload).text
        raise ValueError(f'Unsupported send type: {endpoint}')