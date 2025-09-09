import feedparser, pandas as pd
from pydantic import BaseModel

class CISAAlertCfg(BaseModel):
    feed_url: str = "https://www.cisa.gov/news-events/cybersecurity-advisories/alerts/all.xml"
    limit: int = 30

class CISAAlertsRSS:
    id = "cisa_alerts_rss"
    name = "CISA Alerts (RSS)"
    config_schema = CISAAlertCfg()
    default_refresh_sec = 900

    async def fetch(self, cfg: CISAAlertCfg):
        d = feedparser.parse(cfg.feed_url)
        rows = []
        for e in d.entries[: cfg.limit]:
            rows.append({
                "Title": e.get("title"),
                "Published": e.get("published"),
                "Link": e.get("link"),
                "Summary": (e.get("summary") or "")[:240],
            })
        return {"df": pd.DataFrame(rows)}

    def render(self, st, data):
        st.subheader("CISA Alerts (RSS)")
        st.dataframe(data["df"])

module = CISAAlertsRSS()
