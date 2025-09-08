# Minimal simulation stub; replace with real loop.
def predict_policy_impact(campaign_id, s_amp=None, s_share=None, dsn=None):
    base = 1000
    amp = s_amp if s_amp is not None else 1.0
    shr = s_share if s_share is not None else 1.0
    return {
        "baseline_reach": base,
        "projected_reach": int(base*amp*(1+0.5*shr)),
        "eta": {"amplify": amp, "share": shr}
    }

