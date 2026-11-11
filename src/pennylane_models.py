from __future__ import annotations
import time
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.svm import SVC
from .preprocessing import quantum_preprocessor

N_QUBITS = 4

_fixed_ry_dev = qml.device("lightning.qubit", wires=N_QUBITS)

@qml.qnode(_fixed_ry_dev)
def fixed_ry_cnot_state(x):
    """Selected depth-1 map: H, data RY, zero fixed rotations, linear CNOT."""
    theta = np.zeros((1, N_QUBITS, 2))
    trainable_embedding(x, theta, depth=1)
    return qml.state()

def fixed_ry_cnot_kernel(X, Y=None):
    """Fidelity kernel used by the selected depth-1 PennyLane experiment."""
    Y = X if Y is None else Y
    sx = np.asarray([fixed_ry_cnot_state(x) for x in np.asarray(X)])
    sy = sx if Y is X else np.asarray([fixed_ry_cnot_state(y) for y in np.asarray(Y)])
    return np.abs(sx @ sy.conj().T) ** 2

class FixedRYCNOTKernelClassifier:
    """Leakage-free PCA angles, fixed depth-1 fidelity SVM, and Platt calibration."""
    def __init__(self, seed=42, C=1.0):
        self.seed = seed
        self.C = C

    def fit(self, X, y):
        self.preprocessor_ = quantum_preprocessor(N_QUBITS, self.seed)
        self.X_train_ = self.preprocessor_.fit_transform(X, y)
        K = fixed_ry_cnot_kernel(self.X_train_)
        _, self.svm_, self.calibrator_ = calibrated_precomputed_svm(K, np.asarray(y), K, self.seed, self.C)
        self.model_metadata_ = {
            "name": "PennyLane fixed depth-1 RY/CNOT fidelity kernel",
            "framework": "PennyLane",
            "qubits": N_QUBITS,
            "depth": 1,
            "feature_map": "H on each qubit; RY(x_i); fixed RZ(0), RY(0); linear CNOT chain",
            "kernel": "squared state fidelity",
            "preprocessing": "PDaysEngineer + imputation/encoding/robust scaling + PCA(4) + MinMax[-pi,pi]",
            "calibration": "training-only 25% stratified holdout Platt logistic calibration; final SVC refit on all 300 rows",
            "seed": self.seed,
            "C": self.C,
            "training_rows": int(len(y)),
            "exploratory_metrics": {"pr_auc": 0.23287783944077428, "roc_auc": 0.6768733153638815,
                "precision_at_10": 0.3, "brier": 0.10066108748201394, "log_loss": 0.3488186807830046},
        }
        return self

    def predict_proba(self, X):
        Z = self.preprocessor_.transform(X)
        K = fixed_ry_cnot_kernel(Z, self.X_train_)
        score = self.svm_.decision_function(K).reshape(-1, 1)
        p = self.calibrator_.predict_proba(score)[:, 1]
        return np.column_stack([1.0 - p, p])

def qiskit_equivalent_embedding(x):
    """Exact reps=1 Qiskit zz_feature_map(linear): H, P(2x), CX-P(phi)-CX."""
    for w in range(N_QUBITS):
        qml.Hadamard(wires=w)
        qml.PhaseShift(2.0 * x[w], wires=w)
    for w in range(N_QUBITS - 1):
        qml.CNOT(wires=[w, w + 1])
        qml.PhaseShift(2.0 * (np.pi - x[w]) * (np.pi - x[w + 1]), wires=w + 1)
        qml.CNOT(wires=[w, w + 1])

_dev = qml.device("lightning.qubit", wires=N_QUBITS)
@qml.qnode(_dev)
def equivalent_state(x):
    qiskit_equivalent_embedding(x)
    return qml.state()

def equivalent_kernel(X, Y=None):
    Y = X if Y is None else Y
    sx=np.asarray([equivalent_state(x) for x in np.asarray(X)])
    sy=sx if Y is X else np.asarray([equivalent_state(y) for y in np.asarray(Y)])
    return np.abs(sx @ sy.conj().T) ** 2

def trainable_embedding(x, theta, depth=1):
    for w in range(N_QUBITS): qml.Hadamard(wires=w)
    for d in range(depth):
        for w in range(N_QUBITS):
            qml.RY(x[w], wires=w); qml.RZ(theta[d,w,0], wires=w); qml.RY(theta[d,w,1], wires=w)
        for w in range(N_QUBITS - 1): qml.CNOT(wires=[w,w+1])

def trainable_state_qnode():
    dev=qml.device("default.qubit",wires=N_QUBITS)
    @qml.qnode(dev,interface="autograd")
    def state(x,theta,depth):
        trainable_embedding(x,theta,depth)
        return qml.state()
    return state

def _alignment(K,y):
    yy=pnp.outer(y,y)
    # The label-kernel norm is constant; keeping it a Python float avoids
    # Autograd attempting to differentiate a requires_grad=False tensor.
    yy_norm=float(np.sum(np.asarray(yy)**2))
    return pnp.sum(K*yy)/(pnp.sqrt(pnp.sum(K*K)*yy_norm)+1e-12)

def train_kernel_parameters(X,y,depth=1,lr=.03,iterations=12,seed=42,cap=80):
    rng=np.random.default_rng(seed)
    if len(X)>cap:
        pos=np.flatnonzero(y==1); neg=np.flatnonzero(y==0)
        take_pos=min(len(pos),cap//2); idx=np.r_[rng.choice(pos,take_pos,False),rng.choice(neg,cap-take_pos,False)]
        X,y=np.asarray(X)[idx],np.asarray(y)[idx]
    state=trainable_state_qnode(); theta=pnp.array(rng.normal(0,.15,(depth,N_QUBITS,2)),requires_grad=True)
    target=pnp.array(np.where(y==1,1.,-1.),requires_grad=False); opt=qml.AdamOptimizer(lr); history=[]
    def cost(t):
        S=pnp.stack([state(x,t,depth) for x in X]); K=pnp.abs(S @ pnp.conj(S).T)**2
        return -_alignment(K,target)
    for _ in range(iterations):
        theta,c=opt.step_and_cost(cost,theta); history.append(float(-c))
    return np.asarray(theta),history

def trainable_kernel(X,Y,theta,depth=1):
    state=trainable_state_qnode()
    sx=np.asarray([state(x,theta,depth) for x in np.asarray(X)])
    sy=sx if Y is X else np.asarray([state(y,theta,depth) for y in np.asarray(Y)])
    return np.abs(sx @ sy.conj().T)**2

def calibrated_precomputed_svm(Ktrain,y,Kval,seed=42,C=1.0):
    """Fit Platt correction on an inner split, then refit SVM on all outer-training rows."""
    a,b=next(StratifiedShuffleSplit(1,test_size=.25,random_state=seed).split(Ktrain,y))
    inner=SVC(kernel="precomputed",C=C,class_weight="balanced",random_state=seed).fit(Ktrain[np.ix_(a,a)],y[a])
    scores=inner.decision_function(Ktrain[np.ix_(b,a)])
    calibrator=LogisticRegression(random_state=seed).fit(scores.reshape(-1,1),y[b])
    final=SVC(kernel="precomputed",C=C,class_weight="balanced",random_state=seed).fit(Ktrain,y)
    p=calibrator.predict_proba(final.decision_function(Kval).reshape(-1,1))[:,1]
    return p,final,calibrator

def reupload_circuit(x,weights,layers=2):
    for d in range(layers):
        for w in range(N_QUBITS):
            qml.RY(x[w],wires=w); qml.Rot(*weights[d,w],wires=w)
        for w in range(N_QUBITS): qml.CNOT(wires=[w,(w+1)%N_QUBITS])

def train_reupload_qnn(X,y,layers=2,lr=.03,epochs=35,patience=6,seed=42):
    import torch
    torch.manual_seed(seed); torch.set_default_dtype(torch.float64)
    dev=qml.device("default.qubit",wires=N_QUBITS)
    @qml.qnode(dev,interface="torch")
    def circuit(x,w):
        reupload_circuit(x,w,layers); return qml.expval(qml.PauliZ(0))
    a,b=next(StratifiedShuffleSplit(1,test_size=.25,random_state=seed).split(X,y))
    Xt=torch.tensor(np.asarray(X)[a]); yt=torch.tensor(np.asarray(y)[a],dtype=torch.float64)
    Xv=torch.tensor(np.asarray(X)[b]); yv=np.asarray(y)[b]
    w=torch.nn.Parameter(.1*torch.randn(layers,N_QUBITS,3)); opt=torch.optim.Adam([w],lr=lr)
    history=[]; best=(float("inf"),None); stale=0
    for epoch in range(epochs):
        opt.zero_grad(); prob=torch.stack([(1-circuit(x,w))/2 for x in Xt]).clamp(1e-6,1-1e-6)
        loss=torch.nn.functional.binary_cross_entropy(prob,yt); loss_value=float(loss.detach()); loss.backward(); opt.step()
        with torch.no_grad(): pv=np.array([float((1-circuit(x,w))/2) for x in Xv])
        vl=log_loss(yv,np.clip(pv,1e-6,1-1e-6),labels=[0,1]); history.append({"epoch":epoch+1,"train_loss":loss_value,"validation_loss":vl})
        if vl<best[0]-1e-4: best=(vl,w.detach().clone()); stale=0
        else: stale+=1
        if stale>=patience: break
    wbest=best[1]; raw_cal=np.array([float((1-circuit(x,wbest))/2) for x in Xv])
    cal=LogisticRegression(random_state=seed).fit(raw_cal.reshape(-1,1),yv)
    def predict(Z):
        with torch.no_grad(): raw=np.array([float((1-circuit(torch.tensor(x),wbest))/2) for x in np.asarray(Z)])
        return cal.predict_proba(raw.reshape(-1,1))[:,1],raw
    return predict,np.asarray(wbest),history

def circuit_texts():
    x=np.array([.1,.2,.3,.4]); theta=np.zeros((1,4,2)); w=np.zeros((2,4,3))
    return {
      "pennylane_qsvc":qml.draw(equivalent_state)(x),
      "trainable_kernel":qml.draw(trainable_state_qnode())(x,theta,1),
      "data_reuploading":qml.draw(qml.QNode(lambda a,b:(reupload_circuit(a,b,2),qml.expval(qml.PauliZ(0)))[1],qml.device('default.qubit',wires=4)))(x,w)
    }
