import httpx, pandas as pd
from pydantic import BaseModel

SWPC_URL = "https://services.swpc.noaa.gov/products/alerts.json"

class SWPCCfg(BaseModel):
    event_filter: str = ""   # e.g., "Geomagnetic", "Radio", ""
    limit: int = 50

class SWPCAlerts:
    id = "swpc_alerts"
    name = "NOAA SWPC Alerts"
    config_schema = SWPCCfg()
    default_refresh_sec = 600

    async def fetch(self, cfg: SWPCCfg):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(SWPC_URL)
        r.raise_for_status()
        j = r.json()
        # First row is header
        header = j[0]
        rows = []
        for row in j[1:]:
            rec = dict(zip(header, row))
            if cfg.event_filter and cfg.event_filter.lower() not in (rec.get("message", "") or "").lower():
                continue
            rows.append({
                "IssueTime": rec.get("issue_datetime"),
                "Message": rec.get("message"),
                "Serial": rec.get("serial_number"),
                "Type": rec.get("product_type"),
            })
            if len(rows) >= cfg.limit:
                break
        df = pd.DataFrame(rows)
        return {"df": df}

    def render(self, st, data):
        st.subheader("Space Weather Alerts (SWPC)")
        st.dataframe(data["df"])

module = SWPCAlerts()
