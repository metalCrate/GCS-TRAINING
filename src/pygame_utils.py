import pygame
import numpy as np

def random_unit_vector_3d():
    vec = np.random.randn(3)
    return (vec / np.linalg.norm(vec)).tolist()

def color_by_similarity(color1 : pygame.Color | list[int], similarity: float) -> pygame.Color:
    vec = random_unit_vector_3d()

    if isinstance(color1, pygame.Color):
        color1_vec = np.array([color1.r, color1.g, color1.b])
    else:
        color1_vec = np.array(color1)

    for i in range(3):
        _change = vec[i] * (1 - similarity) * 255

        to_edge = 255 - color1_vec[i] if _change > 0 else color1_vec[i]

        if abs(_change) > abs(to_edge) & to_edge < 255//2:
            _change = -_change

        new_value = color1_vec[i] + _change
        new_value = np.clip(new_value, 0, 255)
        color1_vec[i] = new_value
    
    return pygame.Color(int(color1_vec[0]), int(color1_vec[1]), int(color1_vec[2]))

def print_multiline(
        surface: pygame.Surface,
        font : pygame.font.Font,
        lines: list[str],
        position: tuple,
        fontsize: int,
        color: pygame.Color,
        centered: bool = False):
    
    for i in range(len(lines)):
        _text = lines[i]
        expected_width = font.size(_text)[0]
        if centered:
            _position = (surface.get_width() // 2 - expected_width // 2, position[1] + i * fontsize)
        else:
            _position = (position[0], position[1] + i * fontsize)
        label = font.render(_text, True, color)
        surface.blit(label, _position)
