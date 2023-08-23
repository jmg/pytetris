import pygame
import numpy as np

pygame.init()

SQUARE_SIZE = 50
MAX_WIDTH = 10
MAX_HEIGHT = 20

surface = pygame.display.set_mode((SQUARE_SIZE * MAX_WIDTH, SQUARE_SIZE * MAX_HEIGHT))
clock = pygame.time.Clock()


class GameOverException(Exception):

    pass

class InvalidMoveException(Exception):

    pass


class EmptyState:

    value = 0
    color = (0,0,0)

class CurrentPieceState:

    value = 1
    color = (200,200,200)

class BoardPieceState:

    value = 2
    color = (0,0,255)

class InvalidMoveState:

    value = -1


class Piece:

    shift_y = 0
    shift_x = 0

    def __init__(self, shape):

        self.shape = shape


class RotateAllPiece(Piece):

    shift_y = -1
    shift_x = -1

    def rotate(self, x, y):

        return y, len(self.shape) - x - 1


class RotateMirrorPiece(Piece):

    def rotate(self, x, y):

        return y, x


class NoRotatePiece(Piece):

    def rotate(self, x, y):

        return x, y


class PieceGenerator:

    shapes = {
        0: RotateMirrorPiece([(0, 0), (1, 0), (1, 1), (2, 1)]),     # Z
        1: RotateAllPiece([(0, 0), (0, 1), (0, 2), (1, 2)]),        # L
        2: RotateMirrorPiece([(0, 0), (0, 1), (0, 2), (0, 3)]),     # I
        3: NoRotatePiece([(0, 0), (0, 1), (1, 0), (1, 1)]),         # O
        4: RotateAllPiece([(0, 0), (0, 1), (0, 2), (1, 1)]),        # T
        5: RotateAllPiece([(0, 0), (0, 1), (0, 2), (1, 0)]),        # J
    }

    @classmethod
    def generate_random_piece(cls, position, board_array):

        shape = np.random.randint(0, len(cls.shapes.values()))
        return cls.generate(shape, position, board_array)

    @classmethod
    def generate(cls, shape, position, board_array):

        x, y = position

        for px, py in cls.shapes[shape].shape:
            board_array[x+px][y+py] = CurrentPieceState.value

        return cls.shapes[shape]


class Board:

    board_array = np.zeros((MAX_WIDTH, MAX_HEIGHT))
    current_piece = None

    def generate_random_piece(self):

        position = (MAX_WIDTH / 2, 0)
        self.current_piece = PieceGenerator.generate_random_piece(position, self.board_array)

    def get_current_position(self):

        current_x = None
        current_y = None

        for i in range(MAX_WIDTH):
            for j in range(MAX_HEIGHT):
                if self.board_array[i][j] == CurrentPieceState.value:
                    current_x = i
                    current_y = j
                    break

            if current_x is not None and current_y is not None:
                break

        return current_x, current_y

    def rotate(self):

        new_array = self.board_array.copy()
        new_array[new_array == CurrentPieceState.value] = EmptyState.value

        current_x, current_y = self.get_current_position()

        current_x += self.current_piece.shift_x
        current_y += self.current_piece.shift_y

        rotated_piece = []
        for x, y in self.current_piece.shape:

            new_x, new_y = self.current_piece.rotate(x, y)
            rotated_piece.append((new_x, new_y))
            try:
                if new_array[current_x+new_x][current_y+new_y] == BoardPieceState.value or current_x+new_x > MAX_WIDTH or current_x+new_x < 0 or current_y+new_y > MAX_HEIGHT:
                    #can't rotate
                    return

                new_array[current_x+new_x][current_y+new_y] = CurrentPieceState.value
            except IndexError:
                return

        self.board_array = new_array
        self.current_piece.shape = rotated_piece

    def check_move(self, x, y):

        for i in range(MAX_WIDTH):
            for j in range(MAX_HEIGHT):
                if self.board_array[i][j] == CurrentPieceState.value:
                    try:
                        if i+x < 0 or i+x >= MAX_WIDTH or self.board_array[i+x][j+y] == BoardPieceState.value:
                            raise InvalidMoveException
                        elif j+y+1 >= MAX_HEIGHT:
                            return BoardPieceState.value
                        elif self.board_array[i+x][j+y+1] == BoardPieceState.value:
                            return BoardPieceState.value

                    except (InvalidMoveException, IndexError):
                        return InvalidMoveState.value

        return EmptyState.value

    def check_lines(self):

        for j in range(MAX_HEIGHT):
            if np.all(self.board_array[:, j] == BoardPieceState.value):
                self.board_array[:, 1:j+1] = self.board_array[:, 0:j]
                self.board_array[:, 0] = EmptyState.value

    def move(self, x, y, is_clock=False):

        move = self.check_move(x, y)
        if move == EmptyState.value:
            new_value = CurrentPieceState.value
        elif move == BoardPieceState.value:
            new_value = BoardPieceState.value
        else:
            return

        new_array = self.board_array.copy()
        new_array[new_array == CurrentPieceState.value] = EmptyState.value

        for i in range(MAX_WIDTH):
            for j in range(MAX_HEIGHT):
                if self.board_array[i][j] == CurrentPieceState.value:
                    try:
                        new_array[i+x][j+y] = new_value
                    except IndexError:
                        return

        self.board_array = new_array

        self.check_lines()

        if new_value == BoardPieceState.value:

            self.generate_random_piece()

            if self.check_move(0, 0) == BoardPieceState.value:
                if is_clock:
                    raise GameOverException


board = Board()
board.generate_random_piece()

time = 0
game_ended = False
SPEED = 1000
key_pressed = None

while True:

    surface.fill((0,0,0))

    for event in pygame.event.get():

        if event.type == pygame.KEYDOWN and not game_ended:
            key_pressed = event.key
            if event.key == pygame.K_SPACE:
                board.rotate()
            if event.key == pygame.K_DOWN:
                key_pressed = pygame.K_DOWN
            elif event.key == pygame.K_LEFT:
                board.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                board.move(1, 0)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                key_pressed = None

        elif event.type == pygame.QUIT:
            pygame.quit()
            quit()

    if key_pressed == pygame.K_DOWN:
        board.move(0, 1)

    for i in range(MAX_WIDTH):
        for j in range(MAX_HEIGHT):
            color = None
            if board.board_array[i][j] == CurrentPieceState.value:
                color = CurrentPieceState.color
            elif board.board_array[i][j] == BoardPieceState.value:
                color = BoardPieceState.color

            if color:
                pygame.draw.rect(surface, color, pygame.Rect(i*SQUARE_SIZE, j*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    pygame.display.update()
    clock.tick(25)

    time += 100

    if time % SPEED == 0:
        try:
            if not game_ended:
                board.move(0, 1, is_clock=True)
        except GameOverException:
            game_ended = True
            print("Game Over")