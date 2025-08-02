# config/loader.py
import json
from pathlib import Path
from .models import CountyCfg, Catalogue

CATALOGUE_PATH = Path(__file__).with_name("utility_endpoints.json")

def load_catalogue() -> Catalogue:
    raw = json.loads(CATALOGUE_PATH.read_text())
    return {k: CountyCfg(**v) for k, v in raw.items()}
