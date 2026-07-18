import pygame
import yaml
from src.utils import config
from src.colors import graphene_map, background_color
from src.pygame_utils import print_multiline
from enum import Enum
import random

passive_drill_config = config['passive_drill']

stimulus_duration = passive_drill_config['stimulus_duration']
background_color_duration = passive_drill_config['background_color_duration']
min_repeats = passive_drill_config['min_repeats']
max_repeats = passive_drill_config['max_repeats']
global_repeats = passive_drill_config['global_repeats']

class PassiveDrillRunner:
    def __init__(self):

        self.run_state = PASSIVE_DRILL_STATE.START
        self.current_graphene_index = 0
        self.timer = 0
        self.graphene_display_list = self.generate_graphene_display_list()

    def generate_graphene_display_list(self):
        display_list = []
        ordered_graphenes = sorted(graphene_map.keys())
        for _ in range(global_repeats):
            for g in ordered_graphenes:
                display_list += [g] * random.randint(min_repeats, max_repeats)
        return display_list
    
    def start_screen(self, events):
        self.screen.fill(background_color)
        _text = [
            ""
            "Passive Drill",
            "",
            "You are to watch the letters carefully,",
            "and try to memorize the presented letter-color associations",
            "", 
            f"Estimated time: {self.estimated_time // 60}m {self.estimated_time % 60:.0f}s",
            "",
            "Press any key to start"
        ]

        position = (self.screen.get_width() // 2, self.screen.get_height() // 3)
        print_multiline(self.screen, self.font1, _text, position, 32, pygame.Color('black'), True)
        self.run_state = PASSIVE_DRILL_STATE.START

        for event in events:
                if(event.type == pygame.KEYDOWN):
                    self.run_state = PASSIVE_DRILL_STATE.STIMULUS

    def stimulus_screen(self):
        if(self.current_graphene_index >= len(self.graphene_display_list)):
            self.run_state = PASSIVE_DRILL_STATE.END
            return
        
        self.screen.fill(background_color)
        middle_position = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        graphene = self.graphene_display_list[self.current_graphene_index]
        color = graphene_map[graphene]
        color = pygame.Color(color[0], color[1], color[2])
        text = self.font2.render(graphene, True, color)
        self.screen.blit(text, (middle_position[0] - text.get_width() // 2, middle_position[1] - text.get_height() // 2))
        if(self.timer > stimulus_duration):
            self.run_state = PASSIVE_DRILL_STATE.BACKGROUND
            self.timer = 0

    def background_screen(self):
        graphene = self.graphene_display_list[self.current_graphene_index]
        color = graphene_map[graphene]
        color = pygame.Color(color[0], color[1], color[2])
        self.screen.fill(color)
        if(self.timer > background_color_duration):
            self.run_state = PASSIVE_DRILL_STATE.STIMULUS
            self.current_graphene_index += 1
            self.timer = 0

    def end_screen(self, events):
        self.screen.fill(background_color)
        _text = [
            ""
            "Passive Drill is over",
            "",
            "There are no statistics to display.",
            "",
            "You may quit by pressing the close button or by pressing    any key.",
        ]

        position = (self.screen.get_width() // 2, self.screen.get_height() // 3)
        print_multiline(self.screen, self.font1, _text, position, 32, pygame.Color('black'), True)
        for event in events:
            if(event.type == pygame.KEYDOWN):
                pygame.quit()
                return True
            
        return False
    
    def run(self):
        pygame.init()
        pygame.display.set_caption("Passive Drill")
        screen_size = (config['screen']['width'], config['screen']['height'])
        self.screen = pygame.display.set_mode(screen_size)
        self.font1 = pygame.font.Font('freesansbold.ttf', 32)
        self.font2 = pygame.font.Font('freesansbold.ttf', 64)

        self.estimated_time = (stimulus_duration + background_color_duration) * (min_repeats + max_repeats) / 2 * global_repeats * len(graphene_map)
        self.clock = pygame.time.Clock()
        while True:
            self.clock.tick(60)  # Limit the frame rate to 60 FPS
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.timer += self.clock.get_time() / 1000  # Increment timer by the time elapsed since the last frame in seconds
            match self.run_state:
                case PASSIVE_DRILL_STATE.START:
                    self.start_screen(events)
                case PASSIVE_DRILL_STATE.STIMULUS:
                    self.stimulus_screen()
                case PASSIVE_DRILL_STATE.BACKGROUND:
                    self.background_screen()
                case PASSIVE_DRILL_STATE.END:
                    has_quit = self.end_screen(events)
                    if(has_quit):
                        pygame.quit()
                        return
            pygame.display.flip()

class PASSIVE_DRILL_STATE(Enum):
    START = 0
    STIMULUS = 1
    BACKGROUND = 2
    END = 3

def run_passive_drill():
    runner = PassiveDrillRunner()
    runner.run()


if __name__ == "__main__":
    run_passive_drill()