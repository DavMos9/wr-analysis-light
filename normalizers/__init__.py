from normalizers.registry import normalize, normalize_all, register, registered_sources, REGISTRY

# Import dei normalizer source-specific: registrano se stessi via register() a livello di modulo.
from normalizers import (
    ansa, bbc, bluesky, brave, gdelt, gnews_it, guardian,
    hackernews, lemmy, mastodon, news, nyt, reddit,
    stackexchange, wikipedia, wikitalk, youtube, youtube_comments,
)

__all__ = ["normalize", "normalize_all", "register", "registered_sources", "REGISTRY"]
