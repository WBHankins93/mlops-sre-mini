"""Train Logistic Regression on Iris and write model.pkl at the repo root.
Prints accuracy so we can spot regressions later.
"""
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from pathlib import Path
import pickle

def main():
    iris = load_iris()
    X, y = iris.data, iris.target
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=200)
    clf.fit(X_tr, y_tr)

    acc = accuracy_score(y_te, clf.predict(X_te))
    print(f"accuracy={acc:.4f}")

    out_path = Path(__file__).resolve().parents[1] / "model.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(clf, f)
    print(f"wrote {out_path}")

if __name__ == "__main__":
    main()
