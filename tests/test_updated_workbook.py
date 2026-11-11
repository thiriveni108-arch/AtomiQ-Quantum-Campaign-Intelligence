import pandas as pd,pytest
from src.integration import verify_updated_workbook,build_official_stage1_from_workbook,MappingVerificationError

def test_updated_workbook_resolves_ids_without_feature_changes():
    v=verify_updated_workbook(); assert v["mapping_resolved"] and v["features_unchanged"] and v["training_unchanged"]
def test_updated_cross_sheet_ids():
    p="bank_campaign_participant_release-1.xlsx"; tr=pd.read_excel(p,sheet_name="Stage1_Train"); te=pd.read_excel(p,sheet_name="Stage1_Test"); s2=pd.read_excel(p,sheet_name="Stage2_Data")
    assert len(te)==100 and te.customer_id.is_unique and not te.customer_id.isna().any()
    assert set(te.customer_id)==set(s2.customer_id)-set(tr.customer_id) and set(te.customer_id).isdisjoint(tr.customer_id)
def test_direct_official_ranking_schema_and_ties(tmp_path):
    out=tmp_path/"official.csv"; x,_=build_official_stage1_from_workbook(out=out)
    assert list(x.columns)==["customer_id","predicted_probability","rank","top10_flag"] and x.top10_flag.sum()==10 and x.customer_id.is_unique
    pairs=list(zip(x.predicted_probability,x.customer_id))
    assert pairs==sorted(pairs,key=lambda z:(-z[0],z[1]))
def test_old_workbook_remains_blocked_as_updated_source():
    with pytest.raises(MappingVerificationError): verify_updated_workbook("bank_campaign_participant_release.xlsx","bank_campaign_participant_release.xlsx")
