import pygame
import random
import sys
import time

class Tetris:
    def __init__(self, width=10, height=20):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.new_piece()

    def new_piece(self):
        shapes = [
            [[1, 1, 1, 1]],  # I
            [[1, 1], [1, 1]],  # O
            [[0, 1, 0], [1, 1, 1]],  # T
            [[0, 1, 1], [1, 1, 0]],  # S
            [[1, 1, 0], [0, 1, 1]],  # Z
            [[1, 0, 0], [1, 1, 1]],  # J
            [[0, 0, 1], [1, 1, 1]]   # L
        ]

        self.current_piece = random.choice(shapes)
        self.piece_x = self.width // 2 - len(self.current_piece[0]) // 2
        self.piece_y = 0

        if not self.is_valid_position():
            self.game_over = True

    def rotate_piece(self):
        rotated = [[self.current_piece[y][x] 
                  for y in range(len(self.current_piece)-1, -1, -1)] 
                  for x in range(len(self.current_piece[0]))]

        old_piece = self.current_piece
        self.current_piece = rotated

        if not self.is_valid_position():
            self.current_piece = old_piece

    def is_valid_position(self, x_offset=0, y_offset=0):
        for y in range(len(self.current_piece)):
            for x in range(len(self.current_piece[0])):
                if self.current_piece[y][x]:
                    pos_x, pos_y = self.piece_x + x + x_offset, self.piece_y + y + y_offset

                    if (pos_x < 0 or pos_x >= self.width or 
                        pos_y >= self.height or 
                        (pos_y >= 0 and self.board[pos_y][pos_x])):
                        return False
        return True

    def move(self, dx, dy):
        if not self.paused and not self.game_over and self.is_valid_position(x_offset=dx, y_offset=dy):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False

    def drop(self):
        if not self.paused and not self.game_over and self.move(0, 1):
            return True

        if self.paused or self.game_over:
            return False

        for y in range(len(self.current_piece)):
            for x in range(len(self.current_piece[0])):
                if self.current_piece[y][x]:
                    if 0 <= self.piece_y + y < self.height:
                        self.board[self.piece_y + y][self.piece_x + x] = 1

        self.clear_lines()
        self.new_piece()
        return False

    def clear_lines(self):
        lines_to_clear = []
        for y in range(self.height):
            if all(self.board[y]):
                lines_to_clear.append(y)

        for line in lines_to_clear:
            del self.board[line]
            self.board.insert(0, [0 for _ in range(self.width)])

        cleared = len(lines_to_clear)
        if cleared > 0:
            self.lines_cleared += cleared
            self.score += [0, 100, 300, 500, 800][min(cleared, 4)] * self.level
            self.level = self.lines_cleared // 10 + 1

    def draw(self, screen, cell_size=30, padding=20):
        colors = [
            (40, 40, 60),      # Пустая клетка
            (255, 0, 0),       # Красный
            (255, 255, 0),     # Желтый
            (128, 0, 128),     # Фиолетовый
            (0, 255, 0),       # Зеленый
            (255, 165, 0),     # Оранжевый
            (0, 0, 255),       # Синий
            (0, 255, 255)      # Голубой
        ]

        # Рисуем фон
        screen.fill((40, 40, 60))

        # Рисуем сетку
        for y in range(self.height):
            for x in range(self.width):
                color_idx = self.board[y][x]
                rect = pygame.Rect(
                    padding + x * cell_size,
                    padding + y * cell_size,
                    cell_size, cell_size
                )
                pygame.draw.rect(screen, colors[color_idx], rect)
                pygame.draw.rect(screen, (70, 70, 90), rect, 1)

        # Рисуем текущую фигуру
        if not self.game_over:
            for y in range(len(self.current_piece)):
                for x in range(len(self.current_piece[0])):
                    if self.current_piece[y][x]:
                        rect = pygame.Rect(
                            padding + (self.piece_x + x) * cell_size,
                            padding + (self.piece_y + y) * cell_size,
                            cell_size, cell_size
                        )
                        pygame.draw.rect(screen, colors[1], rect)
                        pygame.draw.rect(screen, (70, 70, 90), rect, 1)

        # Рисуем информацию о игре
        font = pygame.font.SysFont(None, 36)
        status = "🟢 Играем" if not self.paused and not self.game_over else \
                 "⏸ Пауза" if self.paused else \
                 "🔴 Игра окончена"

        texts = [
            f"Счет: {self.score}",
            f"Уровень: {self.level}",
            f"Линий: {self.lines_cleared}",
            f"Статус: {status}"
        ]

        for i, text in enumerate(texts):
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (padding, padding + self.height * cell_size + 10 + i * 35))

class TetrisApp:
    def __init__(self, width=10, height=20):
        pygame.init()
        self.cell_size = 30
        self.padding = 20
        self.screen_width = width * self.cell_size + self.padding * 2
        self.screen_height = height * self.cell_size + self.padding * 2 + 150
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Тетрис")

        self.tetris = Tetris(width, height)
        self.last_drop_time = time.time()
        self.drop_interval = 0.8  # Интервал падения в секундах

        self.clock = pygame.time.Clock()
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.tetris.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.tetris.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    self.tetris.move(0, 1)
                elif event.key == pygame.K_UP:
                    self.tetris.rotate_piece()
                elif event.key == pygame.K_SPACE:
                    while self.tetris.drop():
                        pass
                elif event.key == pygame.K_p:
                    self.tetris.paused = not self.tetris.paused
                elif event.key == pygame.K_r:
                    self.tetris.reset()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        current_time = time.time()
        if current_time - self.last_drop_time > self.drop_interval:
            self.tetris.drop()
            self.last_drop_time = current_time

    def run(self):
        while self.running:
            self.handle_events()

            if not self.tetris.paused and not self.tetris.game_over:
                self.update()

            self.tetris.draw(self.screen, self.cell_size, self.padding)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = TetrisApp()
    app.run()
