from .common import InfoExtractor
from ..utils import get_domain


class RoadSexeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?roadsexe\.com/video/(?P<display_id>[\w-]+)-(?P<id>\d+)\.html'
    _TESTS = [
        {
            'url': 'https://www.roadsexe.com/video/making-a-new-cup-11072.html',
            'info_dict': {
                'id': '11072',
                'display_id': 'making-a-new-cup',
                'ext': 'mp4',
                'title': 'Making A New Cup',
            },
            'skip': 'Test example only',
        },
    ]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)

        # Extract title from the page
        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_meta('title', webpage, 'title', default=None)
            or self._html_extract_title(webpage, default=None)
            or display_id.replace('-', ' ').title()
        )

        # Extract description
        description = (
            self._og_search_description(webpage, default=None)
            or self._html_search_meta('description', webpage, 'description', default=None)
        )

        # Extract thumbnail
        thumbnail = (
            self._og_search_thumbnail(webpage, default=None)
            or self._html_search_meta('thumbnail', webpage, 'thumbnail', default=None)
        )

        # Parse the domain to construct the video player URL pattern
        domain = get_domain(url)
        base_domain = domain
        if base_domain.startswith('www.'):
            base_domain = base_domain[4:]

        # Look for iframe with video.domain.com pattern
        iframe_pattern = r'<iframe[^>]+src=["\']([^"\']*video\.' + base_domain.replace('.', r'\.') + r'[^"\']*)["\']'
        player_url = self._html_search_regex(
            iframe_pattern, webpage, 'player iframe URL', default=None)

        if player_url:
            # Ensure the URL is absolute
            if player_url.startswith('//'):
                player_url = 'https:' + player_url
            elif player_url.startswith('/'):
                player_url = f'https://{domain}' + player_url
        else:
            # Fallback: try to extract MPD directly from the page
            player_url = url

        # Extract MPD URL from the player page
        mpd_url = self._extract_mpd_url(player_url, display_id)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': self._extract_mpd_formats(mpd_url, video_id),
        }

    def _extract_mpd_url(self, player_url, display_id):
        """Extract MPD URL from the player page"""
        player_webpage = self._download_webpage(player_url, display_id, note='Downloading player page')

        # Look for the specific JSON pattern with the src array containing MPD URL
        mpd_pattern = r'"src":\s*\[\s*{\s*"src":\s*"([^"]+\.mpd)"'
        escaped_url = self._search_regex(
            mpd_pattern, player_webpage, 'MPD URL',
            group=1, fatal=True)

        return escaped_url.replace('\\/', '/')
