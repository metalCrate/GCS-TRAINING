import pygame
from sqlalchemy import case
import yaml
from utils import config
from colors import graphene_map, background_color
from pygame_utils import print_multiline
from enum import Enum
import random

passive_drill_config = config['passive_drill']

stimulus_duration = passive_drill_config['stimulus_duration']
background_color_duration = passive_drill_config['background_color_duration']
min_repeats = passive_drill_config['min_repeats']
max_repeats = passive_drill_config['max_repeats']
global_repeats = passive_drill_config['global_repeats']


class PASSIVE_DRILL_STATE(Enum):
    START = 0
    STIMULUS = 1
    BACKGROUND = 2
    END = 3

def start_screen(screen: pygame.Surface, font: pygame.font.Font, events: list[pygame.event.Event], estimated_time: int):
    screen.fill(background_color)
    _text = [
        ""
        "Passive Drill",
        "",
        "\"Participants were instructed to watch the letters carefully,",
        "and to try to memorize the presented letter-color associations\"",
        "",
        f"Estimated time: {estimated_time // 60}m {estimated_time % 60:.0f}s",
        "",
        "Press any key to start"
    ]

    position = (screen.get_width() // 2, screen.get_height() // 3)
    print_multiline(screen, font, _text, position, 32, pygame.Color('black'), True)
    run_state = PASSIVE_DRILL_STATE.START
    for event in events:
            if(event.type == pygame.KEYDOWN):
                run_state = PASSIVE_DRILL_STATE.STIMULUS

    return run_state

def run_passive_drill():
    run_state = PASSIVE_DRILL_STATE.START

    pygame.init()
    pygame.display.set_caption("Passive Drill")
    screen_size = (config['screen']['width'], config['screen']['height'])
    screen = pygame.display.set_mode(screen_size)
    font1 = pygame.font.Font('freesansbold.ttf', 32)
    font2 = pygame.font.Font('freesansbold.ttf', 64)

    estimated_time = (stimulus_duration + background_color_duration) * (min_repeats + max_repeats) / 2 * global_repeats * len(graphene_map)
    clock = pygame.time.Clock()
    

    graphene_display_list = () # Could instead generate on the fly, but its easier to implement and will run efficiently nontheless
    ordered_graphenes = sorted(graphene_map.keys())

    for _ in range(global_repeats):
        for g in ordered_graphenes:
            graphene_display_list += (g,) * random.randint(min_repeats, max_repeats)

    current_graphene_index = 0
    timer = 0
    while True:
        clock.tick(60)  # Limit the frame rate to 60 FPS
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        timer += clock.get_time() / 1000  # Increment timer by the time elapsed since the last frame in seconds
        match run_state:
            case PASSIVE_DRILL_STATE.START:
                run_state = start_screen(screen, font1, events, estimated_time)
                if(run_state == PASSIVE_DRILL_STATE.STIMULUS):
                    timer = 0
            case PASSIVE_DRILL_STATE.STIMULUS:

                if(current_graphene_index >= len(graphene_display_list)):
                    run_state = PASSIVE_DRILL_STATE.END
                    continue

                screen.fill(background_color)
                middle_position = (screen.get_width() // 2, screen.get_height() // 2)
                graphene = graphene_display_list[current_graphene_index]
                color = graphene_map[graphene]
                color = pygame.Color(color[0], color[1], color[2])
                text = font2.render(graphene, True, color)
                screen.blit(text, (middle_position[0] - text.get_width() // 2, middle_position[1] - text.get_height() // 2))
                if(timer > stimulus_duration):
                    run_state = PASSIVE_DRILL_STATE.BACKGROUND
                    timer = 0

            case PASSIVE_DRILL_STATE.BACKGROUND:
                color = graphene_map[graphene]
                color = pygame.Color(color[0], color[1], color[2])
                screen.fill(color)
                if(timer > stimulus_duration):
                    run_state = PASSIVE_DRILL_STATE.STIMULUS
                    current_graphene_index += 1
                    timer = 0

            case PASSIVE_DRILL_STATE.END:
                screen.fill(background_color)
                _text = [
                    ""
                    "Passive Drill is over",
                    "",
                    "There are no statistics to display.",
                    "",
                    "You may quit by pressing the close button or by pressing    any key.",
                ]

                position = (screen.get_width() // 2, screen.get_height() // 3)
                print_multiline(screen, font1, _text, position, 32, pygame.Color('black'), True)

                for event in events:
                    if(event.type == pygame.KEYDOWN):
                        pygame.quit()
                        return


        # Update the display
        pygame.display.flip()

if __name__ == "__main__":
    run_passive_drill()