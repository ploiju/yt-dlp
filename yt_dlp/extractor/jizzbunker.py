from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    url_or_none,
)


class JizzbunkerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jizzbunker\.com/(?:es/)?(?P<id>\d+)/[^/?#]*\.html'
    _TESTS = [{
        'url': 'https://jizzbunker.com/es/489101/mujer-japonesa-vaquera.html',
        'info_dict': {
            'id': '489101',
            'ext': 'mp4',
            'title': 'Mujer japonesa vaquera película del sitio de videos JizzBunker.com',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._extract_video_url(webpage)
        if not video_url:
            raise ExtractorError('Unable to extract video URL', expected=True)

        title = self._html_extract_title(webpage) or video_id

        # Check if the URL has a proper extension, if not assume mp4
        ext = determine_ext(video_url)
        if ext in ('480', '720', '1080') or not ext:
            # If extension is a quality indicator or missing, assume mp4
            return {
                'id': video_id,
                'url': video_url,
                'title': title,
                'ext': 'mp4',
            }
        else:
            return self.url_result(video_url, ie_key=None, video_id=video_id, video_title=title)

    def _extract_video_url(self, webpage):
        video_url = self._search_regex(
            r"sources\.push\(\{[^}]*src:\s*['\"]([^'\"]+)['\"][^}]*\}\)",
            webpage,
            'video url',
            default=None,
        )

        return url_or_none(video_url)
