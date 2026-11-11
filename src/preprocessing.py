from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, MinMaxScaler

FEATURES = ["age","job","marital","education","default","balance","housing","loan",
            "contact","day","month","campaign","pdays","previous","poutcome"]
NUMERIC = ["age","balance","day","campaign","pdays","previous","pdays_never"]
CATEGORICAL = ["job","marital","education","default","housing","loan","contact","month","poutcome"]

class PDaysEngineer(BaseEstimator, TransformerMixin):
    """Represent pdays=-1 as zero plus an explicit never-contacted indicator."""
    def fit(self, X, y=None): return self
    def transform(self, X):
        X = pd.DataFrame(X).copy()
        X["pdays_never"] = (pd.to_numeric(X["pdays"], errors="coerce") == -1).astype(int)
        X["pdays"] = pd.to_numeric(X["pdays"], errors="coerce").replace(-1, 0)
        return X

def base_preprocessor() -> ColumnTransformer:
    num = Pipeline([("impute", SimpleImputer(strategy="median")),
                    ("scale", RobustScaler())])
    cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("num", num, NUMERIC), ("cat", cat, CATEGORICAL)],
                             remainder="drop", sparse_threshold=0)

def classical_pipeline(model) -> Pipeline:
    return Pipeline([("pdays", PDaysEngineer()), ("preprocess", base_preprocessor()), ("model", model)])

def quantum_preprocessor(n_components=4, seed=42) -> Pipeline:
    # PCA is deliberately fitted inside each outer fold. MinMax bounds angles to [-pi, pi].
    return Pipeline([("pdays", PDaysEngineer()), ("preprocess", base_preprocessor()),
                     ("pca", PCA(n_components=n_components, random_state=seed)),
                     ("angles", MinMaxScaler(feature_range=(-np.pi, np.pi), clip=True))])

def validate_features(df: pd.DataFrame):
    missing = sorted(set(FEATURES) - set(df.columns))
    if missing: raise ValueError(f"Missing required features: {missing}")
