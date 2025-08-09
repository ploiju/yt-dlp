import re

from .common import InfoExtractor
from ..utils import int_or_none, urlencode_postdata


class LetMeJerkIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?letmejerk\.com/video/(?P<id>\d+)/'
    _TESTS = [{
        'url': 'https://www.letmejerk.com/video/4019918/incredible-young-babe-sucks-and-rides-huge-dick-until-it-explodes-inside-her.html',
        'info_dict': {
            'id': '4019918',
            'ext': 'mp4',
            'title': 'Incredible Young Babe Sucks And Rides Huge Dick Until It Explodes Inside Her (11:23) - LetMeJerk',
            'duration': 683,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            },
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        scripts = re.findall(r'<script[^>]*>(.*?)</script>', webpage, re.DOTALL | re.IGNORECASE)
        script_block = next((s for s in scripts if 'var a=' in s and 'eval(function' in s), webpage)

        candidates = re.findall(r'([A-Za-z0-9+/]{40,})', script_block)
        token_b64 = candidates[0] if candidates else None

        load_url = f'https://www.letmejerk.com/load/video/{token_b64}/'
        load_html = self._download_webpage(
            load_url,
            video_id,
            data=urlencode_postdata({'id': video_id}),
        )

        m3u8_url = self._search_regex(
            r'<source[^>]+src=["\']([^"\']+\.m3u8[^"\']*)',
            load_html, 'm3u8 url',
        )

        headers = {'Referer': 'https://www.letmejerk.com/'}
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False, headers=headers,
        )

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', fatal=False,
        )
        duration = int_or_none(self._og_search_property('duration', webpage, fatal=False))
        thumbnail = int_or_none(self._og_search_property('image', webpage, fatal=False))
        return {
            'id': video_id,
            'title': title or video_id,
            'thumbnail': thumbnail,
            'formats': formats,
            'duration': duration,
            'age_limit': 18,
        }
