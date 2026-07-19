from src.utils import config
from src.colors import graphene_map, background_color

from src.passive_drill import run_passive_drill
from src.dmts import run_early_dmts, run_late_dmts
from src.span_tasks import run_early_span, run_late_span, run_advanced_span
from src.speed_test_tasks import run_color_to_letter, run_letter_to_color