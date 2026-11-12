"""Task 5.7 Step 2: register the two best candidates under loan-default and give them roles."""
import mlflow
from mlflow import MlflowClient

NAME = "loan-default"
client = MlflowClient()
runs = {r.info.run_name: r for r in mlflow.search_runs(experiment_names=["loan-default"], output_format="list")}

picks = [
    ("logreg-C=0.1-class_weight=balanced", "champion",
     "Balanced logistic regression: highest recall (0.865) with AUC 0.923; catches the most defaulters."),
    ("forest-max_depth=8-class_weight=balanced", "challenger",
     "Balanced random forest depth 8: AUC 0.925, recall 0.788, precision 0.738; fewer false alarms."),
]
for run_name, alias, description in picks:
    run = runs[run_name]
    mv = mlflow.register_model(f"runs:/{run.info.run_id}/model", NAME)
    client.update_model_version(NAME, mv.version, description=description)
    client.set_registered_model_alias(NAME, alias, mv.version)
    print(f"{NAME} v{mv.version} @{alias} <- run {run.info.run_id} ({run_name})")

client.update_registered_model(NAME, description="Loan default risk model for the loan-api service.")
for v in client.search_model_versions(f"name='{NAME}'"):
    print(f"version {v.version}: aliases={v.aliases} run={v.run_id} | {v.description}")
