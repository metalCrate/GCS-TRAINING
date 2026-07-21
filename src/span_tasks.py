import pygame
from src.utils import config
from src.colors import graphene_map, background_color
from src.pygame_utils import print_multiline
from enum import Enum
import random
import os
import json
import time
import pandas as pd
from typing import Literal
import numpy as np

span_config = config['span']

stimulus_duration = span_config['stimulus_duration']
gap_duration = span_config['gap_duration']
total_trials = span_config['total_trials']
response_delay = span_config['response_delay']
initial_sequence_length = span_config['initial_sequence_length']

class SPAN_STATE(Enum):
    GENERATE_SEQUENCE = -1
    START = 1
    STIMULUS = 2
    STIMULUS_GAP = 3
    RESPONSE_GAP = 4
    RESPONSE = 5
    FEEDBACK = 6
    END = 7
    
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

class SpanRunner:
    def __init__(self, user_id, mode : Literal["early", "late", "advanced"]):
        self.user_id = user_id
        self.mode = mode
        
        if self.mode == "early":
            self.stimulus_type = StimulusType.COLORED_LETTER
            self.target_type = StimulusType.COLOR
        elif self.mode == "late":
            self.stimulus_type = StimulusType.COLOR
            self.target_type = StimulusType.LETTER
        else:
            self.stimulus_type = StimulusType.LETTER
            self.target_type = StimulusType.COLOR

        self.stimulus_name = stimulus_type_to_string(self.stimulus_type)
        self.target_name = stimulus_type_to_string(self.target_type)
        
        self.task_name = f"{self.mode.capitalize()} Span"

        self.run_state = SPAN_STATE.START
        self.timer = 0
        self.trial_counter = 0
        self.results = []
        self.feedback_text = ""
    
    def generate_summary(self):
        avg_seq_len = np.mean([result['sequence_length'] for result in self.results])
        accuracy = np.mean([result['is_correct'] for result in self.results])

        self.summary = [
            f"Average sequence length: {avg_seq_len:.1f}",
            f"Average correct answers: {accuracy:.1%}",
            "",
            "Press any key to exit."
        ]

    def start_screen(self, events):
        self.screen.fill(self.background_color)

        _text = [
            f"{self.task_name}",
            "",
            f"You will be shown a sequence of {self.stimulus_name}s",
            "After a short delay, you will be asked to recall the sequence",
            f"by selecting the corresponding {self.target_name}s in order",
            "With each successful trial, the sequence will get longer by 1",
            "With each failed trial, the sequence will get shorter by 1",
            "",
            "Hover over the targets, and click to select them in order",
            "",
            "Press any key to start"
        ]

        position = (self.screen.get_width() // 2, self.screen.get_height() // 4)
        print_multiline(self.screen, self.font1, _text, position, 32, pygame.Color('black'), True)

        for event in events:
            if(event.type == pygame.KEYDOWN):
                self.run_state = SPAN_STATE.GENERATE_SEQUENCE

    def stimulus_screen(self):
        self.screen.fill(self.background_color)
        
        stimulus_key = self.current_sequence[self.current_sequence_index]
        stimulus_color = self.graphene_map[stimulus_key]

        match self.stimulus_type:
            case StimulusType.COLOR:
                rect_size = 200
                rect_pos = (self.middle_position[0] - rect_size // 2, self.middle_position[1] - rect_size // 2)
                rect = pygame.Rect(rect_pos, (rect_size, rect_size))
                pygame.draw.rect(self.screen, pygame.Color(stimulus_color), rect)

            case StimulusType.LETTER:
                _text = self.font2.render(stimulus_key, True, pygame.Color('black'))
                text_rect = _text.get_rect(center=self.middle_position)
                self.screen.blit(_text, text_rect)

            case StimulusType.COLORED_LETTER:
                _text = self.font2.render(stimulus_key, True, pygame.Color(stimulus_color))
                text_rect = _text.get_rect(center=self.middle_position)
                self.screen.blit(_text, text_rect)

        if(self.timer > stimulus_duration):
            self.timer = 0
            self.current_sequence_index += 1
            if(self.current_sequence_index >= len(self.current_sequence)):
                self.run_state = SPAN_STATE.RESPONSE_GAP
            else:
                self.run_state = SPAN_STATE.STIMULUS_GAP

    def stimulus_gap_screen(self):
        self.screen.fill(self.background_color)

        if(self.timer > gap_duration):
            self.timer = 0
            self.run_state = SPAN_STATE.STIMULUS

    def response_gap_screen(self):
        self.screen.fill(self.background_color)
        print_multiline(self.screen, self.font1, ["respond"], self.middle_position, 32, pygame.Color('black'), True)
        #_text = self.font1.render("respond", True, pygame.Color('black'))
        #self.screen.blit(_text, self.middle_position)

        if(self.timer > response_delay):
            self.timer = 0
            self.current_sequence_index = 0
            self.current_response = []
            self.already_pressed_targets = []
            self.run_state = SPAN_STATE.RESPONSE

    def evaluate_response(self, mouse_pos):
        mouse_x = mouse_pos[0]
        num_targets = len(self.graphene_map)
        target_width = self.screen.get_width() / num_targets

        # Find which target was clicked
        target_index = mouse_x // target_width
        target_index = int(target_index)
        if not (0 <= target_index < num_targets):
            return
        
        if (target_index in self.already_pressed_targets):
            return
        
        self.already_pressed_targets.append(target_index)
        self.current_response.append(target_index)
        
    def evaluate_user_sequence(self):
        correct_sequence = self.current_sequence
        user_sequence = [self.target_keys[i] for i in self.current_response]
        #print(f"Correct sequence: {correct_sequence}")
        #print(f"User sequence: {user_sequence}")
        if(user_sequence == correct_sequence):
            self.feedback_text = "correct"
            self.current_sequence_len += 1
        else:
            self.feedback_text = "incorrect"
            self.current_sequence_len -= 1

        result = {
            "correct_sequence": correct_sequence,
            "user_sequence": user_sequence,
            "is_correct": user_sequence == correct_sequence,
            "sequence_length": len(correct_sequence),
            "time_to_answer": self.timer
        }
        self.results.append(result)
        self.current_sequence_len = np.clip(self.current_sequence_len, 1, len(self.graphene_map))

    def response_screen(self, events):
        self.screen.fill(self.background_color)

        if(self.target_type == StimulusType.COLOR):
            for i, rect in enumerate(self.target_rects):
                if i in self.already_pressed_targets:
                    continue
                _col = self.graphene_map[self.target_keys[i]]
                _col = pygame.Color(_col)
                pygame.draw.rect(self.screen, _col, rect)
        else:
            for i, middle in enumerate(self.target_middles):
                if i in self.already_pressed_targets:
                    continue
                
                if self.target_type == StimulusType.LETTER:
                    _col = pygame.Color('black')
                else:
                    _col = pygame.Color(self.graphene_map[self.target_keys[i]])

                _text = self.font2.render(self.target_keys[i], True, _col)
                text_rect = _text.get_rect(center=middle)
                self.screen.blit(_text, text_rect)

        for event in events:
            if(event.type == pygame.MOUSEBUTTONDOWN):
                mouse_pos = pygame.mouse.get_pos()
                self.evaluate_response(mouse_pos)
        
        if(len(self.current_response) >= len(self.current_sequence)):
            self.evaluate_user_sequence()
            self.run_state = SPAN_STATE.FEEDBACK
            self.timer = 0
    
    def feedback_screen(self):
        self.screen.fill(self.background_color)
        _text = self.font1.render(self.feedback_text, True, pygame.Color('black'))
        text_rect = _text.get_rect(center=self.middle_position)
        self.screen.blit(_text, text_rect)

        if(self.timer > 1.0):
            self.timer = 0
            self.run_state = SPAN_STATE.GENERATE_SEQUENCE

    def end_screen(self, events):
        self.screen.fill(self.background_color)
        print_multiline(self.screen, self.font1, self.summary, self.middle_position, 32, pygame.Color('black'), True)

        for event in events:
            if(event.type == pygame.KEYDOWN):
                return True

    def generate_sequence_screen(self):
        self.trial_counter += 1

        if(self.trial_counter > total_trials):
            self.run_state = SPAN_STATE.END
            self.generate_summary()
            return
        
        self.current_sequence_len = np.clip(self.current_sequence_len, 1, len(self.graphene_map))
        self.current_sequence = random.sample(list(self.graphene_map.keys()), self.current_sequence_len)
        self.current_sequence_index = 0
        self.timer = 0
        self.run_state = SPAN_STATE.STIMULUS

        if(self.target_type == StimulusType.COLOR):
            self.target_keys = list(self.graphene_map.keys())
            random.shuffle(self.target_keys)
        else:
            self.target_keys = sorted(list(self.graphene_map.keys()))

    def load_user_settings(self):
        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-span'
        task_directory = os.path.join(user_root, task_folder)

        if not os.path.exists(task_directory):
            os.makedirs(task_directory)

        settings_directory = os.path.join(task_directory, 'settings.json')

        if not os.path.exists(settings_directory):
            default_settings = {
                "initial_sequence_length": initial_sequence_length
            }
            with open(settings_directory, 'w') as f:
                json.dump(default_settings, f)

        with open(settings_directory, 'r') as f:
            user_settings = json.load(f)

        self.current_sequence_len = user_settings.get("initial_sequence_length", initial_sequence_length)

    def run(self):
        pygame.init()
        pygame.display.set_caption(self.task_name)
        screen_size = (config['screen']['width'], config['screen']['height'])
        self.screen = pygame.display.set_mode(screen_size)
        self.font1 = pygame.font.Font('freesansbold.ttf', 32)
        self.font2 = pygame.font.Font('freesansbold.ttf', 64)
        clock = pygame.time.Clock()
        self.middle_position = (self.screen.get_width() // 2, self.screen.get_height() // 2)

        self.graphene_map = graphene_map
        self.background_color = background_color

        
        num_pairs = len(self.graphene_map)
        width_per_target = self.screen.get_width() // num_pairs
        
        self.results = []

        if self.target_type in [StimulusType.LETTER, StimulusType.COLORED_LETTER]:
            self.target_middles = [(width_per_target * i + width_per_target // 2, self.screen.get_height() // 2) for i in range(num_pairs)]
        else:
            self.target_rects = []
            y = self.middle_position[1] - width_per_target // 2
            for i in range(num_pairs):
                x = width_per_target * i
                rect = pygame.Rect(x, y, width_per_target, width_per_target)
                self.target_rects.append(rect)
        
        self.current_sequence_len = initial_sequence_length
        self.load_user_settings()

        while True:
            clock.tick(60) # 60 Fps
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                
            self.timer += clock.get_time() / 1000.0  # seconds

            match self.run_state:
                case SPAN_STATE.START:
                    self.start_screen(events)
                case SPAN_STATE.GENERATE_SEQUENCE:
                    self.generate_sequence_screen()
                case SPAN_STATE.STIMULUS:
                    self.stimulus_screen()
                case SPAN_STATE.STIMULUS_GAP:
                    self.stimulus_gap_screen()
                case SPAN_STATE.RESPONSE_GAP:
                    self.response_gap_screen()
                case SPAN_STATE.RESPONSE:
                    self.response_screen(events)
                case SPAN_STATE.FEEDBACK:
                    self.feedback_screen()
                case SPAN_STATE.END:
                    has_quit = self.end_screen(events)
                    if(has_quit):
                        pygame.quit()
                        return

            pygame.display.flip()
 
    def save_user_settings(self):
        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-span'
        task_directory = os.path.join(user_root, task_folder)

        settings_directory = os.path.join(task_directory, 'settings.json')
        
        # Sometimes the value is NaN, need to check the issue root
        try:
            avg_final_sequence_length = np.mean([result['sequence_length'] for result in self.results]) 
            avg_final_sequence_length = np.clip(avg_final_sequence_length, 1, len(self.graphene_map))
            avg_final_sequence_length = int(round(avg_final_sequence_length))
        except Exception as e:
            print(f"Error converting avg_final_sequence_length to int: {e}")
            avg_final_sequence_length = initial_sequence_length  # fallback to initial value
        
        user_settings = {
            "initial_sequence_length": avg_final_sequence_length
        }
        
        with open(settings_directory, 'w') as f:
            json.dump(user_settings, f)

        return

    def log_user_results(self):
        final_average_sequence_length = np.mean([result['sequence_length'] for result in self.results])
        final_average_accuracy = np.mean([result['is_correct'] for result in self.results])
        
        mean_correct_seq_len = np.mean([result['sequence_length'] for result in self.results if result['is_correct']])
        median_correct_seq_len = np.median([result['sequence_length'] for result in self.results if result['is_correct']])
        mean_time_to_answer = np.mean([result['time_to_answer'] for result in self.results])

        time_of_finish = time.strftime("%Y-%m-%d %H:%M:%S")

        new_row = {
            "user_id": self.user_id,
            "session_number": 1,
            "mode": self.mode,
            "stimulus_type": self.stimulus_name,
            "target_type": self.target_name,
            "total_trials": total_trials,
            "mean_sequence_length": final_average_sequence_length,
            "mean_accuracy": final_average_accuracy,
            "mean_correct_sequence_length": mean_correct_seq_len,
            "median_correct_sequence_length": median_correct_seq_len,
            "mean_time_to_answer": mean_time_to_answer,
            "time_of_finish" : time_of_finish
        }

        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-span'
        task_directory = os.path.join(user_root, task_folder)
        csv_path = os.path.join(task_directory, 'results.csv')

        if(os.path.exists(csv_path)):
            df = pd.read_csv(csv_path)
            new_row['session_number'] = df['session_number'].max() + 1
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])
        
        df.to_csv(csv_path, index=False)

        return
        

def run_span(user_id, mode="early"):
    runner = SpanRunner(user_id, mode=mode) # type: ignore
    runner.run()
    runner.save_user_settings()
    runner.log_user_results()


def run_early_span(user_id):
    run_span(user_id, mode="early")

def run_late_span(user_id):
    run_span(user_id, mode="late")

def run_advanced_span(user_id):
    run_span(user_id, mode="advanced")

def run_backward_span(user_id):
    return # Not implemented yet
    run_span(user_id, mode="backward")