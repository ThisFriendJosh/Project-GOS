import httpx, pandas as pd
from pydantic import BaseModel

class QuakeCfg(BaseModel):
    min_magnitude: float = 3.0
    window: str = "day"  # 'hour' | 'day' | 'week' | 'month'
    limit: int = 100

class USGSQuakes:
    id = "usgs_quakes"
    name = "USGS Earthquakes"
    config_schema = QuakeCfg()
    default_refresh_sec = 300

    async def fetch(self, cfg: QuakeCfg):
        url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{cfg.window}.geojson"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            j = r.json()
        rows = []
        for f in j.get("features", []):
            p = f.get("properties", {})
            if p.get("mag") is None:
                continue
            if p["mag"] < cfg.min_magnitude:
                continue
            rows.append({
                "Time": pd.to_datetime(p.get("time"), unit="ms", utc=True),
                "Mag": p.get("mag"),
                "Place": p.get("place"),
                "Depth_km": f.get("geometry", {}).get("coordinates", [None, None, None])[2],
                "URL": p.get("url"),
            })
            if len(rows) >= cfg.limit:
                break
        df = pd.DataFrame(rows)
        return {"df": df}

    def render(self, st, data):
        st.subheader("USGS Earthquakes")
        st.dataframe(data["df"])

module = USGSQuakes()
