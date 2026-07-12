import json
from utils import config

with open(config['colors_map_path'], 'r') as f:
    color_map = json.load(f)

graphene_map = color_map['graphenes']
background_color = color_map['background']