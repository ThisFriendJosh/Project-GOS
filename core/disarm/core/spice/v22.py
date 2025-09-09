from datetime import datetime

def build_spice_report_v22(scope: str, scope_id: str, window, dsn: str=None):
    # TODO: implement full SP!CE v2.2 scoring
    return {
        "report_id": f"sprt_{scope}_{scope_id}_{int(datetime.utcnow().timestamp())}",
        "version":"2.2","scope":scope,"scope_id":scope_id,
        "scores":{},"top_ttps":[],"paths":{},"blue_coas":[],
        "generated_at": datetime.utcnow().isoformat()
    }