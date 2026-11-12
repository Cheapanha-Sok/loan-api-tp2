"""Train several loan-default models and track every run in MLflow.

Task 5.7: extended from the four runs of Lesson 5.2 to eight runs across
three model types (logistic regression, random forest, gradient boosting).
"""
import matplotlib
matplotlib.use("Agg")  # draw charts without a screen
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import RocCurveDisplay, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data import FEATURES, make_data

mlflow.set_experiment("loan-default")  # created on first use

df = make_data()
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURES], df.defaulted, test_size=0.2, random_state=42)

candidates = [
    ("logreg", {"C": 0.1, "class_weight": None}),
    ("logreg", {"C": 0.1, "class_weight": "balanced"}),
    ("logreg", {"C": 1.0, "class_weight": "balanced"}),
    ("forest", {"max_depth": 4, "class_weight": None}),
    ("forest", {"max_depth": 8, "class_weight": "balanced"}),
    ("forest", {"max_depth": 12, "class_weight": "balanced"}),
    ("gboost", {"max_depth": 2, "learning_rate": 0.1}),
    ("gboost", {"max_depth": 3, "learning_rate": 0.05}),
]

TRUSTED = {
    "forest": ["sklearn.tree._tree.Tree"],
    "gboost": ["sklearn.tree._tree.Tree", "sklearn._loss.loss.HalfBinomialLoss",
               "sklearn._loss.link.LogitLink", "sklearn._loss.link.Interval",
               "sklearn.ensemble._gb.LossFunction"],
}


def build(kind, params):
    if kind == "logreg":
        return make_pipeline(StandardScaler(), LogisticRegression(**params))
    if kind == "forest":
        return RandomForestClassifier(n_estimators=200, random_state=42, **params)
    return GradientBoostingClassifier(n_estimators=200, random_state=42, **params)


for kind, params in candidates:
    model = build(kind, params)
    with mlflow.start_run(run_name=f"{kind}-" + "-".join(f"{k}={v}" for k, v in params.items())):
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        predicted = proba >= 0.5
        auc, rec, prec = (roc_auc_score(y_test, proba), recall_score(y_test, predicted),
                          precision_score(y_test, predicted))
        mlflow.log_params({"model": kind, **{k: str(v) for k, v in params.items()}})
        mlflow.log_metrics({"auc": auc, "recall": rec, "precision": prec})
        mlflow.log_figure(RocCurveDisplay.from_predictions(y_test, proba).figure_, "roc_curve.png")
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            signature=infer_signature(X_test, model.predict_proba(X_test)),
            input_example=X_test.head(3),
            pyfunc_predict_fn="predict_proba",  # serving returns probabilities, not 0/1
            skops_trusted_types=TRUSTED.get(kind),
        )
        print(f"{kind:<6} {params} auc={auc:.3f} recall={rec:.3f} precision={prec:.3f}")
