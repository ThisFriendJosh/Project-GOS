import httpx, pandas as pd
from pydantic import BaseModel

ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"

class HNCfg(BaseModel):
    query: str = "security"  # default focus
    limit: int = 50

class HackerNewsRecent:
    id = "hn_recent"
    name = "Hacker News (recent by query)"
    config_schema = HNCfg()
    default_refresh_sec = 120

    async def fetch(self, cfg: HNCfg):
        params = {"tags": "story", "query": cfg.query, "hitsPerPage": min(cfg.limit, 100)}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(ALGOLIA, params=params)
            r.raise_for_status()
            j = r.json()
        rows = []
        for h in j.get("hits", []):
            rows.append({
                "Time": h.get("created_at"),
                "Title": h.get("title"),
                "Points": h.get("points"),
                "Author": h.get("author"),
                "URL": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            })
        df = pd.DataFrame(rows[: cfg.limit])
        return {"df": df}

    def render(self, st, data):
        st.subheader("Hacker News (query feed)")
        st.dataframe(data["df"])

module = HackerNewsRecent()
