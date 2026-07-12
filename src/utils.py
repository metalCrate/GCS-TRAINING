import yaml
config_path = "configs/config.yaml"

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

