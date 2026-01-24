from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional


def _sigmoid(z: float) -> float:
    # stable sigmoid
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)


@dataclass
class SimpleLogisticRegression:
    l2: float = 1e-4
    lr: float = 0.05
    epochs: int = 5
    seed: int = 0
    pos_weight: float = 1.0  # weight for y=1
    neg_weight: float = 1.0  # weight for y=0

    w: Optional[List[float]] = None
    b: float = 0.0

    def _init(self, n_features: int) -> None:
        rng = random.Random(self.seed)
        self.w = [(rng.random() - 0.5) * 0.01 for _ in range(n_features)]
        self.b = 0.0

    def _dot(self, x: List[float]) -> float:
        assert self.w is not None
        s = 0.0
        for wi, xi in zip(self.w, x):
            s += wi * xi
        return s

    def fit(self, X: List[List[float]], y: List[int]) -> "SimpleLogisticRegression":
        if not X:
            raise ValueError("Empty X")
        n_features = len(X[0])
        self._init(n_features)

        assert self.w is not None
        rng = random.Random(self.seed)

        idxs = list(range(len(X)))

        for _ in range(self.epochs):
            rng.shuffle(idxs)
            for i in idxs:
                xi = X[i]
                yi = 1 if y[i] else 0
                z = self._dot(xi) + self.b
                p = _sigmoid(z)

                # weight by class
                w_cls = self.pos_weight if yi == 1 else self.neg_weight

                # grad for logloss: (p - y)*x
                err = (p - yi) * w_cls

                # L2
                for j in range(n_features):
                    self.w[j] -= self.lr * (err * xi[j] + self.l2 * self.w[j])
                self.b -= self.lr * err

        return self

    def predict_proba(self, X: List[List[float]]) -> List[float]:
        if self.w is None:
            raise ValueError("Model not fitted")
        out = []
        for xi in X:
            z = self._dot(xi) + self.b
            out.append(_sigmoid(z))
        return out

    def predict_logits(self, X: List[List[float]]) -> List[float]:
        if self.w is None:
            raise ValueError("Model not fitted")
        out = []
        for xi in X:
            z = self._dot(xi) + self.b
            out.append(float(z))
        return out

    def predict(self, X: List[List[float]]) -> List[int]:
        return [1 if p >= 0.5 else 0 for p in self.predict_proba(X)]


class SimpleDictVectorizer:
    """Simple implementation of DictVectorizer for ML features"""
    
    def __init__(self):
        self.feature_names_ = []
        self.vocabulary_ = {}
    
    def fit_transform(self, X_dict):
        """Fit vectorizer and transform data"""
        # Collect all feature names
        feature_set = set()
        for x in X_dict:
            feature_set.update(x.keys())
        self.feature_names_ = sorted(feature_set)
        self.vocabulary_ = {name: idx for idx, name in enumerate(self.feature_names_)}
        
        # Create sparse matrix representation
        X = []
        for x in X_dict:
            row = [0.0] * len(self.feature_names_)
            for name, value in x.items():
                if name in self.vocabulary_:
                    row[self.vocabulary_[name]] = value
            X.append(row)
        return X
    
    def transform(self, X_dict):
        """Transform data using fitted vectorizer"""
        X = []
        for x in X_dict:
            row = [0.0] * len(self.feature_names_)
            for name, value in x.items():
                if name in self.vocabulary_:
                    row[self.vocabulary_[name]] = value
            X.append(row)
        return X


class SimpleRidge:
    """Simple Ridge regression implementation"""
    
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.weights_ = None
        self.bias_ = None
    
    def fit(self, X, y):
        """Fit Ridge regression model"""
        import numpy as np
        X = np.array(X)
        y = np.array(y)
        
        # Add bias term
        X_with_bias = np.column_stack([X, np.ones(X.shape[0])])
        
        # Ridge regression: (X^T X + alpha*I)^-1 X^T y
        n_features = X_with_bias.shape[1]
        identity = np.eye(n_features)
        identity[-1, -1] = 0  # Don't regularize bias
        
        self.weights_ = np.linalg.solve(
            X_with_bias.T @ X_with_bias + self.alpha * identity,
            X_with_bias.T @ y
        )
        self.bias_ = self.weights_[-1]
        self.weights_ = self.weights_[:-1]
    
    def predict(self, X):
        """Predict using fitted model"""
        import numpy as np
        X = np.array(X)
        return X @ self.weights_ + self.bias_


class SimpleDecisionTreeRegressor:
    """Simple Decision Tree Regressor implementation"""
    
    def __init__(self, max_depth=3, min_samples_split=2, max_features=None, random_state=0):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state
        self.tree_ = None

    def fit(self, X, y):
        """Fit decision tree model"""
        import numpy as np
        rng = np.random.RandomState(self.random_state)
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n_features = X.shape[1]

        if self.max_features is None:
            max_feats = n_features
        else:
            max_feats = min(n_features, int(self.max_features))

        def build_node(idxs, depth):
            # leaf
            if depth >= self.max_depth or len(idxs) < self.min_samples_split:
                return {"leaf": True, "value": float(np.mean(y[idxs]))}

            feat_candidates = rng.choice(n_features, size=max_feats, replace=False)
            best = {"score": float("inf")}

            for f in feat_candidates:
                # пороги: возьмем несколько квантилей вместо всех уникальных
                col = X[idxs, f]
                qs = np.unique(np.quantile(col, [0.2, 0.4, 0.6, 0.8]))
                for thr in qs:
                    left = [i for i in idxs if X[i, f] <= thr]
                    right = [i for i in idxs if X[i, f] > thr]
                    if not left or not right:
                        continue
                    # mse
                    mse_left = np.var(y[left]) * len(left)
                    mse_right = np.var(y[right]) * len(right)
                    mse = mse_left + mse_right
                    if mse < best["score"]:
                        best = {"score": mse, "f": int(f), "thr": float(thr), "left": left, "right": right}

            if "f" not in best:
                return {"leaf": True, "value": float(np.mean(y[idxs]))}

            return {
                "leaf": False,
                "f": best["f"],
                "thr": best["thr"],
                "left": build_node(best["left"], depth + 1),
                "right": build_node(best["right"], depth + 1),
            }

        self.tree_ = build_node(list(range(len(X))), 0)
        return self

    def _predict_one(self, row, node):
        """Predict single sample"""
        if node["leaf"]:
            return node["value"]
        if row[node["f"]] <= node["thr"]:
            return self._predict_one(row, node["left"])
        return self._predict_one(row, node["right"])

    def predict(self, X):
        """Predict using fitted tree"""
        import numpy as np
        X = np.asarray(X, dtype=float)
        return np.array([self._predict_one(x, self.tree_) for x in X], dtype=float)


class SimpleRandomForestRegressor:
    """Simple Random Forest Regressor implementation"""
    
    def __init__(self, n_estimators=50, max_depth=4, sample_ratio=0.8, max_features="sqrt", random_state=0):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.sample_ratio = sample_ratio
        self.max_features = max_features
        self.random_state = random_state
        self.trees_ = []

    def fit(self, X, y):
        """Fit random forest model"""
        import numpy as np
        rng = np.random.RandomState(self.random_state)
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n = len(X)
        n_features = X.shape[1]

        if self.max_features == "sqrt":
            mf = max(1, int(np.sqrt(n_features)))
        elif self.max_features == "log2":
            mf = max(1, int(np.log2(n_features)))
        elif self.max_features is None:
            mf = n_features
        else:
            mf = int(self.max_features)

        self.trees_ = []
        m = max(2, int(n * self.sample_ratio))

        for t in range(self.n_estimators):
            idxs = rng.randint(0, n, size=m)  # bootstrap
            tree = SimpleDecisionTreeRegressor(
                max_depth=self.max_depth,
                min_samples_split=2,
                max_features=mf,
                random_state=int(rng.randint(0, 1_000_000))
            )
            tree.fit(X[idxs], y[idxs])
            self.trees_.append(tree)
        return self

    def predict(self, X):
        """Predict using fitted forest"""
        import numpy as np
        X = np.asarray(X, dtype=float)
        preds = np.stack([tr.predict(X) for tr in self.trees_], axis=0)
        return np.mean(preds, axis=0)
