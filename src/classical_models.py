from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from .preprocessing import classical_pipeline

def models(seed=42):
    inner = StratifiedKFold(3, shuffle=True, random_state=seed + 1)
    logit = classical_pipeline(LogisticRegression(max_iter=2000, random_state=seed))
    logit_search = GridSearchCV(logit, {"model__C":[0.1,1.0,10.0],
                                       "model__class_weight":[None,"balanced"]},
                                scoring="average_precision", cv=inner, n_jobs=1, refit=True)
    calibrated_svm = CalibratedClassifierCV(
        SVC(class_weight="balanced", random_state=seed), method="sigmoid", cv=3)
    svm = classical_pipeline(calibrated_svm)
    svm_search = GridSearchCV(svm, {"model__estimator__C":[0.5,1.0,5.0],
                                    "model__estimator__gamma":["scale",0.1,1.0]},
                              scoring="average_precision", cv=inner, n_jobs=1, refit=True)
    return {
      "DummyPrior": classical_pipeline(DummyClassifier(strategy="prior")),
      "LogisticRegression": logit_search,
      "RBF-SVM": svm_search
    }

SEARCH_PROTOCOL = {
 "LogisticRegression": {"C":[0.1,1.0,10.0], "class_weight":[None,"balanced"]},
 "RBF-SVM": {"C":[0.5,1.0,5.0], "gamma":["scale",0.1,1.0]},
 "note":"Each outer training fold runs a 3-fold stratified average-precision grid search; sigmoid calibration is nested inside the selected RBF-SVM pipeline. Stage1_Test is never used."
}
