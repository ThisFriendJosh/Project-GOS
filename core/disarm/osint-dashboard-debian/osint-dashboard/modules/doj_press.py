import feedparser, pandas as pd
from pydantic import BaseModel

class DOJCfg(BaseModel):
    feed_url: str = "https://www.justice.gov/opa/press-releases/rss.xml"
    limit: int = 30

class DOJPress:
    id = "doj_press"
    name = "DOJ Press Releases (RSS)"
    config_schema = DOJCfg()
    default_refresh_sec = 900

    async def fetch(self, cfg: DOJCfg):
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
        st.subheader("DOJ Press Releases")
        st.dataframe(data["df"])

module = DOJPress()
