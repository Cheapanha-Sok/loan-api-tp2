"""Move the champion alias to a version: python move_alias.py 2"""
import sys
from mlflow import MlflowClient
MlflowClient().set_registered_model_alias("loan-default", "champion", sys.argv[1])
print(f"champion -> version {sys.argv[1]}")
