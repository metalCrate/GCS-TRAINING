import pygame
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
