import pygame
from src.utils import config
from src.colors import graphene_map, background_color
from src.pygame_utils import print_multiline, color_by_similarity
from enum import Enum
import random
import os
import json
import time
import pandas as pd
import numpy as np

nback_config = config['nback']

stimulus_duration = nback_config['stimulus_duration']
gap_duration = nback_config['gap_duration']
letter_chance = nback_config['letter_chance']
match_trial_chance = nback_config['match_trial_chance']
total_trials = nback_config['total_trials']
initial_n = nback_config['initial_n']
show_feedback = nback_config['show_feedback']
accuracy_to_progress = nback_config['accuracy_to_progress']

class NBACK_STATE(Enum):
    PREPARE_STIMULUS = -1
    START = 1
    STIMULUS = 2
    GAP = 3
    END = 4

class NBackRunner:
    def __init__(self, user_id):
        self.user_id = user_id

    def save_user_settings(self):
        user_root = f'data/users/{self.user_id}/'
        task_folder = 'nback'
        task_directory = os.path.join(user_root, task_folder)
        settings_directory = os.path.join(task_directory, 'settings.json')

        avg_accuracy = sum([1 for r in self.results if r['is_user_correct']]) / len(self.results) if self.results else 0

        increase_n = avg_accuracy >= accuracy_to_progress
        next_n = self.current_n + 1 if increase_n else self.current_n

        settings = {
            'next_n': next_n,
        }

        with open(settings_directory, 'w') as f:
            json.dump(settings, f)

        return
    
    def log_user_results(self):

        final_average_accuracy = sum([1 for r in self.results if r['is_user_correct']]) / len(self.results) if self.results else 0
        mean_time_to_answer = np.mean([r['time_to_respond'] for r in self.results]) if self.results else 0
        mean_grapheme_accuracy = (t := [r for r in self.results if r['stimulus_type'] == 'letter']) and (sum([1 for r in t if r['is_user_correct']]) / len(t)) or 0
        mean_color_accuracy = (t := [r for r in self.results if r['stimulus_type'] == 'color']) and (sum([1 for r in t if r['is_user_correct']]) / len(t)) or 0
        time_of_finish = time.strftime("%Y-%m-%d %H:%M:%S")

        new_row = {
            "user_id": self.user_id,
            "session_number": 1,
            "total_trials": total_trials,
            "num_correct" :1 ,
            "mean_accuracy": final_average_accuracy,
            "mean_grapheme_accuracy": mean_grapheme_accuracy,
            "mean_color_accuracy": mean_color_accuracy,
            "mean_time_to_answer": mean_time_to_answer,
            "time_of_finish" : time_of_finish
        }

        user_root = f'data/users/{self.user_id}/'
        task_folder = 'nback'
        task_directory = os.path.join(user_root, task_folder)
        
        csv_path = os.path.join(task_directory, 'results.csv')

        if (os.path.isfile(csv_path)):
            df = pd.read_csv(csv_path)
            new_row['session_number'] = df['session_number'].max() + 1
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_csv(csv_path, index=False)

        print(f"Results logged for user {self.user_id} in {csv_path}")

    def load_user_settings(self):
        user_root = f'data/users/{self.user_id}/'
        task_folder = 'nback'
        task_directory = os.path.join(user_root, task_folder)

        if not os.path.exists(task_directory):
            os.makedirs(task_directory)

        settings_directory = os.path.join(task_directory, 'settings.json')

        if not os.path.exists(settings_directory):
            default_settings = {
                'next_n': initial_n,
            }
            
            with open(settings_directory, 'w') as f:
                json.dump(default_settings, f)

        with open(settings_directory, 'r') as f:
            self.user_settings = json.load(f)
        
        self.current_n = self.user_settings.get('next_n', initial_n)

    def generate_trial_list(self):
        num_match_trials = round(total_trials * match_trial_chance)
        non_match_trials = total_trials - num_match_trials
        self.match_trials = [0] * non_match_trials + [1] * num_match_trials
        random.shuffle(self.match_trials)
        self.match_trials = [0] * self.current_n + self.match_trials # left pad with non matches

        grapheme_keys = list(graphene_map.keys())
        self.trial_list = [random.choice(grapheme_keys) for _ in range(len(self.match_trials))]
        self.trials_type = ['letter' if random.random() < letter_chance else 'color' for _ in range(len(self.match_trials))]
        # Ensure correct sequence of trials based on match/non-match conditions
        for i, this_key in enumerate(self.trial_list):
            is_a_match = self.match_trials[i]

            if is_a_match:
                self.trial_list[i] = self.trial_list[i - self.current_n] # shouldnt out of index due to left padding
            else:
                prev_key = self.trial_list[i - self.current_n]
                if(not prev_key == this_key):
                    continue
                else:
                    non_matching_keys = [k for k in grapheme_keys if not k == prev_key]
                    self.trial_list[i] = random.choice(non_matching_keys)

    def evaluate_response(self, user_response: bool):
        
        is_current_match = self.match_trials[self.current_trial_index] == 1
        is_user_correct = user_response == is_current_match

        self.feedback_text = "+" if is_user_correct else "-"
        result = {
            "trial_index": self.current_trial_index,
            "stimulus": self.trial_list[self.current_trial_index],
            "stimulus_type": self.trials_type[self.current_trial_index],
            "is_match": is_current_match,
            "user_response": user_response,
            "time_to_respond" : self.timer,
            "is_user_correct": is_user_correct
        }

        self.results.append(result)

        # Change to next state
        self.run_state = NBACK_STATE.GAP
        self.timer = 0
        self.current_trial_index += 1

    # States
    def start_screen(self, events):
        self.screen.fill(background_color)

        nback_word = (
            f"{self.current_n}th-Back" if self.current_n > 3
            else f"{self.current_n}rd-Back" if self.current_n == 3
            else f"{self.current_n}nd-Back" if self.current_n == 2
            else "previous"
        )

        _text = [
            "Synesthesia N-Back Task.",
            "",
            "You will be shown colored squares and letters.",
            "You are to press space if the current stimulus",
            f"corresponds to the {nback_word} stimulus.",
            "",
            "Press any key to start"
        ]
        _pos = (self.screen.get_width() // 2, self.screen.get_height() // 3)
        
        print_multiline(self.screen, self.font1, _text,_pos,32,pygame.Color('black'),)


        for event in events:
            if(event.type == pygame.KEYDOWN):
                self.run_state = NBACK_STATE.PREPARE_STIMULUS
                self.timer = 0
                return

    def generate_summary(self):
        accuracy = sum([1 for r in self.results if r['is_user_correct']]) / len(self.results) if self.results else 0
        accuracy_percentage = round(accuracy * 100, 1)

        self.summary = [
            "Summary.",
            "",
            "Average Accuracy: " + str(accuracy_percentage) + "%",
            f"Next session will have N = {self.current_n + 1 if accuracy >= accuracy_to_progress else self.current_n}"
        ]



    def prepare_stimulus_screen(self):
        self.run_state = NBACK_STATE.STIMULUS
        self.timer = 0
        
        if(self.current_trial_index >= self.total_trials):
            self.generate_summary()
            self.run_state = NBACK_STATE.END
            return

    def stimulus_screen(self, events):
        self.screen.fill(background_color)

        current_stimulus = self.trial_list[self.current_trial_index]
        
        is_letter = self.trials_type[self.current_trial_index] == 'letter'

        if is_letter:
            _text = self.font2.render(current_stimulus, True, pygame.Color('black'))
            t_rect = _text.get_rect()
            t_rect.center = self.middle_position
            self.screen.blit(_text, t_rect)
        else:
            color = graphene_map[current_stimulus]
            color = pygame.Color(color)
            
            square_size = 100
            square_rect = pygame.Rect(0, 0, square_size, square_size)
            square_rect.center = self.middle_position
            self.screen.fill(color, square_rect)


        if(self.timer > stimulus_duration):
            self.evaluate_response(user_response=False)
            return

        for event in events:
            if(event.type == pygame.KEYDOWN):
                if(event.key == pygame.K_SPACE):
                    self.evaluate_response(user_response=True)

    def gap_screen(self):
        self.screen.fill(background_color)


        if(show_feedback and self.current_trial_index > self.current_n):
            text = self.font1.render(self.feedback_text, True, pygame.Color('black'))
            text_rect = text.get_rect()
            text_rect.center = self.middle_position
            self.screen.blit(text, text_rect)

        if(self.timer > gap_duration):
            self.run_state = NBACK_STATE.PREPARE_STIMULUS
            self.timer = 0

    def end_screen(self, events):
        self.screen.fill(background_color)

        print_multiline(self.screen, self.font1, self.summary, self.middle_position, 32, pygame.Color('black'))

        for event in events:
            if(event.type == pygame.KEYDOWN):
                return True
        return False

    def run(self):
        pygame.init()
        pygame.display.set_caption("Synesthesia N-Back")

        screen_size = (config['screen']['width'], config['screen']['height'])
        self.screen = pygame.display.set_mode(screen_size)
        self.middle_position = (self.screen.get_width() // 2, self.screen.get_height() // 2)

        self.font1 = pygame.font.Font('freesansbold.ttf', 32)
        self.font2 = pygame.font.Font('freesansbold.ttf', 64)



        clock = pygame.time.Clock()
        
        self.current_n = initial_n
        self.run_state = NBACK_STATE.START
        self.current_trial_index = 0

        self.trial_list = [] # actual len will be total_trials + current_n due to left padding
        self.feedback_text = "No feedback"
        self.load_user_settings()
        self.generate_trial_list()

        self.total_trials = len(self.trial_list)
        self.timer = 0
        self.results = []
        self.summary = []
        while True:
            clock.tick(60)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.timer += clock.get_time() / 1000.0 # convert to seconds

            match self.run_state: 
                case NBACK_STATE.START:
                    self.start_screen(events)

                case NBACK_STATE.PREPARE_STIMULUS:
                    self.prepare_stimulus_screen()

                case NBACK_STATE.STIMULUS:
                    self.stimulus_screen(events)

                case NBACK_STATE.GAP:
                    self.gap_screen()
                    
                case NBACK_STATE.END:
                    has_quit = self.end_screen(events)
                    if(has_quit):
                        pygame.quit()
                        return

            pygame.display.flip()

def run_nback(user_id):
    runner = NBackRunner(user_id)
    runner.run()
    runner.save_user_settings()
    runner.log_user_results()