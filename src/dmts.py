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

def adjust_similarity(current, delta):
    if delta > 0:
        return current + (1-current) * delta
    else:
        return current * (1 - abs(delta))

# EARLY DELAYED MATCH TO SAMPLE (edmts)

edmts_drill_config = config['early-dmts']

stimulus_duration = edmts_drill_config['stimulus_duration']
delay_duration = edmts_drill_config['delay_duration']
response_duration = edmts_drill_config['response_duration']
initial_fake_similarity = edmts_drill_config['initial_fake_similarity']
success_delta_similarity = edmts_drill_config['success_delta_similarity']
failure_delta_similarity = edmts_drill_config['failure_delta_similarity']
total_trials = edmts_drill_config['total_trials']

similarity_dict = {graphene: initial_fake_similarity for graphene in graphene_map.keys()}

# Change to load for user file

class DMTS_STATE(Enum):
    GENERATE_STIMULUS = -1
    START = 0
    STIMULUS = 1
    DELAY = 2
    RESPONSE = 3
    FEEDBACK = 4
    END = 5

class DMTSRunner:
    def __init__(self, user_id, mode :str = 'early'):
        self.user_id = user_id
        self.mode = mode
        
        self.run_state = DMTS_STATE.START
        self.timer = 0
        self.trial_counter = 0
        self.results = []
        self.feedback_text = ""
        self.target_graphene = None
        self.is_left_correct = False
        self.estimated_time_min = -1
        self.estimated_time_max = -1
        self.screen : pygame.Surface = None
        self.font1 : pygame.font.Font = None
        self.graphenes = list(graphene_map.keys())
        self.color_graphenes = True if self.mode == 'early' else False
        self.has_finished = False

    def start_screen(self, events):
        self.screen.fill(background_color)
        _text = [
            ""
            "Early Delayed Match to Sample" if self.mode == 'early' else "Late Delayed Match to Sample",
            "",
            "You will be shown letters in their corresponding colors." if self.color_graphenes else "You will be shown letters in black.",
            "After a delay, you will be asked to select the correct color from 2 options." if self.color_graphenes else "After a delay, you will be asked to select the corresponding color from 2 options.",
            "With each successful trial, the task will become more difficult.",
            "With each failed trial, the task will become easier.",
            "",
            "Choose left with left arrow key <--, and right with right arrow key -->",
            "",
            f"The task will take between {self.estimated_time_min // 60:.0f}m {self.estimated_time_min % 60:.0f}s and {self.estimated_time_max // 60:.0f}m {self.estimated_time_max % 60:.0f}s.",
            "",
            "Press any key to start."
        ]

        position = (self.screen.get_width() // 2, self.screen.get_height() // 3)
        print_multiline(self.screen, self.font1, _text, position, 32, pygame.Color('black'), True)
        run_state = DMTS_STATE.START
        for event in events:
                if(event.type == pygame.KEYDOWN):
                    run_state = DMTS_STATE.GENERATE_STIMULUS

        self.run_state = run_state

    def generate_stimulus_screen(self):
        self.trial_counter += 1
        if(self.trial_counter > total_trials):
            self.run_state = DMTS_STATE.END
            self.generate_summary()
            return
        self.is_left_correct = random.choice([True, False])
        self.target_graphene = random.choice(self.graphenes)
        similarity = self.similarity_dict[self.target_graphene]
        self.foil_color = color_by_similarity(graphene_map[self.target_graphene], similarity)
        self.timer = 0
        self.run_state = DMTS_STATE.STIMULUS

    def stimulus_screen(self):
        self.screen.fill(background_color)

        color = graphene_map[self.target_graphene] if self.color_graphenes else (0, 0, 0)
        color = pygame.Color(color)
        text = self.font2.render(self.target_graphene, True, color)
        self.screen.blit(text, (self.middle_position[0] - text.get_width() // 2, self.middle_position[1] - text.get_height() // 2))

        if(self.timer > stimulus_duration):
            self.timer = 0
            self.run_state = DMTS_STATE.DELAY

    def delay_screen(self):
        self.screen.fill(background_color)

        if(self.timer > delay_duration):
            self.timer = 0
            self.run_state = DMTS_STATE.RESPONSE

    def response_screen(self, events):

        self.screen.fill(background_color)
        color_l = graphene_map[self.target_graphene] if self.is_left_correct else self.foil_color
        color_r = self.foil_color if self.is_left_correct else graphene_map[self.target_graphene]
        color_l = pygame.Color(color_l)
        color_r = pygame.Color(color_r)

        pygame.draw.rect(self.screen, color_l, self.square_left_rect)
        pygame.draw.rect(self.screen, color_r, self.square_right_rect)
        
        response = evaluate_response(self.is_left_correct, events, self.target_graphene)

        if response is not None:
            similarity = self.similarity_dict[self.target_graphene]
            result = {
                'target_graphene': self.target_graphene,
                'response': 'left' if self.is_left_correct else 'right',
                'correct': response,
                'similarity': similarity,
                'time_to_response': self.timer
            }
            self.results.append(result)
            sim_delta = success_delta_similarity if response else failure_delta_similarity
            similarity = adjust_similarity(similarity, sim_delta)
            self.similarity_dict[self.target_graphene] = similarity
            self.feedback_text = 'Correct' if response else 'Incorrect'
            self.timer = 0
            self.run_state = DMTS_STATE.FEEDBACK
            return
        
        if (self.timer > response_duration):
            result = {
                'target_graphene': self.target_graphene,
                'response': None,
                'correct': False,
                'similarity': self.similarity_dict[self.target_graphene],
                'time_to_response': self.timer
            }
            self.results.append(result)
            self.timer = 0
            self.run_state = DMTS_STATE.FEEDBACK
            self.feedback_text = 'Out of time'
        
    def feedback_screen(self):
        self.screen.fill(background_color)
        text = self.font1.render(self.feedback_text, True, pygame.Color('black'))
        self.screen.blit(text, (self.middle_position[0] - text.get_width() // 2, self.middle_position[1] - text.get_height() // 2))
        if(self.timer > 1):
            self.timer = 0
            self.run_state = DMTS_STATE.GENERATE_STIMULUS

    def end_screen(self, events):
        self.screen.fill(background_color)
        print_multiline(self.screen, self.font1, self.summary, (self.screen.get_width() // 2, self.screen.get_height() // 3), 32, pygame.Color('black'), True)
        
        for event in events:
            if(event.type == pygame.KEYDOWN):
                pygame.quit()
                return True
            
        return False

    def generate_summary(self):
        self.has_finished = True
        average_correct_time = 0
        accuracy = 0
        for result in self.results:
            if result['correct']:
                average_correct_time += result['time_to_response']
                accuracy += 1

        average_correct_time /= accuracy if accuracy > 0 else -1
        accuracy = accuracy / len(self.results) if len(self.results) > 0 else -1

        best_letter = None
        worst_letter = None

        letter_avg_sim = {}

        for result in self.results:
            letter = result['target_graphene']
            if letter not in letter_avg_sim:
                letter_avg_sim[letter] = []
            letter_avg_sim[letter].append(result['similarity'])
        
        letter_avg_sim = {letter: sum(sim_list) / len(sim_list) for letter, sim_list in letter_avg_sim.items()}

        best_letter = max(letter_avg_sim, key=letter_avg_sim.get)
        worst_letter = min(letter_avg_sim, key=letter_avg_sim.get)

        average_difficulty = sum(self.similarity_dict.values()) / len(self.similarity_dict) if len(self.similarity_dict) > 0 else -1
        
        self.summary = [
            f"Average time to correct response: {average_correct_time:.2f}s",
            f"Accuracy: {accuracy * 100:.2f}%",
            f"Final average difficulty (similarity): {average_difficulty:.2f}",
            f"Best letter: {best_letter} (avg similarity: {letter_avg_sim[best_letter]:.2f})",
            f"Worst letter: {worst_letter} (avg similarity: {letter_avg_sim[worst_letter]:.2f})"
            "",
            "Press any key to exit."
        ]

        # SAVE average_difficulty for the next run

    def load_user_settings(self):
        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-dmts'
        task_directory = os.path.join(user_root, task_folder)
 
           
        if(not os.path.exists(task_directory)):
            os.makedirs(task_directory, exist_ok=True) # Create path if doesnt exist
        
        
        settings_directory = os.path.join(task_directory, 'settings.json')    

        if(not os.path.isfile(settings_directory)):
            # Create default settings file
            default_settings = {'start_similarity': initial_fake_similarity}
            with open(settings_directory, 'w') as f:
                json.dump(default_settings, f)

        with open(settings_directory, 'r') as f:
            settings = json.load(f)
        
        start_similarity = settings.get('start_similarity', initial_fake_similarity)
        for graphene in self.similarity_dict.keys():
            self.similarity_dict[graphene] = start_similarity

    def save_user_settings(self):
        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-dmts'
        task_directory = os.path.join(user_root, task_folder)
        
        settings_directory = os.path.join(task_directory, 'settings.json')

        average_difficulty = sum(self.similarity_dict.values()) / len(self.similarity_dict) if len(self.similarity_dict) > 0 else initial_fake_similarity
        settings = {'start_similarity': average_difficulty}
        with open(settings_directory, 'w') as f:
            json.dump(settings, f)

        return
    
    def log_user_results(self):
        
        final_average_difficulty = (
            sum(self.similarity_dict.values()) / len(self.similarity_dict)
            if len(self.similarity_dict) > 0 
            else initial_fake_similarity
        )
        
        average_time_to_respond = (t := [r['time_to_response'] for r in self.results if r['response'] is not None]) and sum(t)/len(t) or None
        average_time_to_correct_response = (t := [r['time_to_response'] for r in self.results if r['correct']]) and sum(t)/len(t) or None
        accuracy = (t := [r['correct'] for r in self.results]) and sum(t)/len(t) or None
        response_percent = (t := [r['response'] for r in self.results]) and sum(1 for x in t if x is not None)/len(t) or None
        time_of_finish = time.strftime("%Y-%m-%d %H:%M:%S")
        
        new_row = {
            'user_id': self.user_id,
            'session_number': 1,
            'mode': self.mode,
            'final_average_difficulty': final_average_difficulty,
            'average_time_to_respond': average_time_to_respond,
            'average_time_to_correct_response': average_time_to_correct_response,
            'accuracy': accuracy,
            'response_percent': response_percent,
            'time_of_finish': time_of_finish
        }
        
        user_root = f'data/users/{self.user_id}/'
        task_folder = f'{self.mode}-dmts'
        task_directory = os.path.join(user_root, task_folder)
        
        csv_path = os.path.join(task_directory, 'results.csv')

        if(os.path.isfile(csv_path)):
            df = pd.read_csv(csv_path)
            new_row['session_number'] = df['session_number'].max() + 1
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_csv(csv_path, index=False)



    def run(self):
        pygame.init()
        pygame.display.set_caption("Early Delayed Match to Sample")
        screen_size = (config['screen']['width'], config['screen']['height'])
        self.screen = pygame.display.set_mode(screen_size)
        self.font1 = pygame.font.Font('freesansbold.ttf', 32)
        self.font2 = pygame.font.Font('freesansbold.ttf', 64)
        clock = pygame.time.Clock()
        self.middle_position = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        self.estimated_time_min = (stimulus_duration + delay_duration) * total_trials
        self.estimated_time_max = (stimulus_duration + delay_duration + response_duration) * total_trials

        middle_position = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        square_size = 50
        half_square_size = square_size // 2
        left_middle = (middle_position[0] - square_size, middle_position[1])
        right_middle = (middle_position[0] + square_size, middle_position[1])
        
        self.square_left_rect = pygame.Rect(left_middle[0] - half_square_size, left_middle[1] - half_square_size, square_size, square_size)
        self.square_right_rect = pygame.Rect(right_middle[0] - half_square_size, right_middle[1] - half_square_size, square_size, square_size)

        self.similarity_dict = {graphene: initial_fake_similarity for graphene in graphene_map.keys()}

        self.load_user_settings()

        while True:
            clock.tick(60)  # Limit the frame rate to 60 FPS
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.timer += clock.get_time() / 1000  # Increment timer by the time elapsed since the last frame in seconds

            match self.run_state:
                case DMTS_STATE.START:
                    self.start_screen(events)
                case DMTS_STATE.GENERATE_STIMULUS:
                    self.generate_stimulus_screen()
                case DMTS_STATE.STIMULUS:
                    self.stimulus_screen()
                case DMTS_STATE.DELAY:
                    self.delay_screen()
                case DMTS_STATE.RESPONSE:
                    self.response_screen(events)
                case DMTS_STATE.FEEDBACK:
                    self.feedback_screen()
                case DMTS_STATE.END:
                    has_quit = self.end_screen(events)
                    if(has_quit):
                        pygame.quit()
                        return
            # Update the display
            pygame.display.flip()

def evaluate_response(is_left_correct: bool, events: list[pygame.event.Event], target_graphene: str):
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                return is_left_correct
            elif event.key == pygame.K_RIGHT:
                return not is_left_correct
    return None

def run_early_dmts(user_id=None):
    runner = DMTSRunner(user_id, mode='early')
    runner.run()
    runner.save_user_settings()
    runner.log_user_results()
def run_late_dmts(user_id=None):
    runner = DMTSRunner(user_id, mode='late')
    runner.run()
    runner.save_user_settings()
    runner.log_user_results()
if __name__ == "__main__":
    run_early_dmts()