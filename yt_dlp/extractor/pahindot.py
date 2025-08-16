
from .common import InfoExtractor
from ..utils import ExtractorError, urljoin


class PahindotIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pahindot\.tv/watch/(?P<id>[^/]+)/?'
    _TESTS = [{
        'url': 'https://pahindot.tv/watch/some-title-sentence/',
        'info_dict': {
            'id': 'some-title-sentence',
            'ext': 'mp4',
            'title': 'some-title-sentence',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Extract title from page
        title = (
            self._html_search_regex(r'<title>([^<]+)</title>', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or video_id
        )

        # Find iframe with same domain (pahindot.tv)
        iframe_src = self._html_search_regex(
            r'<iframe[^>]+src=["\']([^"\']*pahindot\.tv[^"\']*)["\']',
            webpage, 'iframe src')

        iframe_url = urljoin(url, iframe_src)

        # Download iframe content with proper headers
        headers = {
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        iframe_webpage = self._download_webpage(iframe_url, video_id, note='Downloading iframe content', headers=headers)

        # Extract video source from iframe content
        # Look for various video source patterns
        video_url = (
            self._html_search_regex(
                r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']',
                iframe_webpage, 'source src', default=None)
            or self._html_search_regex(
                r'<video[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']',
                iframe_webpage, 'video src', default=None)
            or self._html_search_regex(
                r'src:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                iframe_webpage, 'js video src', default=None)
        )

        if not video_url:
            raise ExtractorError('No video source found in iframe')

        # Make video URL absolute
        video_url = urljoin(iframe_url, video_url)

        return {
            'id': video_id,
            'title': title,
            'formats': [{
                'url': video_url,
                'ext': 'mp4',
                'http_headers': {
                    'Referer': url,
                },
            }],
        }
