from __future__ import annotations
import time, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.metrics import (average_precision_score, roc_auc_score, brier_score_loss, log_loss,
 accuracy_score, f1_score, precision_recall_curve, confusion_matrix, ConfusionMatrixDisplay)
from sklearn.model_selection import StratifiedKFold
from sklearn.calibration import calibration_curve
from .preprocessing import quantum_preprocessor
from .quantum_models import qsvc, vqc

def metrics(y,p):
    p=np.clip(np.asarray(p,float),1e-7,1-1e-7); pred=(p>=.5).astype(int)
    top=np.argsort(-p,kind="stable")[:10]
    return {"pr_auc":average_precision_score(y,p),"roc_auc":roc_auc_score(y,p),
      "precision_at_10":float(np.mean(np.asarray(y)[top])),"recall_at_10":float(np.sum(np.asarray(y)[top])/np.sum(y)),
      "brier":brier_score_loss(y,p),"log_loss":log_loss(y,p,labels=[0,1]),
      "accuracy":accuracy_score(y,pred),"f1":f1_score(y,pred,zero_division=0)}

def evaluate_classical(X,y,models,seed=42):
    cv=StratifiedKFold(3,shuffle=True,random_state=seed); rows=[]; oof={}
    for name,est in models.items():
        p=np.zeros(len(y)); fit_t=pred_t=0
        for tr,va in cv.split(X,y):
            e=clone(est); t=time.perf_counter(); e.fit(X.iloc[tr],y[tr]); fit_t+=time.perf_counter()-t
            t=time.perf_counter(); p[va]=e.predict_proba(X.iloc[va])[:,1]; pred_t+=time.perf_counter()-t
        row={"model":name,**metrics(y,p),"train_seconds":fit_t,"inference_seconds":pred_t,"executed":True}
        rows.append(row); oof[name]=p
    return rows,oof

def evaluate_quantum(X,y,maxiter=30,seed=42,reps=1):
    cv=StratifiedKFold(3,shuffle=True,random_state=seed); rows=[]; oof={}; losses={}
    vqc_parameters=[]
    for name in ("QSVC","VQC"):
        p=np.zeros(len(y)); fit_t=pred_t=0; all_loss=[]
        for fold,(tr,va) in enumerate(cv.split(X,y)):
            prep=quantum_preprocessor(4,seed+fold); Xt=prep.fit_transform(X.iloc[tr],y[tr]); Xv=prep.transform(X.iloc[va])
            if name=="QSVC": model,_=qsvc(reps)
            else:
                history=[]
                model=vqc(maxiter,reps,seed+fold,lambda w,l: history.append(float(l)))
            t=time.perf_counter(); model.fit(Xt,y[tr]); fit_t+=time.perf_counter()-t
            t=time.perf_counter(); p[va]=model.predict_proba(Xv)[:,1]; pred_t+=time.perf_counter()-t
            if name=="VQC":
                all_loss.append(history)
                vqc_parameters.append(np.asarray(model.weights).tolist())
        rows.append({"model":name,**metrics(y,p),"train_seconds":fit_t,"inference_seconds":pred_t,"executed":True})
        oof[name]=p; losses[name]=all_loss
    losses["VQC_parameters_by_fold"] = vqc_parameters
    return rows,oof,losses

def make_plots(y,oof,out="reports/figures"):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots()
    for n,p in oof.items():
        pr,re,_=precision_recall_curve(y,p); ax.plot(re,pr,label=n)
    ax.axhline(np.mean(y),ls="--",color="gray"); ax.set(xlabel="Recall",ylabel="Precision",title="Out-of-fold precision-recall"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(out/"precision_recall.png",dpi=160); plt.close(fig)
    fig,ax=plt.subplots()
    for n,p in oof.items():
        frac,mean=calibration_curve(y,p,n_bins=5,strategy="quantile"); ax.plot(mean,frac,"o-",label=n)
    ax.plot([0,1],[0,1],"k--"); ax.set(xlabel="Mean predicted probability",ylabel="Observed fraction",title="Reliability (OOF, 5 quantile bins)"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(out/"calibration.png",dpi=160); plt.close(fig)
    summary=pd.DataFrame([{"model":n,**metrics(y,p)} for n,p in oof.items()])
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    axes[0].bar(summary.model,summary.pr_auc); axes[0].axhline(np.mean(y),ls="--",color="gray"); axes[0].set_title("PR-AUC (prevalence dashed)")
    axes[1].bar(summary.model,summary.brier); axes[1].set_title("Brier score (lower is better)")
    for ax in axes: ax.tick_params(axis="x",rotation=35)
    fig.tight_layout(); fig.savefig(out/"model_comparison.png",dpi=160); plt.close(fig)
    for n,p in oof.items():
        fig,ax=plt.subplots(); ConfusionMatrixDisplay(confusion_matrix(y,np.asarray(p)>=.5)).plot(ax=ax,colorbar=False); ax.set_title(n)
        fig.tight_layout(); fig.savefig(out/f"confusion_{n.lower().replace(' ','_')}.png",dpi=140); plt.close(fig)
