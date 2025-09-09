import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sim.tickloop import predict_policy_impact


def test_predict_policy_impact_constant():
    res = predict_policy_impact("camp", s_amp=1, s_share=1, network=0, decay=0, ticks=3)
    assert res["trajectory"] == [1000, 1000, 1000, 1000]
    assert res["projected_reach"] == 1000


def test_predict_policy_impact_growth_decay():
    res = predict_policy_impact("camp", s_amp=1, s_share=1, network=0.2, decay=0.1, ticks=3)
    assert res["trajectory"] == [1000, 1080, 1166, 1259]
    assert res["projected_reach"] == 1259
