import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from src.preprocessing import FEATURES, classical_pipeline, PDaysEngineer
from src.evaluation import metrics

def fixture(n=30):
    rng=np.random.default_rng(42)
    d=pd.DataFrame({"age":rng.integers(18,70,n),"job":["admin."]*n,"marital":["single"]*n,"education":["unknown"]*n,
      "default":["no"]*n,"balance":rng.normal(100,100,n),"housing":["yes"]*n,"loan":["no"]*n,"contact":["cellular"]*n,
      "day":rng.integers(1,29,n),"month":["may"]*n,"campaign":rng.integers(1,5,n),"pdays":np.where(np.arange(n)%2,-1,20),
      "previous":rng.integers(0,3,n),"poutcome":["unknown"]*n})
    y=np.array([0,1]*(n//2)); return d,y

def test_class_encoding_and_probability_range():
    assert pd.Series(["yes","no"]).map({"yes":1,"no":0}).tolist()==[1,0]
    X,y=fixture(); m=classical_pipeline(LogisticRegression()).fit(X,y); p=m.predict_proba(X)[:,1]
    assert len(p)==len(X) and np.all((p>=0)&(p<=1))
def test_pdays_semantics():
    X,_=fixture(); z=PDaysEngineer().fit_transform(X); assert ((z.pdays_never==1)==(X.pdays==-1)).all() and (z.pdays>=0).all()
def test_ranking_metrics_top_10():
    y=np.array([1]*5+[0]*15); p=np.linspace(1,0,20); m=metrics(y,p); assert m["precision_at_10"]==.5 and m["recall_at_10"]==1
def test_feature_schema_excludes_id_and_target():
    assert "customer_id" not in FEATURES and "y" not in FEATURES and len(FEATURES)==15
