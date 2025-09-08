import httpx, pandas as pd
from pydantic import BaseModel

class NVDConfig(BaseModel):
    keyword: str = ""
    limit: int = 30

class NVDModule:
    id = "nvd_cve"
    name = "NVD CVEs (Latest)"
    config_schema = NVDConfig()
    default_refresh_sec = 180

    async def fetch(self, cfg: NVDConfig):
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=200"
        if cfg.keyword:
            url += f"&keywordSearch={cfg.keyword}"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url)
            r.raise_for_status()
            j = r.json()
        items = []
        for v in j.get("vulnerabilities", [])[: cfg.limit]:
            c = v["cve"]
            metrics = c.get("metrics", {})
            score = None
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV30" in metrics:
                score = metrics["cvssMetricV30"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV2" in metrics:
                score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]
            items.append({
                "CVE": c["id"],
                "Published": c.get("published"),
                "BaseScore": score,
                "Summary": (c.get("descriptions", [{}])[0].get("value", "") or "")[:240],
            })
        df = pd.DataFrame(items)
        return {"df": df}

    def render(self, st, data):
        st.subheader("Latest CVEs (NVD)")
        st.dataframe(data["df"])
        if not data["df"].empty:
            st.caption("Tip: Use the sidebar ‘keyword’ to filter by vendor/product.")

module = NVDModule()
