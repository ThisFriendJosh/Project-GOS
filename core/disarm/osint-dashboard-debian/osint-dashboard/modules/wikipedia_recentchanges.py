import httpx, pandas as pd
from pydantic import BaseModel

API = "https://en.wikipedia.org/w/api.php"

class WikiCfg(BaseModel):
    query: str = ""   # filter by title or comment substring
    limit: int = 50

class WikiRecent:
    id = "wikipedia_recent"
    name = "Wikipedia Recent Changes"
    config_schema = WikiCfg()
    default_refresh_sec = 60

    async def fetch(self, cfg: WikiCfg):
        params = {
            "action": "query",
            "list": "recentchanges",
            "rcprop": "title|ids|sizes|flags|user|timestamp|comment",
            "rclimit": min(cfg.limit, 100),
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "OSINT-Dashboard/1.0"}) as client:
            r = await client.get(API, params=params)
            r.raise_for_status()
            j = r.json()
        rows = []
        for rc in j.get("query", {}).get("recentchanges", []):
            title = rc.get("title", "")
            comment = rc.get("comment", "") or ""
            if cfg.query and (cfg.query.lower() not in title.lower() and cfg.query.lower() not in comment.lower()):
                continue
            rows.append({
                "Time": rc.get("timestamp"),
                "Title": title,
                "User": rc.get("user"),
                "Comment": comment[:180],
                "NewLen": rc.get("newlen"),
                "OldLen": rc.get("oldlen"),
                "DiffURL": f"https://en.wikipedia.org/?diff={rc.get('revid')}"
            })
        df = pd.DataFrame(rows)
        return {"df": df}

    def render(self, st, data):
        st.subheader("Wikipedia Recent Changes")
        st.dataframe(data["df"])

module = WikiRecent()
