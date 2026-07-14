import pygame
from sqlalchemy import case
import yaml
from src.utils import config
from src.colors import graphene_map, background_color
from src.pygame_utils import print_multiline, color_by_similarity
from enum import Enum
import random

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

def start_screen(screen: pygame.Surface, font: pygame.font.Font, events: list[pygame.event.Event], estimated_time_min: float, estimated_time_max: float):
    screen.fill(background_color)
    _text = [
        ""
        "Early Delayed Match to Sample",
        "",
        "You will be shown letters in their corresponding colors.",
        "After a delay, you will be asked to select the correct color from 2 options.",
        "With each successful trial, the task will become more difficult.",
        "With each failed trial, the task will become easier.",
        "",
        "Choose left with left arrow key <--, and right with right arrow key -->",
        "",
        f"The task will take between {estimated_time_min // 60:.0f}m {estimated_time_min % 60:.0f}s and {estimated_time_max // 60:.0f}m {estimated_time_max % 60:.0f}s.",
        "",
        "Press any key to start."
    ]

    position = (screen.get_width() // 2, screen.get_height() // 3)
    print_multiline(screen, font, _text, position, 32, pygame.Color('black'), True)
    run_state = DMTS_STATE.START
    for event in events:
            if(event.type == pygame.KEYDOWN):
                run_state = DMTS_STATE.GENERATE_STIMULUS

    return run_state

def evaluate_response(is_left_correct: bool, events: list[pygame.event.Event], target_graphene: str):
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                return is_left_correct
            elif event.key == pygame.K_RIGHT:
                return not is_left_correct
    return None

def run_early_dmts():

    def generate_run_summary():
        average_correct_time = 0
        accuracy = 0
        for result in results:
            if result['correct']:
                average_correct_time += result['time_to_response']
                accuracy += 1

        average_correct_time /= accuracy if accuracy > 0 else -1
        accuracy = accuracy / len(results) if len(results) > 0 else -1

        best_letter = None
        worst_letter = None

        letter_avg_sim = {}

        for result in results:
            letter = result['target_graphene']
            if letter not in letter_avg_sim:
                letter_avg_sim[letter] = []
            letter_avg_sim[letter].append(result['similarity'])
        
        letter_avg_sim = {letter: sum(sim_list) / len(sim_list) for letter, sim_list in letter_avg_sim.items()}

        best_letter = max(letter_avg_sim, key=letter_avg_sim.get)
        worst_letter = min(letter_avg_sim, key=letter_avg_sim.get)

        average_difficulty = sum(similarity_dict.values()) / len(similarity_dict) if len(similarity_dict) > 0 else -1
        
        summary = [
            f"Average time to correct response: {average_correct_time:.2f}s",
            f"Accuracy: {accuracy * 100:.2f}%",
            f"Final average difficulty (similarity): {average_difficulty:.2f}",
            f"Best letter: {best_letter} (avg similarity: {letter_avg_sim[best_letter]:.2f})",
            f"Worst letter: {worst_letter} (avg similarity: {letter_avg_sim[worst_letter]:.2f})"
        ]

        # SAVE average_difficulty for the next run
        return summary

    pygame.init()
    pygame.display.set_caption("Passive Drill")
    screen_size = (config['screen']['width'], config['screen']['height'])
    screen = pygame.display.set_mode(screen_size)
    font1 = pygame.font.Font('freesansbold.ttf', 32)
    font2 = pygame.font.Font('freesansbold.ttf', 64)
    clock = pygame.time.Clock()
    middle_position = (screen.get_width() // 2, screen.get_height() // 2)
    minimum_time = (stimulus_duration + delay_duration) * total_trials
    maximum_time = (stimulus_duration + delay_duration + response_duration) * total_trials
    state = DMTS_STATE.START
    timer = 0

    square_size = 50
    half_square_size = square_size // 2
    left_middle = (middle_position[0] - square_size, middle_position[1])
    right_middle = (middle_position[0] + square_size, middle_position[1])
    square_left_rect = pygame.Rect(left_middle[0] - half_square_size, left_middle[1] - half_square_size, square_size, square_size)
    square_right_rect = pygame.Rect(right_middle[0] - half_square_size, right_middle[1] - half_square_size, square_size, square_size)

    is_left_correct = False
    graphenes = list(graphene_map.keys())
    target_graphene = None
    foil_color = pygame.Color('black')

    results = []
    feedback_text = ""
    trial_counter = 0
    summary = []
    average_difficulty = -1 
    while True:
        clock.tick(60)  # Limit the frame rate to 60 FPS
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        timer += clock.get_time() / 1000  # Increment timer by the time elapsed since the last frame in seconds


        match state:
            case DMTS_STATE.START:
                state = start_screen(screen, font1, events, minimum_time, maximum_time)
            case DMTS_STATE.GENERATE_STIMULUS:
                trial_counter += 1
                if(trial_counter > total_trials):
                    state = DMTS_STATE.END
                    summary = generate_run_summary()
                    continue
                is_left_correct = random.choice([True, False])
                target_graphene = random.choice(graphenes)
                similarity = similarity_dict[target_graphene]
                foil_color = color_by_similarity(graphene_map[target_graphene], similarity)
                timer = 0
                state = DMTS_STATE.STIMULUS
            case DMTS_STATE.STIMULUS:
                screen.fill(background_color)
                color = graphene_map[target_graphene]
                color = pygame.Color(color)
                text = font2.render(target_graphene, True, color)
                screen.blit(text, (middle_position[0] - text.get_width() // 2, middle_position[1] - text.get_height() // 2))

                if (timer > stimulus_duration):
                    timer = 0
                    state = DMTS_STATE.DELAY

            case DMTS_STATE.DELAY:
                screen.fill(background_color)

                if (timer > delay_duration):
                    timer = 0
                    state = DMTS_STATE.RESPONSE
                
            case DMTS_STATE.RESPONSE:
                screen.fill(background_color)
                color_l = graphene_map[target_graphene] if is_left_correct else foil_color
                color_r = foil_color if is_left_correct else graphene_map[target_graphene]
                color_l = pygame.Color(color_l)
                color_r = pygame.Color(color_r)

                pygame.draw.rect(screen, color_l, square_left_rect)
                pygame.draw.rect(screen, color_r, square_right_rect)

                response = evaluate_response(is_left_correct, events, target_graphene)
                if response is not None:
                    similarity = similarity_dict[target_graphene]
                    result = {
                        'target_graphene': target_graphene,
                        'response': 'left' if is_left_correct else 'right',
                        'correct': response,
                        'similarity': similarity,
                        'time_to_response': timer
                    }
                    results.append(result)
                    sim_delta = success_delta_similarity if response else failure_delta_similarity
                    similarity = adjust_similarity(similarity, sim_delta)
                    similarity_dict[target_graphene] = similarity
                    feedback_text = 'Correct' if response else 'Incorrect'
                    timer = 0
                    state = DMTS_STATE.FEEDBACK
                    continue

                if(timer > response_duration):
                    result = {
                        'target_graphene': target_graphene,
                        'response': None,
                        'correct': False,
                        'similarity': similarity_dict[target_graphene],
                        'time_to_response': timer
                    }
                    results.append(result)
                    timer = 0
                    state = DMTS_STATE.FEEDBACK
                    feedback_text = 'Out of time'
            
            
            case DMTS_STATE.FEEDBACK:
                screen.fill(background_color)
                text = font1.render(feedback_text, True, pygame.Color('black'))
                screen.blit(text, (middle_position[0] - text.get_width() // 2, middle_position[1] - text.get_height() // 2))
                if(timer > 1):
                    timer = 0
                    state = DMTS_STATE.GENERATE_STIMULUS
            case DMTS_STATE.END:
                screen.fill(background_color)
                print_multiline(screen, font1, summary, (screen.get_width() // 2, screen.get_height() // 3), 32, pygame.Color('black'), True)

        # Update the display
        pygame.display.flip()


if __name__ == "__main__":
    run_early_dmts()