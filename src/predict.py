from pathlib import Path
import joblib, numpy as np, pandas as pd

def save_predictions(model, X_test, out="results/stage1_predictions_provisional.csv", artifact="artifacts/stage1_final_model.joblib"):
    p=np.clip(model.predict_proba(X_test)[:,1],0,1)
    df=pd.DataFrame({"test_row_index":np.arange(len(X_test)),"predicted_probability":p})
    df=df.sort_values(["predicted_probability","test_row_index"],ascending=[False,True],kind="stable").reset_index(drop=True)
    df.insert(0,"rank",np.arange(1,len(df)+1)); df["top_10"]=df["rank"]<=10; df["status"]="PROVISIONAL_MISSING_CUSTOMER_ID"
    Path(out).parent.mkdir(parents=True,exist_ok=True); df.to_csv(out,index=False)
    Path(artifact).parent.mkdir(parents=True,exist_ok=True); joblib.dump(model,artifact)
    return df
