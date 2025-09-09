import httpx, pandas as pd, os
from pydantic import BaseModel

class OTXCfg(BaseModel):
    query: str = "ransomware"
    limit: int = 25
    api_key_env: str = "OTX_API_KEY"

class OTXPulses:
    id = "otx_pulses"
    name = "AlienVault OTX Pulses"
    config_schema = OTXCfg()
    default_refresh_sec = 900

    async def fetch(self, cfg: OTXCfg):
        api_key = os.getenv(cfg.api_key_env, "")
        headers = {"X-OTX-API-KEY": api_key} if api_key else {}
        params = {"q": cfg.query, "limit": min(cfg.limit, 50)}
        url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            r = await client.get(url, params=params)
            if r.status_code == 401:
                return {"df": pd.DataFrame([{"Error": "Set OTX_API_KEY in your environment to use this module."}])}
            r.raise_for_status()
            j = r.json()
        rows = []
        for p in j.get("results", [])[: cfg.limit]:
            rows.append({
                "Name": p.get("name"),
                "Author": p.get("author_name"),
                "Created": p.get("created"),
                "References": ", ".join(p.get("references", [])[:3]),
                "Tags": ", ".join(p.get("tags", [])[:6]),
                "Link": f"https://otx.alienvault.com/pulse/{p.get('id')}",
            })
        df = pd.DataFrame(rows)
        return {"df": df}

    def render(self, st, data):
        st.subheader("OTX Pulses")
        st.dataframe(data["df"])

module = OTXPulses()
