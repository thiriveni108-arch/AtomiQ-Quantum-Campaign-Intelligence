import pytest
from src.simulation.stage3_pipeline import SubscriptionRecord,validate_records,load_demo,load_official,OfficialStage3Blocked

def test_demo_matches_stage2_selection(): assert [r.customer_id for r in load_demo()]==["DEMO01","DEMO02","DEMO03","DEMO04","DEMO05","DEMO09"]
def test_wrong_count_and_duplicates():
    with pytest.raises(ValueError): validate_records([SubscriptionRecord("A",.5)]*5)
    with pytest.raises(ValueError,match="Duplicate"): validate_records([SubscriptionRecord("A",.5)]*6)
def test_invalid_record_probability():
    with pytest.raises(ValueError): validate_records([SubscriptionRecord(str(i),2 if i==0 else .5) for i in range(6)])
def test_official_blocked():
    with pytest.raises(OfficialStage3Blocked): load_official("results/does_not_exist_stage2_selection.json")
