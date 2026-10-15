"""
Classical Machine Learning Engine for Hospital Quantum Network Defense.
Implements a pure NumPy-based Random Forest Classifier (zero external C-extension DLL dependencies)
capable of:
1. Detecting Threat Type (Normal, Eavesdropping/Theft, Fiber Tampering/Loss, Hardware Fault/Corruption).
2. Localizing the exact optical link and hospital conduit being attacked.
3. Calculating Gini Feature Importances to explain the quantum telemetry decisions.
"""

from typing import Dict, List, Optional, Tuple, Any
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config import LINK_MAP


class PureDecisionTree:
    """Classification Decision Tree with Gini Impurity and Random Feature Subsampling."""

    def __init__(self, max_depth: int = 12, min_samples_split: int = 5, max_features: str = 'sqrt'):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.root: Optional[Dict[str, Any]] = None
        self.feature_gains: Dict[int, float] = {}

    def _gini(self, y: np.ndarray) -> float:
        if len(y) == 0:
            return 0.0
        _, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1.0 - float(np.sum(probs ** 2))

    def _best_split(self, X: np.ndarray, y: np.ndarray, feature_indices: np.ndarray) -> Tuple[Optional[int], Optional[float], float]:
        best_gain = -1.0
        best_feat = None
        best_thresh = None
        current_gini = self._gini(y)
        n = len(y)

        for feat in feature_indices:
            vals = X[:, feat]
            thresholds = np.percentile(vals, [15, 30, 50, 70, 85])
            for thresh in thresholds:
                left_mask = vals <= thresh
                right_mask = ~left_mask
                n_l, n_r = np.sum(left_mask), np.sum(right_mask)
                if n_l < 2 or n_r < 2:
                    continue
                g_l = self._gini(y[left_mask])
                g_r = self._gini(y[right_mask])
                gain = current_gini - ((n_l / n) * g_l + (n_r / n) * g_r)
                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat
                    best_thresh = thresh

        return best_feat, best_thresh, best_gain

    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> Dict[str, Any]:
        classes, counts = np.unique(y, return_counts=True)
        prob_dict = {cls: float(count / len(y)) for cls, count in zip(classes, counts)}
        majority_class = classes[np.argmax(counts)]

        # Stopping criteria
        if depth >= self.max_depth or len(classes) == 1 or len(y) < self.min_samples_split:
            return {'is_leaf': True, 'class': majority_class, 'probs': prob_dict}

        n_feats = X.shape[1]
        m = max(1, int(np.sqrt(n_feats))) if self.max_features == 'sqrt' else n_feats
        feat_subset = np.random.choice(n_feats, size=m, replace=False)

        feat, thresh, gain = self._best_split(X, y, feat_subset)
        if feat is None or gain <= 1e-6:
            return {'is_leaf': True, 'class': majority_class, 'probs': prob_dict}

        # Track Gini feature importance contribution
        self.feature_gains[feat] = self.feature_gains.get(feat, 0.0) + (gain * len(y))

        left_mask = X[:, feat] <= thresh
        right_mask = ~left_mask

        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[right_mask], y[right_mask], depth + 1)

        return {
            'is_leaf': False,
            'feat': int(feat),
            'thresh': float(thresh),
            'left': left_child,
            'right': right_child,
            'probs': prob_dict
        }

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.feature_gains = {}
        self.root = self._build_tree(X, y, depth=0)

    def _predict_row(self, node: Dict[str, Any], x: np.ndarray) -> Tuple[Any, Dict[Any, float]]:
        if node['is_leaf']:
            return node['class'], node['probs']
        if x[node['feat']] <= node['thresh']:
            return self._predict_row(node['left'], x)
        return self._predict_row(node['right'], x)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_row(self.root, row)[0] for row in X])

    def predict_proba(self, X: np.ndarray, all_classes: List[Any]) -> np.ndarray:
        probs = []
        for row in X:
            _, p_dict = self._predict_row(self.root, row)
            p_vec = [p_dict.get(c, 0.0) for c in all_classes]
            probs.append(p_vec)
        return np.array(probs)


class PureRandomForestClassifier:
    """Random Forest Classifier using Bagging and Feature Randomization."""

    def __init__(self, n_estimators: int = 40, max_depth: int = 14, min_samples_split: int = 4):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees: List[PureDecisionTree] = []
        self.classes: List[Any] = []
        self.feature_importances_: np.ndarray = np.array([])

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.classes = sorted(list(np.unique(y)))
        n_samples, n_features = X.shape
        self.trees = []
        feature_accum = np.zeros(n_features)

        for _ in range(self.n_estimators):
            # Bootstrap sample (sample with replacement)
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_b, y_b = X[indices], y[indices]

            tree = PureDecisionTree(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                max_features='sqrt'
            )
            tree.fit(X_b, y_b)
            self.trees.append(tree)

            for feat_idx, g in tree.feature_gains.items():
                feature_accum[feat_idx] += g

        total_gain = np.sum(feature_accum)
        self.feature_importances_ = (feature_accum / total_gain) if total_gain > 0 else feature_accum

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        all_probs = np.zeros((len(X), len(self.classes)))
        for tree in self.trees:
            all_probs += tree.predict_proba(X, self.classes)
        return all_probs / self.n_estimators

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        best_indices = np.argmax(probs, axis=1)
        return np.array([self.classes[i] for i in best_indices])

    def to_dict(self) -> Dict[str, Any]:
        """Serializes forest to pure Python dictionary."""
        return {
            'classes': self.classes,
            'feature_importances': self.feature_importances_.tolist(),
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'trees': [t.root for t in self.trees]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PureRandomForestClassifier':
        """Reconstructs forest from pure Python dictionary."""
        rf = cls(n_estimators=data['n_estimators'], max_depth=data['max_depth'])
        rf.classes = data['classes']
        rf.feature_importances_ = np.array(data['feature_importances'])
        rf.trees = []
        for root in data['trees']:
            tree = PureDecisionTree(max_depth=data['max_depth'])
            tree.root = root
            rf.trees.append(tree)
        return rf


class HospitalSecurityAI:
    def __init__(
        self,
        threat_model_path: str = "rf_threat_model.pkl",
        location_model_path: str = "rf_location_model.pkl"
    ):
        self.threat_model_path = threat_model_path
        self.location_model_path = location_model_path
        self.threat_model: Optional[PureRandomForestClassifier] = None
        self.location_model: Optional[PureRandomForestClassifier] = None
        self.feature_columns: List[str] = []

        if os.path.exists(threat_model_path) and os.path.exists(location_model_path):
            self.load_models()

    def load_models(self):
        with open(self.threat_model_path, "rb") as f:
            data_t = pickle.load(f)
            self.threat_model = PureRandomForestClassifier.from_dict(data_t["model_dict"])
            self.feature_columns = data_t["features"]

        with open(self.location_model_path, "rb") as f:
            data_l = pickle.load(f)
            self.location_model = PureRandomForestClassifier.from_dict(data_l["model_dict"])
        print("ML Models loaded successfully from disk.")

    def save_models(self):
        with open(self.threat_model_path, "wb") as f:
            pickle.dump({"model_dict": self.threat_model.to_dict(), "features": self.feature_columns}, f)
        with open(self.location_model_path, "wb") as f:
            pickle.dump({"model_dict": self.location_model.to_dict(), "features": self.feature_columns}, f)

    def train_and_evaluate(
        self,
        csv_path: str = "hospital_qkd_telemetry_dataset.csv",
        report_fig_path: str = "ml_evaluation_report.png"
    ):
        print(f"Loading telemetry dataset from {csv_path}...")
        df = pd.read_csv(csv_path)

        target_threat = df["target_threat"].values
        target_link = df["target_link"].values

        drop_cols = ["target_threat", "target_link", "target_location"]
        X_df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        self.feature_columns = list(X_df.columns)
        X = X_df.values.astype(np.float32)

        # 80/20 Train Test Split
        n = len(X)
        indices = np.arange(n)
        np.random.seed(42)
        np.random.shuffle(indices)

        split_idx = int(n * 0.8)
        train_idx, test_idx = indices[:split_idx], indices[split_idx:]

        X_train, X_test = X[train_idx], X[test_idx]
        y_threat_train, y_threat_test = target_threat[train_idx], target_threat[test_idx]
        y_link_train, y_link_test = target_link[train_idx], target_link[test_idx]

        print(f"Dataset split: {len(X_train)} training records, {len(X_test)} evaluation records.")
        print(f"Features: {X.shape[1]} metrics per network telemetry snapshot.")

        # 1. Train Threat Classifier
        print("\n" + "=" * 60)
        print("1. TRAINING THREAT CLASSIFIER (Random Forest Ensemble)")
        print("=" * 60)
        self.threat_model = PureRandomForestClassifier(n_estimators=35, max_depth=14)
        self.threat_model.fit(X_train, y_threat_train)

        threat_preds = self.threat_model.predict(X_test)
        threat_acc = np.mean(threat_preds == y_threat_test)
        print(f"Threat Classifier Accuracy: {threat_acc:.2%}")

        # 2. Train Localization Engine
        print("\n" + "=" * 60)
        print("2. TRAINING LOCALIZATION ENGINE (Random Forest Ensemble)")
        print("=" * 60)
        self.location_model = PureRandomForestClassifier(n_estimators=35, max_depth=14)
        self.location_model.fit(X_train, y_link_train)

        link_preds = self.location_model.predict(X_test)
        link_acc = np.mean(link_preds == y_link_test)
        print(f"Physical Localization Accuracy: {link_acc:.2%}")

        self.save_models()
        print(f"\nTrained models persisted to '{self.threat_model_path}' and '{self.location_model_path}'.")

        # Visualizations
        self._plot_evaluation_diagnostics(
            y_threat_test, threat_preds,
            y_link_test, link_preds,
            report_fig_path
        )
        print(f"Visual diagnostic report saved to: {report_fig_path}")

    def _plot_evaluation_diagnostics(
        self,
        y_threat_true: np.ndarray, y_threat_pred: np.ndarray,
        y_link_true: np.ndarray, y_link_pred: np.ndarray,
        save_path: str
    ):
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        fig.patch.set_facecolor('#0f172a')

        # 1. Threat Classification Confusion Matrix
        labels = sorted(list(set(y_threat_true)))
        cm = np.zeros((len(labels), len(labels)), dtype=int)
        label_to_idx = {l: i for i, l in enumerate(labels)}
        for t, p in zip(y_threat_true, y_threat_pred):
            cm[label_to_idx[t], label_to_idx[p]] += 1

        ax1 = axes[0]
        ax1.set_facecolor('#1e293b')
        cax1 = ax1.imshow(cm, cmap='Blues', interpolation='nearest')
        ax1.set_title("Threat Classifier Confusion Matrix", color='#f8fafc', fontsize=13, fontweight='bold', pad=12)
        ax1.set_xticks(range(len(labels)))
        ax1.set_yticks(range(len(labels)))
        ax1.set_xticklabels(labels, rotation=30, ha='right', color='#e2e8f0', fontsize=9)
        ax1.set_yticklabels(labels, color='#e2e8f0', fontsize=9)
        ax1.set_xlabel("Predicted Threat", color='#94a3b8', fontsize=11)
        ax1.set_ylabel("Ground Truth Threat", color='#94a3b8', fontsize=11)

        for i in range(len(labels)):
            for j in range(len(labels)):
                ax1.text(j, i, str(cm[i, j]), ha="center", va="center",
                         color="white" if cm[i, j] > cm.max() / 2 else "black",
                         fontweight='bold', fontsize=10)

        # 2. Top 10 Feature Importances
        ax2 = axes[1]
        ax2.set_facecolor('#1e293b')
        importances = self.threat_model.feature_importances_
        top_k = min(10, len(importances))
        sorted_indices = np.argsort(importances)[::-1][:top_k]

        top_feats = [self.feature_columns[i] for i in sorted_indices]
        top_vals = importances[sorted_indices]

        ax2.barh(range(top_k), top_vals[::-1], color='#38bdf8', edgecolor='#0284c7')
        ax2.set_yticks(range(top_k))
        ax2.set_yticklabels(top_feats[::-1], color='#e2e8f0', fontsize=9)
        ax2.set_xlabel("Gini Feature Importance", color='#94a3b8', fontsize=11)
        ax2.set_title("Top 10 Quantum Telemetry Predictors", color='#f8fafc', fontsize=13, fontweight='bold', pad=12)
        ax2.tick_params(colors='#94a3b8')

        plt.tight_layout()
        plt.savefig(save_path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)

    def analyze_network_telemetry(self, raw_telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs real-time ML inference on live hospital network telemetry.
        """
        if self.threat_model is None or self.location_model is None:
            self.load_models()

        row = np.array([[raw_telemetry[col] for col in self.feature_columns]], dtype=np.float32)

        # Threat Prediction
        threat_probs = self.threat_model.predict_proba(row)[0]
        threat_idx = np.argmax(threat_probs)
        threat_pred = self.threat_model.classes[threat_idx]
        threat_conf = float(threat_probs[threat_idx])

        # Location Prediction
        link_probs = self.location_model.predict_proba(row)[0]
        link_idx = np.argmax(link_probs)
        link_pred = self.location_model.classes[link_idx]
        link_conf = float(link_probs[link_idx])

        physical_loc = "NONE (All hospital fiber conduits secure)"
        if link_pred != "NONE" and link_pred in LINK_MAP:
            physical_loc = LINK_MAP[link_pred].physical_location

        # Dynamic Incident Response Action
        if threat_pred == "NORMAL":
            action = "Channel secure. Transmitting patient medical telemetry normally."
        elif threat_pred == "EAVESDROPPING":
            action = (
                f"CRITICAL BREACH! Eve intercept-resend attack detected at [{physical_loc}]. "
                f"Aborting QKD key generation on link {link_pred}. Rerouting patient data."
            )
        elif threat_pred == "FIBER_TAMPER":
            action = (
                f"PHYSICAL FIBER COMPROMISED! Severe photon loss detected at [{physical_loc}]. "
                f"Dispatching hospital physical security to inspect conduit. Rerouting traffic."
            )
        else:
            action = (
                f"HARDWARE ANOMALY! Excessive optical noise on transceiver at [{physical_loc}]. "
                f"Schedule laser recalibration and detector diagnostic."
            )

        return {
            "predicted_threat": threat_pred,
            "threat_confidence": round(threat_conf * 100, 2),
            "predicted_link": link_pred,
            "link_confidence": round(link_conf * 100, 2),
            "physical_location": physical_loc,
            "recommended_action": action
        }


if __name__ == "__main__":
    ai = HospitalSecurityAI()
    ai.train_and_evaluate()
