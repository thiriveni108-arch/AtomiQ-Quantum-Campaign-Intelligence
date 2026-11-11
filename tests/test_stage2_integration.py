import pytest
from src.optimization.stage2_pipeline import load_demo,load_official,OfficialIntegrationBlocked
def test_demo_schema(): assert len(load_demo()[0])==10
def test_official_mode_is_blocked_without_ids():
    with pytest.raises(OfficialIntegrationBlocked,match="no verified customer_id"): load_official("results/does_not_exist_official.csv")
