import re

from .common import InfoExtractor
from ..utils import ExtractorError, js_to_json, parse_iso8601


class ClapDatIE(InfoExtractor):
    """
    Extractor for clapdat.com videos

    DEOBFUSCATION LOGIC EXPLANATION:

    MakeDat obfuscates video URLs to prevent direct access. The deobfuscation was
    reverse-engineered from their JavaScript code found in these files:
    - https://www.clapdat.com/_app/immutable/chunks/plyr.min.c313f9f1.js
    - https://www.clapdat.com/_app/immutable/nodes/19.23420e49.js

    Key JavaScript functions that were reverse-engineered:

    1. gt(s): Base64 character lookup function
       - Maps A-Z to 0-25, a-z to 26-51, 0-9 to 52-61, + to 62, / to 63

    2. _t(s, e): Deobfuscation and Base64 decoding
       - Removes junk data: s.slice(0, 19) + s.slice(209, s.length)
       - Cleans non-Base64 chars: s.replace(/[^A-Za-z0-9+/]/g, "")
       - Decodes Base64 manually using gt() for character mapping

    3. Ce(s, e): URL construction
       - Ce(domain, encoded_path) => `https://${domain}/${decoded_path}`
       - Called like: Ce(videoPage.file_domain, videoPage.file)

    Data structure found in page source:
    ```javascript
    const data = [{
        "type": "data",
        "data": {
            "videoPage": {
                "id": "video_id",
                "file": "base64_encoded_obfuscated_path",
                "file_domain": "s4.clapdat.com",
                "title": "Video Title",
                // ... other metadata
            }
        }
    }];
    ```

    DEBUGGING TIPS FOR FUTURE BREAKAGE:

    1. If extraction fails, check these elements in browser DevTools:
       - Look for the 'const data = [...]' variable in page source
       - Verify the videoPage object structure hasn't changed
       - Check if new obfuscation parameters are used

    2. If URL decoding fails, examine the JavaScript:
       - Search for functions like _t(), gt(), Ce() in the minified JS
       - Check if slice positions (19, 209) have changed in _t()
       - Verify Base64 character mapping in gt() is still the same

    3. If video URLs are wrong, check:
       - file_domain and file field names in videoPage
       - Domain patterns (currently s4.clapdat.com, x1.clapdat.com)
       - URL construction format in Ce() function

    4. Common breakage points:
       - Slice positions in deobfuscation: s[:19] + s[209:]
       - Base64 character mapping in _gt()
       - JavaScript variable names: 'data', 'videoPage', 'file', 'file_domain'
       - URL patterns: /video/ path structure
    """
    IE_NAME = 'clapdat'
    _VALID_URL = r'https?://(?:www\.)?clapdat\.com/video/(?P<id>[^/?#]+)'

    _TESTS = [{
        'url': 'https://www.clapdat.com/video/this-is-video-w9mvschrnp',
        'info_dict': {
            'id': 'w9mvschrnp',
            'ext': 'mp4',
            'title': 'title of video',
            'uploader': 'motr',
            'description': 'a big long description',
            'upload_date': '20201219',
        },
        'skip': 'Test video - may not exist',
    }]

    def _gt(self, char_code):
        """Base64 character lookup - converts char code to 6-bit value"""
        if 65 <= char_code <= 90:  # A-Z
            return char_code - 65
        elif 97 <= char_code <= 122:  # a-z
            return char_code - 71  # 97 - 26
        elif 48 <= char_code <= 57:  # 0-9
            return char_code + 4  # 48 + 4 = 52
        elif char_code == 43:  # +
            return 62
        elif char_code == 47:  # /
            return 63
        else:
            return 0

    def _decode_obfuscated_string(self, s, e=None):
        """Decode obfuscated Base64 string"""
        # 1. Remove obfuscation - slice out middle section (19-209)
        s = s[:19] + s[209:]

        # 2. Keep only valid Base64 characters
        r = re.sub(r'[^A-Za-z0-9+/]', '', s)

        # 3. Calculate output length
        o = len(r)
        if e:
            t = ((o * 3 + 1) >> 2) // e * e
            t = ((t + e - 1) // e) * e  # Ceiling division
        else:
            t = (o * 3 + 1) >> 2

        # 4. Create output array
        i = bytearray(t)

        # 5. Decode Base64
        d = 0
        v = 0

        for p in range(o):
            a = p & 3
            d |= self._gt(ord(r[p])) << (6 * (3 - a))

            if a == 3 or o - p == 1:
                l = 0
                while l < 3 and v < t:
                    i[v] = (d >> (16 - (l << 3))) & 255
                    l += 1
                    v += 1
                d = 0

        return i

    def _construct_video_url(self, domain, encoded_path):
        """Construct URL from domain and encoded path"""
        try:
            decoded_bytes = self._decode_obfuscated_string(encoded_path)
            # Convert bytes to string, filtering out null bytes
            path = ''.join(chr(b) for b in decoded_bytes if b != 0)
            return f'https://{domain}/{path}'
        except Exception as e:
            raise ExtractorError(f'Failed to decode video URL: {e!s}')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Download the webpage
        webpage = self._download_webpage(url, video_id)

        # Extract the data variable from JavaScript
        # Look for: const data = [...]
        data_match = self._search_regex(
            r'const\s+data\s*=\s*(\[.*?\]);',
            webpage, 'data variable', fatal=True, flags=re.DOTALL,
        )

        if not data_match:
            raise ExtractorError('Could not find data variable in page')

        # Parse the JavaScript array using js_to_json to convert JS to JSON
        try:
            # Convert JavaScript object to JSON
            json_str = js_to_json(data_match)
            data_json = self._parse_json(json_str, video_id, fatal=True)
        except Exception as e:
            raise ExtractorError(f'Failed to parse data JSON: {e!s}')

        # Find the videoPage data (should be in the second array element)
        video_page = None
        for item in data_json:
            if (isinstance(item, dict)
                and item.get('type') == 'data'
                and isinstance(item.get('data'), dict)
                    and 'videoPage' in item.get('data', {})):
                video_page = item['data']['videoPage']
                break

        if not video_page:
            raise ExtractorError('Could not find videoPage data')

        # Extract required fields
        actual_video_id = video_page.get('id')
        if not actual_video_id:
            raise ExtractorError('Could not find video ID in data')

        file_domain = video_page.get('file_domain')
        encoded_file = video_page.get('file')

        if not file_domain or not encoded_file:
            raise ExtractorError('Could not find video URL parameters')

        # Construct the actual video URL
        video_url = self._construct_video_url(file_domain, encoded_file)

        # Extract metadata
        title = video_page.get('title') or actual_video_id
        description = video_page.get('description')
        uploader = video_page.get('uploader')

        # Handle thumbnail
        thumbnail = video_page.get('image')
        if thumbnail and not thumbnail.startswith('http'):
            # If it's a relative path, construct full URL
            image_domain = video_page.get('image_domain', 'x1.clapdat.com')
            thumbnail = f'https://{image_domain}/{thumbnail}.jpg'
        elif thumbnail and not thumbnail.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            # If no extension, add .jpg
            thumbnail = f'{thumbnail}.jpg'

        # Handle upload date
        timestamp = None
        if video_page.get('date'):
            timestamp = parse_iso8601(video_page['date'])

        # Additional metadata
        uploader_id = uploader
        uploader_url = f'https://www.clapdat.com/user/{uploader}' if uploader else None

        # Duration and view count are not available in the provided data structure
        duration = None
        view_count = None

        return {
            'id': actual_video_id,
            'title': title,
            'url': video_url,
            'description': description,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'ext': 'mp4',
        }
