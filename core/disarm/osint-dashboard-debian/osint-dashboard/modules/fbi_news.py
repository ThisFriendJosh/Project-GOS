import feedparser, pandas as pd
from pydantic import BaseModel

class FBICfg(BaseModel):
    feed_url: str = "https://www.fbi.gov/feeds/fbi-in-the-news/atom.xml"
    limit: int = 30

class FBINews:
    id = "fbi_news"
    name = "FBI News (RSS)"
    config_schema = FBICfg()
    default_refresh_sec = 900

    async def fetch(self, cfg: FBICfg):
        d = feedparser.parse(cfg.feed_url)
        rows = []
        for e in d.entries[: cfg.limit]:
            rows.append({
                "Title": e.get("title"),
                "Published": e.get("published"),
                "Link": e.get("link"),
                "Summary": (e.get("summary") or "")[:200],
            })
        return {"df": pd.DataFrame(rows)}

    def render(self, st, data):
        st.subheader("FBI News")
        st.dataframe(data["df"])

module = FBINews()
