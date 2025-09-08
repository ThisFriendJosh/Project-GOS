import httpx, pandas as pd, os
from pydantic import BaseModel

class ShodanCfg(BaseModel):
    query: str = "product:OpenSSH"
    facets: str = "country:10,org:10"
    api_key_env: str = "SHODAN_API_KEY"

class ShodanCounts:
    id = "shodan_counts"
    name = "Shodan Counts (facets)"
    config_schema = ShodanCfg()
    default_refresh_sec = 1800

    async def fetch(self, cfg: ShodanCfg):
        key = os.getenv(cfg.api_key_env, "")
        if not key:
            return {"df": pd.DataFrame([{"Error": "Set SHODAN_API_KEY in your environment to use this module."}])}
        url = "https://api.shodan.io/shodan/host/count"
        params = {"key": key, "query": cfg.query, "facets": cfg.facets}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            j = r.json()
        rows = []
        facets = j.get("facets", {})
        for facet_name, items in facets.items():
            for it in items:
                rows.append({
                    "Facet": facet_name,
                    "Value": it.get("value"),
                    "Count": it.get("count"),
                })
        df = pd.DataFrame(rows)
        return {"df": df}

    def render(self, st, data):
        st.subheader("Shodan Facet Counts")
        st.dataframe(data["df"])

module = ShodanCounts()
