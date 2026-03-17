import os

# Needs to happen before local imports
os.environ["ENV_STATE"] = "test"
from src.settings import config
