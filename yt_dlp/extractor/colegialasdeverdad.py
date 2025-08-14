
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
)


class ColegialasdeVerdadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?colegialasdeverdad\.com/(?P<id>[^/?#&]+)/?'
    _TESTS = [
        {
            'url': 'https://colegialasdeverdad.com/esta-morrita-de-guadalajara-la-pasa-demasiado-bien-sobre-mi-verga/',
            'info_dict': {
                'id': 'esta-morrita-de-guadalajara-la-pasa-demasiado-bien-sobre-mi-verga',
                'url': 'https://cdn.colegialasdeverdad.vip/videos/MXJzTVQvcHV0Y20xNmwzU1ZBekdGUT09.mp4',
                'ext': 'mp4',
                'title': 'Esta morrita de Guadalajara la pasa demasiado bien sobre mi verga',
                'description': '😉 No te pierdas de este video porno de colegialas xxx al que titulamos: "Esta morrita de Guadalajara la pasa demasiado bien sobre mi verga". Esta morrita',
                'duration': 583,
                'thumbnail': 'https://cdn.colegialasdeverdad.vip/media/img/mxjztvqvchv0y20xnmwzu1zbekdgut09.webp',
                'age_limit': 18,
            },
            # 'skip': 'Test example only',
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Temporary thumbnail hack to extract video URL
        thumbnail = self._html_search_regex(
            r'class="blackPlayer"[^>]*style="[^"]*background-image:\s*url\(([^)]+)\)',
            webpage, 'thumbnail', default=None,
        )

        if not thumbnail:
            raise ExtractorError('Video URL not found', expected=True)

        video_url = thumbnail.replace('/thumbnails/', '/videos/').replace('.jpg', '.mp4')

        # Extract title from meta name (itemprop="name")
        title = self._html_search_meta('name', webpage, 'title', default=None)

        # Fallback to other title sources if meta name is empty
        if not title or title.strip() == '':
            title = (
                self._og_search_title(webpage, default=None)
                or self._html_extract_title(webpage, default=None)
                or video_id
            )

        thumbnail = self._html_search_meta('thumbnailUrl', webpage, 'thumbnail', default=None)

        duration_str = self._html_search_meta('duration', webpage, 'duration', default=None)
        duration = None
        if duration_str:
            duration = parse_duration(duration_str)

        description = self._og_search_description(webpage, default=None)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'ext': 'mp4',
        }
