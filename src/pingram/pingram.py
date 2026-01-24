
# SPDX-FileCopyrightText: 2026-present zvizr <zvizr@proton.me>
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026-present zvizr <zvizr@proton.me>
#
# SPDX-License-Identifier: MIT
from typing import Any, Union

import httpx


__all__ = ['Pingram']

class Pingram:
    def __init__(self, token: str) -> None:
        self.token = token
        self.client = httpx.Client()
        self.endpoints = {
            'me': f'https://api.telegram.org/bot{token}/getMe',
            'msg': f'https://api.telegram.org/bot{token}/sendMessage',
            'photo': f'https://api.telegram.org/bot{token}/sendPhoto',
            'doc': f'https://api.telegram.org/bot{token}/sendDocument',
            'audio': f'https://api.telegram.org/bot{token}/sendAudio',
            'video': f'https://api.telegram.org/bot{token}/sendVideo',
        }

    def _get(self, key: str, data: dict | None = None) -> httpx.Response:
        return self.client.get(url=self.endpoints[key], params=data, timeout=10)

    def _post(self, key: str, data: dict[str, Any], files: dict[str, Any] | None = None) -> httpx.Response:
        filtered = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
        return self.client.post(url=self.endpoints[key], data=filtered, files=files, timeout=10)
    
    def _type(self, type_map: dict) -> bool:
        for value, expected_type in type_map.items():
            if not isinstance(value, expected_type):
                raise TypeError(f"Expected {value!r} to be of type {expected_type}, got {type(value)}")
        return True

    def me(self) -> httpx.Response:
        return self._get('me')

    def message(self, chat_id: Union[str,int], text: str, **kwargs) -> httpx.Response | str:
        self._type({chat_id: str})
        return self._post('msg', {'chat_id': str(chat_id), 'text': text, **kwargs})

    def send_photo(self, chat_id: Union[str,int], path: str, caption=None, **kwargs) -> httpx.Response:
        """
        The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20
        Max file size is 10 MB
        """
        self._type({chat_id: str, path: str})
        
        data = {'chat_id': str(chat_id), **kwargs}
        if caption: data['caption'] = caption
        if path.startswith('http'):
            data['photo'] = path
            return self._post('photo', data)
        with open(path, 'rb') as f:
            return self._post('photo', data, files={'photo': f})

    def send_doc(self, chat_id: Union[str,int], path: str, caption=None, **kwargs) -> httpx.Response:
        """
        Any document file format accepted
        Max file size is 50 MB
        """
        self._type({chat_id: str, path: str})
        
        data = {'chat_id': str(chat_id), **kwargs}
        if caption: data['caption'] = caption
        if path.startswith('http'):
            data['document'] = path
            return self._post('doc', data)
        with open(path, 'rb') as f:
            return self._post('doc', data, files={'document': f})

    def send_audio(self, chat_id: Union[str,int], path: str, **kwargs) -> httpx.Response:
        """
        Audio must be in the .MP3 or .M4A format
        Max file size is 50 MB
        """
        self._type({chat_id: str, path: str})
        
        data = {'chat_id': str(chat_id), **kwargs}
        if path.startswith('http'):
            data['audio'] = path
            return self._post('audio', data)
        with open(path, 'rb') as f:
            return self._post('audio', data, files={'audio': f})

    def send_video(self, chat_id: Union[str,int], path: str, **kwargs) -> httpx.Response:
        """
        Telegram clients support MPEG4 videos (other formats may be sent as Document)
        Max file size is 50 MB
        """
        self._type({chat_id: str, path: str})
        
        data = {'chat_id': str(chat_id), **kwargs}
        if path.startswith('http'):
            data['video'] = path
            return self._post('video', data)
        with open(path, 'rb') as f:
            return self._post('video', data, files={'video': f})