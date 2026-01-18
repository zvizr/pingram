import os

import httpx
    
# if not os.environ.get('TG_BOT_TOKEN'):
#     print('Environment Variable: [TG_BOT_TOKEN] is not set, exiting.')
#     exit(1)

# TOKEN = os.environ.get('TG_BOT_TOKEN')

TOKEN = '8360111661:AAGRL4t6jZNLy1YiWgqITPyRwgZtmntjMDI'


class Pingram():
    def __init__(self, token: str) -> None:
        self.token = token
        self.client = httpx.Client()
        self.endpoints = {
            'msg': f'https://api.telegram.org/bot{TOKEN}/sendMessage',
            'photo': f'https://api.telegram.org/bot{TOKEN}/sendPhoto',
            'doc': f'https://api.telegram.org/bot{TOKEN}/sendDocument',
            'me': f'https://api.telegram.org/bot{TOKEN}/getMe',
        }
        
        
    def _check_key(self, key: str) -> str:
        try:
            return self.endpoints[key]
        except KeyError:
            raise KeyError(f'Endpoint {key} is missing.')
        
    def _get(self, key: str, data: dict | None = None) -> httpx.Response :
        url = self._check_key(key)
        try:
            return self.client.get(url=url, params=data, timeout=10)
        except httpx.RequestError as e:
            raise ConnectionError(f'GET Requst Failed: {e}')
    
    def _post(self, key: str, data: dict | str | None = None) -> httpx.Response:
        url = self._check_key(key)
        try:
            return self.client.post(url=url, params=data, timeout=10)
        except httpx.RequestError as e:
            raise ConnectionError(f'POST Request Failed: {e}')
    
    def send(self, endpoint: str, payload: dict | str | None = None) -> httpx.Response:
        endpoint = endpoint.lower()
        if endpoint == 'msg':
            if isinstance(payload, dict):
                payload = {
                    'chat_id': payload.get('chat_id', {}),
                    'text': payload.get('text', {})
                }
            return self._post('msg', payload)
        
        elif endpoint == 'photo':
            return self._post('photo', payload)
        
        elif endpoint == 'doc':
            return self._post('doc', payload)
        
        elif endpoint == 'me':
            return self._get('me')
        else:
            raise ValueError(f"Unsupported send type '{type}'")
        
        
bot = Pingram(token=TOKEN)
print(bot.send('msg', payload={'chat_id': CHAT_ID, 'text': 'This is a test.'}).text)