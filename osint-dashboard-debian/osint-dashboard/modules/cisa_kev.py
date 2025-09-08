import httpx, pandas as pd
from pydantic import BaseModel

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

class KEVCfg(BaseModel):
    vendor: str = ""     # filter by vendor substring
    product: str = ""    # filter by product substring
    limit: int = 50

class CISAKEV:
    id = "cisa_kev"
    name = "CISA KEV Catalog"
    config_schema = KEVCfg()
    default_refresh_sec = 3600

    async def fetch(self, cfg: KEVCfg):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(CISA_KEV_URL)
            r.raise_for_status()
            j = r.json()
        vulns = j.get("vulnerabilities", [])
        rows = []
        for v in vulns:
            if cfg.vendor and cfg.vendor.lower() not in (v.get("vendorProject","") or "").lower():
                continue
            if cfg.product and cfg.product.lower() not in (v.get("product","") or "").lower():
                continue
            rows.append({
                "CVE": v.get("cveID"),
                "Vendor": v.get("vendorProject"),
                "Product": v.get("product"),
                "VulnerabilityName": v.get("vulnerabilityName"),
                "DateAdded": v.get("dateAdded"),
                "DueDate": v.get("dueDate"),
                "KnownRansomwareCampaignUse": v.get("knownRansomwareCampaignUse"),
                "Notes": v.get("shortDescription"),
            })
            if len(rows) >= cfg.limit:
                break
        df = pd.DataFrame(rows)
        return {"df": df, "count": len(df)}

    def render(self, st, data):
        st.subheader(f"CISA KEV (top {len(data['df'])})")
        st.dataframe(data["df"])

module = CISAKEV()
