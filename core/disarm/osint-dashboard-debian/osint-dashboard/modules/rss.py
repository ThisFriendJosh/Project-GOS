import feedparser, pandas as pd
from pydantic import BaseModel

class RSSConfig(BaseModel):
    feed_url: str = "https://hnrss.org/frontpage"
    limit: int = 20

class RSSModule:
    id = "rss"
    name = "RSS Feed (Generic)"
    config_schema = RSSConfig()
    default_refresh_sec = 60

    async def fetch(self, cfg: RSSConfig):
        d = feedparser.parse(cfg.feed_url)
        rows = []
        for e in d.entries[: cfg.limit]:
            rows.append({
                "title": e.get("title"),
                "link": e.get("link"),
                "published": e.get("published"),
                "source": d.feed.get("title"),
            })
        return {
            "df": pd.DataFrame(rows),
            "source": d.feed.get("title") or "RSS",
            "url": cfg.feed_url
        }

    def render(self, st, data):
        st.subheader(f"{data['source']} • {data['url']}")
        st.dataframe(data["df"])

module = RSSModule()
