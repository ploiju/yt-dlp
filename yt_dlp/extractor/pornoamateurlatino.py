
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    update_url,
    url_or_none,
)


class PornoAmateurLatinoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornoamateurlatino\.net/(?:\d{4}/\d{2}/)?(?P<id>[^/?#]+)\.html'
    _TESTS = [{
        'url': 'https://pornoamateurlatino.net/2025/02/tetona-tatuada-en-tanga-roja-montando-verga-en-el-sofa.html',
        'info_dict': {
            'id': 'tetona-tatuada-en-tanga-roja-montando-verga-en-el-sofa',
            'ext': 'mp4',
            'title': 'Beautiful busty Argentina Eats a Foreign Cock Without a Condom for an Extra in Buenos Aires',
        },

    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._extract_video_url(webpage)
        if not video_url:
            raise ExtractorError('Unable to extract video URL', expected=True)

        title = self._html_extract_title(webpage) or video_id.replace('-', ' ').title()

        return self.url_result(video_url, ie_key=None, video_id=video_id, video_title=title)

    def _extract_video_url(self, webpage):
        js_object_str = self._search_regex(
            r'vidorev_jav_js_object\s*=\s*({.*?});',
            webpage,
            'video object',
            default=None,
        )

        if not js_object_str:
            return None

        try:
            js_object = self._parse_json(js_object_str, None, fatal=False)
            if js_object:
                iframe_html = js_object.get('single_video_url', '')
                if iframe_html:
                    iframe_attrs = extract_attributes(iframe_html)
                    video_url = iframe_attrs.get('src')
                    if video_url:
                        return update_url(video_url, scheme='https')
        except Exception:
            pass

        video_url = self._search_regex(
            r'"single_video_url":\s*"[^"]*src=\\"([^"\\]+)\\"',
            webpage,
            'video url fallback',
            default=None,
        )

        if video_url:
            video_url = video_url.replace('.com', '.org')
            return url_or_none(video_url)

        return None
