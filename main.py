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
    
    def _post(self, key: str, 
              data: dict[str, Any] | None = None,
              files: dict[str, Any] | None = None) -> httpx.Response:
        
        url = self._check_key(key)
        try:
            return self.client.post(url=url, data=data, files=files, timeout=10)
        except httpx.RequestError as e:
            raise ConnectionError(f'POST Request Failed: {e}')
        
        
    def me(self): return self._get('me')
        
        
    def send_photo(self, chat_id: str, path: str, **kwargs) -> httpx.Response:
        data = {'chat_id': chat_id, **kwargs}
        
        if path.startswith('http'):
            data['photo'] = path
            return self._post('photo', data=data)
        
        with open(path, 'rb') as f:
            files = {'photo': f}
            return self._post('photo', data=data, files=files)
        
        
    def send_doc(self, chat_id: str, path: str, **kwargs) -> httpx.Response:
        data = {'chat_id': chat_id, **kwargs}
        
        if path.startswith('http'):
            data['document'] = path
            return self._post('doc', data=data)
        
        with open(path, 'rb') as f:
            files = {'document': f}
            return self._post('doc', data=data, files=files)
    
    
    def send(self, endpoint: str, payload: dict[str, Any] | None = None, **kwargs) -> httpx.Response | str:
        endpoint = endpoint.lower()
        
        if endpoint == 'me':
            return self.me()
        
        if endpoint == 'msg':
            if isinstance(payload, dict):
                payload = {
                    'chat_id': payload.get('chat_id', ''),
                    'text': payload.get('text', '')
                }
            return self._post('msg', payload)
        
        elif endpoint == 'photo':
            if isinstance(payload, dict):
                extras = {k: v for k, v in payload.items() if k not in ('chat_id', 'path')}
                try:
                    chat_id = payload.get('chat_id', '')
                    path = payload.get('path', '')
                    caption = payload.get('caption', '')
                    return self.send_photo(chat_id, path, caption=caption)
                except Exception as e:
                    raise e
                
        elif endpoint == 'doc':
            if isinstance(payload, dict):
                try:
                    chat_id = payload.get('chat_id', '')
                    path = payload.get('path', '')
                    caption = payload.get('caption', '')
                    extras = {k: v for k, v in payload.items() if k not in ('chat_id', 'path')}
                    return self.send_doc(chat_id, path, caption=caption)
                except Exception as e:
                    raise e
        raise ValueError(f'Unsupported send type: {endpoint}')