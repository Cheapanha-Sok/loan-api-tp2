"""Build the experiment table/chart and the drift chart for the Task 5.7 report from the tracking server."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
from mlflow import MlflowClient

client = MlflowClient()
runs = mlflow.search_runs(experiment_names=["loan-default"]).sort_values("start_time")
cols = ["tags.mlflow.runName", "params.model", "metrics.auc", "metrics.recall", "metrics.precision", "run_id"]
table = runs[cols].rename(columns=lambda c: c.split(".")[-1]).round(3)
table.to_csv("report/experiment_table.csv", index=False)
print(table.to_string(index=False))

colors = {"logreg": "#2a6fdb", "forest": "#1f9d55", "gboost": "#d97706"}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
for _, r in table.iterrows():
    a1.scatter(r.recall, r.precision, s=90 + 900 * (r.auc - 0.9), color=colors[r.model], alpha=.8)
    a1.annotate(r.runName.replace("-class_weight", " cw").replace("learning_rate", "lr"),
                (r.recall, r.precision), fontsize=7, xytext=(4, 4), textcoords="offset points")
a1.set(xlabel="recall (share of defaulters caught)", ylabel="precision", title="8 runs: recall vs precision (size = AUC)")
for k, c in colors.items(): a1.scatter([], [], color=c, label=k)
a1.legend(); a1.grid(alpha=.3)
x = range(len(table)); w = .27
for i, m in enumerate(["auc", "recall", "precision"]):
    a2.bar([j + (i - 1) * w for j in x], table[m], w, label=m)
a2.set_xticks(list(x)); a2.set_xticklabels([n.split("-")[0] + "\n" + "-".join(n.split("-")[1:2]) for n in table.runName], fontsize=7)
a2.set_ylim(.5, 1); a2.legend(); a2.grid(axis="y", alpha=.3); a2.set_title("AUC / recall / precision per run")
fig.tight_layout(); fig.savefig("report/runs_comparison.png", dpi=130)

mon = mlflow.search_runs(experiment_names=["loan-default-monitoring"]).iloc[0].run_id
hist = lambda k: sorted((m.step, m.value) for m in client.get_metric_history(mon, k))
fig, (b1, b2) = plt.subplots(1, 2, figsize=(13, 4.6))
for k in ["psi_monthly_income_usd", "psi_amount_usd", "psi_late_payments"]:
    s, v = zip(*hist(k)); b1.plot(s, v, marker="o", label=k)
b1.axhline(.1, ls="--", color="orange", label="warn 0.1"); b1.axhline(.2, ls="--", color="red", label="alert 0.2")
b1.set(xlabel="day", ylabel="PSI", title="Feature drift (PSI) over 14 days"); b1.legend(fontsize=8); b1.grid(alpha=.3)
for k in ["mean_predicted_default", "actual_default_rate"]:
    s, v = zip(*hist(k)); b2.plot(s, v, marker="o", label=k)
b2.axhline(.40, ls="--", color="red", label="alert 0.40")
b2.set(xlabel="day", title="Prediction drift"); b2.legend(fontsize=8); b2.grid(alpha=.3)
fig.tight_layout(); fig.savefig("report/drift_chart.png", dpi=130)
print("monitor run", mon)
