import httpx, pandas as pd
from pydantic import BaseModel

class NVDHiCfg(BaseModel):
    keyword: str = ""
    min_score: float = 8.0
    limit: int = 50

class NVDHigh:
    id = "nvd_high"
    name = "NVD High/Critical CVEs"
    config_schema = NVDHiCfg()
    default_refresh_sec = 600

    async def fetch(self, cfg: NVDHiCfg):
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=200"
        if cfg.keyword:
            url += f"&keywordSearch={cfg.keyword}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            j = r.json()
        rows = []
        for v in j.get("vulnerabilities", []):
            c = v["cve"]
            metrics = c.get("metrics", {})
            score = None
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV30" in metrics:
                score = metrics["cvssMetricV30"][0]["cvssData"]["baseScore"]
            elif "cvssMetricV2" in metrics:
                score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]
            if score is None or score < cfg.min_score:
                continue
            rows.append({
                "CVE": c["id"],
                "Score": score,
                "Published": c.get("published"),
                "Summary": (c.get("descriptions", [{}])[0].get("value", "") or "")[:240],
            })
            if len(rows) >= cfg.limit:
                break
        df = pd.DataFrame(rows)
        return {"df": df}

    def render(self, st, data):
        st.subheader("NVD High/Critical")
        st.dataframe(data["df"])

module = NVDHigh()
