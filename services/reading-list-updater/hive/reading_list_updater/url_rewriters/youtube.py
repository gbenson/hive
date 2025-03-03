from collections import defaultdict
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def maybe_rewrite_youtube_url(url: str) -> Optional[str]:
    scheme, netloc, path, params, query, fragment = urlparse(url)
    if params or fragment:
        return None
    if scheme != "https":
        if scheme != "http":
            return None
        scheme = "https"

    is_short = False
    is_youtu_be = (netloc == "youtu.be")
    if not is_youtu_be:
        is_short = path.startswith("/shorts/")
        if not is_short and path != "/watch":
            return None
        if netloc != "www.youtube.com":
            if netloc != "youtube.com":
                return None
            netloc = "www.youtube.com"

    query = defaultdict(list, parse_qs(query))
    if is_youtu_be:
        video = path.removeprefix("/")
        if not video:
            return None
        netloc = "www.youtube.com"
        path = "/watch"
        query["v"].append(video)
        del video

    if is_short:
        video = path.removeprefix("/shorts/")
        if not video:
            return None
        path = "/watch"
        query["v"].append(video)
        del video

    query = dict((k, v) for k, v in query.items() if k in "vt")
    if any(len(v) != 1 for v in query.values()):
        return None
    if "v" not in query:
        return None
    query = urlencode(dict(reversed(query.items())), doseq=True)

    return urlunparse((scheme, netloc, path, params, query, fragment))
