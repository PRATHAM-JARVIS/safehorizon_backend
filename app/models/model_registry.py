import os
import pickle
from typing import Any
from ..config import get_settings


def _models_dir() -> str:
    settings = get_settings()
    os.makedirs(settings.models_dir, exist_ok=True)
    return settings.models_dir


def save_model(obj: Any, name: str) -> str:
    path = os.path.join(_models_dir(), f"{name}.pkl")
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return path


def load_model(name: str) -> Any:
    path = os.path.join(_models_dir(), f"{name}.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as f:
        return pickle.load(f)
