from __future__ import annotations
import json,time
from pathlib import Path
import numpy as np, pandas as pd
from qiskit.quantum_info import Statevector
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC
from .preprocessing import PDaysEngineer,base_preprocessor,quantum_preprocessor
from .evaluation import metrics
from .quantum_models import circuits
from .pennylane_models import (equivalent_kernel,train_kernel_parameters,trainable_kernel,
 calibrated_precomputed_svm,train_reupload_qnn,circuit_texts)

def feature_pipe(kind,seed):
    if kind=="pca": return quantum_preprocessor(4,seed)
    return Pipeline([("pdays",PDaysEngineer()),("preprocess",base_preprocessor()),
      ("select",SelectKBest(f_classif,k=4)),("angles",MinMaxScaler((-np.pi,np.pi),clip=True))])

def equivalence_diagnostics(X,y,out):
    fm,_=circuits(); qstates=np.asarray([Statevector(fm.assign_parameters(x)).data for x in X]); Kq=np.abs(qstates@qstates.conj().T)**2
    Kp=equivalent_kernel(X); diff=np.abs(Kq-Kp); eig=np.linalg.eigvalsh((Kp+Kp.T)/2)
    cut=max(4,len(X)-5); a=np.arange(cut); b=np.arange(cut,len(X))
    mq=SVC(kernel="precomputed",C=1.0,class_weight="balanced",random_state=42).fit(Kq[np.ix_(a,a)],y[a])
    mp=SVC(kernel="precomputed",C=1.0,class_weight="balanced",random_state=42).fit(Kp[np.ix_(a,a)],y[a])
    agree=float(np.mean(mq.predict(Kq[np.ix_(b,a)])==mp.predict(Kp[np.ix_(b,a)])))
    d={"samples":len(X),"max_absolute_difference":float(diff.max()),"mean_absolute_difference":float(diff.mean()),
       "qiskit_min_eigenvalue":float(np.linalg.eigvalsh((Kq+Kq.T)/2).min()),"pennylane_min_eigenvalue":float(eig.min()),
       "pennylane_negative_eigenvalues_below_-1e-10":int(np.sum(eig < -1e-10)),"prediction_agreement":agree,
       "definition":"|<phi(x)|phi(y)>|^2; exact statevectors"}
    Path(out).write_text(json.dumps(d,indent=2),encoding="utf-8"); return d

def run_experiments(X,y,cfg):
    cv=StratifiedKFold(cfg["outer_folds"],shuffle=True,random_state=cfg["seed"]); folds=[]; oof={}; artifacts={}
    specs=[("PennyLane Fixed QSVC PCA","fixed","pca",1,.0,42),
           ("PennyLane Fixed QSVC Supervised","fixed","supervised_f_classif",1,.0,42)]
    for depth in cfg["trainable_kernel"]["depths"]:
      for lr in cfg["trainable_kernel"]["learning_rates"]:
       for s in cfg["trainable_kernel"]["initialization_seeds"]:
        specs.append((f"PennyLane Trainable Kernel d{depth} lr{lr} s{s}","trainable","pca",depth,lr,s))
    for s in cfg["data_reuploading"]["initialization_seeds"]:
        specs.append((f"PennyLane Data Reuploading QNN s{s}","qnn","pca",2,cfg["data_reuploading"]["learning_rate"],s))
    for name,kind,rep,depth,lr,init_seed in specs:
        pred=np.zeros(len(y)); raw=np.zeros(len(y)); histories=[]; elapsed=0
        for fold,(tr,va) in enumerate(cv.split(X,y)):
            prep=feature_pipe(rep,cfg["seed"]+fold); Xt=prep.fit_transform(X.iloc[tr],y[tr]); Xv=prep.transform(X.iloc[va])
            t=time.perf_counter()
            if kind=="fixed":
                Kt=equivalent_kernel(Xt); Kv=equivalent_kernel(Xv,Xt); p,_,_=calibrated_precomputed_svm(Kt,y[tr],Kv,cfg["seed"]+fold); hist=[]
            elif kind=="trainable":
                theta,hist=train_kernel_parameters(Xt,y[tr],depth,lr,cfg["trainable_kernel"]["iterations"],init_seed+fold,cfg["trainable_kernel"]["alignment_sample_cap"])
                Kt=trainable_kernel(Xt,Xt,theta,depth); Kv=trainable_kernel(Xv,Xt,theta,depth); p,_,_=calibrated_precomputed_svm(Kt,y[tr],Kv,cfg["seed"]+fold)
                artifacts.setdefault(name,[]).append({"theta":theta.tolist(),"alignment":hist})
            else:
                predict,w,hist=train_reupload_qnn(Xt,y[tr],depth,lr,cfg["data_reuploading"]["epochs"],cfg["data_reuploading"]["patience"],init_seed+fold)
                p,r=predict(Xv); raw[va]=r; artifacts.setdefault(name,[]).append({"weights":w.tolist(),"history":hist})
            elapsed+=time.perf_counter()-t; pred[va]=p; histories.append(hist)
            folds.append({"model":name,"fold":fold+1,**metrics(y[va],p),"runtime_seconds":time.perf_counter()-t,"n_train":len(tr),"n_validation":len(va)})
        oof[name]=pred; artifacts.setdefault(name,[])
        artifacts[name+"__summary"]={**metrics(y,pred),"runtime_seconds":elapsed,"representation":rep,"kind":kind}
    return pd.DataFrame(folds),oof,artifacts
