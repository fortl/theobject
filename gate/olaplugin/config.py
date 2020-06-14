import yaml
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
FILENAME = str(BASE_DIR / 'config.yaml')

with open(FILENAME) as f:
    config = yaml.safe_load(f)

def save_config():
    with open(FILENAME, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)