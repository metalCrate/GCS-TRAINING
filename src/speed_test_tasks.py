import pygame
from src.utils import config
from src.colors import graphene_map, background_color
from src.pygame_utils import print_multiline
from enum import Enum
import random
import os
import time
import pandas as pd
from typing import Literal
import numpy as np

gap_duration = config['speed_test']['gap_duration']
show_feedback = config['speed_test']['show_feedback']
total_trials = config['speed_test']['total_trials']

class SpeedTestState(Enum):
    PREPARE_STIMULUS = -1
    START = 1
    STIMULUS = 2
    GAP = 3
    END = 4

# Move to a shared file, since this is used in both span_tasks.py and speed_test_tasks.py
class StimulusType(Enum):
    COLOR = 1
    LETTER = 2
    COLORED_LETTER = 3

def stimulus_type_to_string(stimulus_type : StimulusType) -> str:
    if stimulus_type == StimulusType.COLOR:
        return "Colored Square"
    elif stimulus_type == StimulusType.LETTER:
        return "Letter"
    elif stimulus_type == StimulusType.COLORED_LETTER:
        return "Colored Letter"
    else:
        raise ValueError(f"Invalid stimulus type: {stimulus_type}")

class SpeedTestRunner:
    def __init__(self, user_id, mode : Literal["letter-to-color", "color-to-letter"]):
        self.user_id = user_id
        self.mode = mode
        self.task_name = ("Letter to Color" if mode == "letter-to-color" else "Color to Letter") + " Speed Test"
        self.stimulus_type = StimulusType.COLOR if mode == "color-to-letter" else StimulusType.LETTER
        self.target_type = StimulusType.LETTER if mode == "color-to-letter" else StimulusType.COLOR

        self.stimulus_name = stimulus_type_to_string(self.stimulus_type)
        self.target_name = stimulus_type_to_string(self.target_type)

    def generate_summary(self):
        avg_time = np.mean([result["time_to_answer"] for result in self.results])
        accuracy = np.mean([result["is_correct"] for result in self.results]) * 100
        self.summary = [
            "Results Summary",
            f"Average Time to Answer: {avg_time:.2f} seconds",
            f"Accuracy: {accuracy:.2f}%",
            "",
            "Press any key to exit."
        ]

    def start_screen(self, events):
        position = (self.screen.get_width() // 2, self.screen.get_height() // 4)
        _text = [
            f"{self.task_name}",
            f"You will be shown {self.stimulus_name}s.",
            f"Your task is to identify the corresponding {self.target_name}s",
            "as fast as possible and press them.",
            "",
            f"There will be {total_trials} trials in total.",
            "",
            "Press any key to start."
        ]

        print_multiline(self.screen, self.font1, _text, position, 32, pygame.Color('black'), True)

        for event in events:
            if(event.type == pygame.KEYDOWN):
                self.run_state = SpeedTestState.PREPARE_STIMULUS

    def prepare_stimulus(self):
        self.trial_counter += 1

        if self.trial_counter > total_trials:
            self.run_state = SpeedTestState.END
            self.generate_summary()
            return
        
        self.current_stimulus = random.choice(list(graphene_map.keys()))
        self.target_order = list(graphene_map.keys())
        
        if(self.mode == "letter-to-color"):
            random.shuffle(self.target_order)

        self.timer = 0
        self.run_state = SpeedTestState.STIMULUS

    def stimulus_screen(self, events):
        
        # Draw stimulus
        if self.stimulus_type == StimulusType.COLOR:
            sqr_size = 100
            square_rect = pygame.Rect(0,0, sqr_size, sqr_size)
            square_rect.center = self.third_from_top
            _color = graphene_map[self.current_stimulus]
            _color = pygame.Color(_color)
            pygame.draw.rect(self.screen, _color, square_rect)
        else:
            text = self.font2.render(self.current_stimulus, True, pygame.Color('black'))
            text_rect = text.get_rect()
            text_rect.center = self.third_from_top
            self.screen.blit(text, text_rect)

        # Draw targets
        width = self.screen.get_width() / len(graphene_map)
        height_pos = self.screen.get_height() * 3 // 4
        for i, letter in enumerate(self.target_order):
            color = graphene_map[letter]
            if self.target_type == StimulusType.COLOR:
                sqr_size = width
                square_rect = pygame.Rect(0,0, sqr_size, sqr_size)
                square_rect.center = (width * i + width // 2, height_pos)
                _color = pygame.Color(color)
                pygame.draw.rect(self.screen, _color, square_rect)
            else:
                text = self.font2.render(letter, True, pygame.Color('black'))
                text_rect = text.get_rect()
                text_rect.center = (width * i + width // 2, height_pos)
                self.screen.blit(text, text_rect)
        

        found_mouse_click = False
        # Check for left mouse click
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                found_mouse_click = True
                break

        if not found_mouse_click:
            return
        
        # Evaluate mouse click
        mouse_pos = pygame.mouse.get_pos()
        
        # Get the index of the clicked target
        clicked_index = int(mouse_pos[0] // width)
        
        if(clicked_index < 0 or clicked_index >= len(graphene_map)):
            return # Generally shouldnt happen...
        
        # On valid selection
        selected_letter = self.target_order[clicked_index]
        is_correct = (selected_letter == self.current_stimulus)
        
        result = {
            "time_to_answer" : self.timer,
            "target_letter" : self.current_stimulus,
            "selected_letter" : selected_letter,
            "is_correct" : is_correct
        }
        self.results.append(result)
        self.timer = 0 
        self.run_state = SpeedTestState.GAP
        self.feedback_text = "correct" if is_correct else "incorrect"

    def gap_screen(self):
        if self.timer > gap_duration:
            self.run_state = SpeedTestState.PREPARE_STIMULUS
            self.timer = 0
            return
        
        if not show_feedback:
            return
        
        text = self.font1.render(self.feedback_text, True, pygame.Color('black'))
        text_rect = text.get_rect()
        text_rect.center = self.third_from_top
        self.screen.blit(text, text_rect)

    def end_screen(self, events):
        position = (self.screen.get_width() // 2, self.screen.get_height() // 4)


        print_multiline(self.screen, self.font1, self.summary, position, 32, pygame.Color('black'), True)

        for event in events:
            if(event.type == pygame.KEYDOWN):
                return True
            
        return False


    def run(self):
        pygame.init()
        pygame.display.set_caption(self.task_name)
        screen_size = (config['screen']['width'], config['screen']['height'])
        self.screen = pygame.display.set_mode(screen_size)
        self.font1 = pygame.font.Font('freesansbold.ttf', 32)
        self.font2 = pygame.font.Font('freesansbold.ttf', 64)
        clock = pygame.time.Clock()
        self.third_from_top = (self.screen.get_width() // 2, self.screen.get_height() // 3)
        self.middle_position = (self.screen.get_width() // 2, self.screen.get_height() // 2)

        self.trial_counter = 0
        self.timer = 0.0
        self.run_state = SpeedTestState.START
        self.results = []
        self.feedback_text = ""
        while True:
            clock.tick(60) # 60 Fps
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                
            self.timer += clock.get_time() / 1000.0  # seconds

            self.screen.fill(pygame.Color(background_color))
            
            match self.run_state:
                case SpeedTestState.START:
                    self.start_screen(events)
                case SpeedTestState.PREPARE_STIMULUS:
                    self.prepare_stimulus()
                case SpeedTestState.STIMULUS:
                    self.stimulus_screen(events)
                case SpeedTestState.GAP:
                    self.gap_screen()
                case SpeedTestState.END:
                    has_quit = self.end_screen(events)
                    if(has_quit):
                        pygame.quit()
                        return

            pygame.display.flip()

    def log_user_results(self):
        mean_time_to_answer = np.mean([result["time_to_answer"] for result in self.results])
        accuracy = np.mean([result["is_correct"] for result in self.results])
        mean_time_to_correct = np.mean([result["time_to_answer"] for result in self.results if result["is_correct"]])
        mean_time_to_wrong = np.mean([result["time_to_answer"] for result in self.results if not result["is_correct"]])

        time_of_finish = time.strftime("%Y-%m-%d %H:%M:%S")
        new_row = {
            "user_id" : self.user_id,
            "session_number" : 1,
            "mode" : self.mode,
            "stimulus_type" : self.stimulus_type.name,
            "target_type" : self.target_type.name,
            "total_trials" : total_trials,
            "mean_time_to_answer" : mean_time_to_answer,
            "accuracy" : accuracy,
            "mean_time_to_correct" : mean_time_to_correct,
            "mean_time_to_wrong" : mean_time_to_wrong,
            "time_of_finish" : time_of_finish,
        }

        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-speed-test'
        task_directory = os.path.join(user_root, task_folder)
        csv_path = os.path.join(task_directory, 'results.csv')

        if not os.path.exists(task_directory):
            os.makedirs(task_directory)

        if(os.path.exists(csv_path)):
            df = pd.read_csv(csv_path)
            new_row['session_number'] = df['session_number'].max() + 1
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])
        
        df.to_csv(csv_path, index=False)

        return

def run_color_to_letter(user_id):
    runner = SpeedTestRunner(user_id, mode="color-to-letter")
    runner.run()
    runner.log_user_results()

def run_letter_to_color(user_id):
    runner = SpeedTestRunner(user_id, mode="letter-to-color")
    runner.run()
    runner.log_user_results()