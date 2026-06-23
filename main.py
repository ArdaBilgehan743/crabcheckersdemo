from __future__ import annotations

import math
import random
import sys
from collections import Counter
from dataclasses import dataclass

import pygame

from crabcheckers.ai import choose_move, player_label
from crabcheckers.content import CHARACTERS, MODIFIERS, STAKES, get_character, get_stake
from crabcheckers.rules import (
    BOARD_SIZE,
    DIRS,
    EMPTY,
    Move,
    PLAYER_A,
    PLAYER_B,
    START_BOARD,
    apply_move,
    check_winner,
    compute_destination,
    legal_destinations,
    legal_moves,
    is_repetition_draw,
    move_for_destination,
    move_notation,
    opponent,
    position_key,
    terminal_result,
)


CELL_SIZE = 72
BOARD_PIXELS = CELL_SIZE * BOARD_SIZE
LEFT_PANEL = 260
RIGHT_PANEL = 330
MARGIN = 24
BOARD_X = LEFT_PANEL + MARGIN * 2
BOARD_Y = 122
WINDOW_WIDTH = LEFT_PANEL + BOARD_PIXELS + RIGHT_PANEL + MARGIN * 4
WINDOW_HEIGHT = 720
FPS = 60

BG = (236, 224, 202)
INK = (37, 32, 28)
MUTED = (103, 91, 78)
PANEL = (249, 241, 224)
PANEL_DARK = (219, 199, 167)
BOARD_LIGHT = (235, 198, 166)
BOARD_DARK = (194, 123, 104)
GRID = (85, 55, 46)
A_COLOR = (210, 72, 69)
B_COLOR = (68, 92, 198)
GOLD = (224, 170, 62)
GREEN = (72, 150, 92)
BAD = (196, 62, 62)
WHITE = (255, 250, 239)


@dataclass(slots=True)
class Button:
    key: str
    rect: pygame.Rect
    label: str
    sublabel: str = ""
    selected: bool = False
    enabled: bool = True


@dataclass(slots=True)
class Snapshot:
    board: tuple[str, ...]
    current_player: str
    position_counts: Counter
    move_log: list[str]
    result: str | None
    status: str


@dataclass(slots=True)
class Animation:
    player: str
    start: tuple[int, int]
    end: tuple[int, int]
    progress: float = 0.0
    duration: float = 0.18


class SoundEffects:
    def __init__(self) -> None:
        self.enabled = True
        self.available = False
        self.move_sound = None
        self.invalid_sound = None
        self.win_sound = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.move_sound = self._tone(523, 0.06, 0.18)
            self.invalid_sound = self._tone(140, 0.08, 0.20)
            self.win_sound = self._tone(784, 0.14, 0.16)
            self.available = True
        except pygame.error:
            self.available = False

    def _tone(self, freq: int, seconds: float, volume: float) -> pygame.mixer.Sound:
        sample_rate = 22050
        count = int(sample_rate * seconds)
        samples = bytearray()
        for i in range(count):
            wave = math.sin(2 * math.pi * freq * i / sample_rate)
            envelope = 1 - (i / count)
            value = int(wave * envelope * volume * 32767)
            samples.extend(value.to_bytes(2, byteorder="little", signed=True))
        return pygame.mixer.Sound(buffer=bytes(samples))

    def play(self, name: str) -> None:
        if not self.enabled or not self.available:
            return
        sound = {
            "move": self.move_sound,
            "invalid": self.invalid_sound,
            "win": self.win_sound,
        }.get(name)
        if sound:
            sound.play()


class CrabCheckersApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Crab Checkers")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("arial", 44, bold=True)
        self.font_big = pygame.font.SysFont("arial", 30, bold=True)
        self.font = pygame.font.SysFont("arial", 22)
        self.font_small = pygame.font.SysFont("arial", 17)
        self.font_tiny = pygame.font.SysFont("arial", 14)
        self.rng = random.Random()
        self.sound = SoundEffects()

        self.state = "menu"
        self.mode = "ai"
        self.stake_key = "mid"
        self.human_player = PLAYER_A
        self.ai_player = PLAYER_B
        self.characters = {
            PLAYER_A: CHARACTERS[0].key,
            PLAYER_B: CHARACTERS[1].key,
        }
        self.selected_menu_side = PLAYER_A
        self.menu_buttons: list[Button] = []
        self.game_buttons: list[Button] = []
        self.arrow_buttons: dict[str, pygame.Rect] = {}

        self.board = START_BOARD
        self.current_player = PLAYER_A
        self.selected: tuple[int, int] | None = None
        self.keyboard_cursor = (0, 0)
        self.drag_start: tuple[int, int] | None = None
        self.drag_pos: tuple[int, int] | None = None
        self.move_log: list[str] = []
        self.undo_stack: list[Snapshot] = []
        self.position_counts: Counter = Counter()
        self.result: str | None = None
        self.status = "Choose your table."
        self.flash_message = ""
        self.flash_timer = 0.0
        self.hint_move: Move | None = None
        self.animation: Animation | None = None
        self.ai_delay = 0.0
        self.reset_game()

    def reset_game(self) -> None:
        self.board = START_BOARD
        self.current_player = PLAYER_A
        self.ai_player = opponent(self.human_player)
        self.selected = None
        self.keyboard_cursor = first_piece(self.board, self.current_player) or (0, 0)
        self.drag_start = None
        self.drag_pos = None
        self.move_log = []
        self.undo_stack = []
        self.position_counts = Counter()
        self.result = None
        self.status = "A to move."
        self.flash_message = ""
        self.flash_timer = 0.0
        self.hint_move = None
        self.animation = None
        self.ai_delay = 0.0
        self.record_position()
        if self.mode == "ai" and self.current_player == self.ai_player:
            self.ai_delay = 0.35

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.state == "menu":
                    self.handle_menu_event(event)
                else:
                    self.handle_game_event(event)
            self.update(dt)
            self.draw()

    def update(self, dt: float) -> None:
        if self.flash_timer > 0:
            self.flash_timer = max(0, self.flash_timer - dt)
        if self.animation:
            self.animation.progress += dt / self.animation.duration
            if self.animation.progress >= 1:
                self.animation = None
        if self.state == "playing" and not self.result and not self.animation:
            if self.mode == "ai" and self.current_player == self.ai_player:
                self.ai_delay = max(0.0, self.ai_delay - dt)
                if self.ai_delay == 0:
                    self.perform_ai_move()

    def handle_menu_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for button in self.menu_buttons:
            if button.enabled and button.rect.collidepoint(event.pos):
                self.activate_menu_button(button.key)
                return

    def activate_menu_button(self, key: str) -> None:
        if key.startswith("mode:"):
            self.mode = key.split(":", 1)[1]
            if self.mode == "pvp":
                self.status = "Local table selected."
            else:
                self.status = f"{get_stake(self.stake_key).label} selected."
        elif key.startswith("stake:"):
            self.stake_key = key.split(":", 1)[1]
            self.status = f"{get_stake(self.stake_key).label} selected."
        elif key.startswith("side:"):
            self.human_player = key.split(":", 1)[1]
            self.ai_player = opponent(self.human_player)
        elif key.startswith("slot:"):
            self.selected_menu_side = key.split(":", 1)[1]
        elif key.startswith("char:"):
            self.characters[self.selected_menu_side] = key.split(":", 1)[1]
        elif key == "start":
            self.state = "playing"
            self.reset_game()

    def handle_game_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.handle_key(event.key)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.drag_start:
            self.drag_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.handle_mouse_up(event.pos)

    def handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.state = "menu"
            return
        if key == pygame.K_r:
            self.reset_game()
            return
        if key == pygame.K_u:
            self.undo()
            return
        if key == pygame.K_m:
            self.sound.enabled = not self.sound.enabled
            return
        if key == pygame.K_h:
            self.set_hint()
            return
        if self.result or self.is_ai_turn() or self.animation:
            return

        if key == pygame.K_TAB:
            self.cycle_piece()
            return
        if key == pygame.K_SPACE:
            self.toggle_keyboard_selection()
            return

        direction_by_key = {
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
        }
        if key not in direction_by_key:
            return
        direction = direction_by_key[key]
        if self.selected:
            self.try_move(Move(*self.selected, direction))
        else:
            self.move_cursor(direction)

    def handle_mouse_down(self, pos: tuple[int, int]) -> None:
        for button in self.game_buttons:
            if button.enabled and button.rect.collidepoint(pos):
                self.activate_game_button(button.key)
                return
        if self.result or self.is_ai_turn() or self.animation:
            return
        for direction, rect in self.arrow_buttons.items():
            if rect.collidepoint(pos) and self.selected:
                self.try_move(Move(*self.selected, direction))
                return

        cell = self.cell_at(pos)
        if cell is None:
            return
        row, col = cell
        self.keyboard_cursor = cell

        if self.selected:
            move = move_for_destination(self.board, *self.selected, cell)
            if move:
                self.try_move(move)
                return

        if self.board[row][col] == self.current_player:
            self.selected = cell
            self.drag_start = cell
            self.drag_pos = pos
            self.hint_move = None

    def handle_mouse_up(self, pos: tuple[int, int]) -> None:
        if not self.drag_start:
            return
        start = self.drag_start
        drag_pos = self.drag_pos or pos
        dx = drag_pos[0] - (BOARD_X + start[1] * CELL_SIZE + CELL_SIZE // 2)
        dy = drag_pos[1] - (BOARD_Y + start[0] * CELL_SIZE + CELL_SIZE // 2)
        self.drag_start = None
        self.drag_pos = None
        if abs(dx) < 14 and abs(dy) < 14:
            self.selected = start
            return
        direction = drag_direction(dx, dy)
        self.try_move(Move(start[0], start[1], direction))

    def activate_game_button(self, key: str) -> None:
        if key == "menu":
            self.state = "menu"
        elif key == "restart":
            self.reset_game()
        elif key == "undo":
            self.undo()
        elif key == "hint":
            self.set_hint()
        elif key == "mute":
            self.sound.enabled = not self.sound.enabled

    def is_ai_turn(self) -> bool:
        return self.mode == "ai" and self.current_player == self.ai_player

    def push_undo(self) -> None:
        self.undo_stack.append(
            Snapshot(
                board=self.board,
                current_player=self.current_player,
                position_counts=self.position_counts.copy(),
                move_log=list(self.move_log),
                result=self.result,
                status=self.status,
            )
        )

    def undo(self) -> None:
        if not self.undo_stack or self.animation:
            self.flash("Nothing to undo.", BAD)
            return
        snapshot = self.undo_stack.pop()
        self.board = snapshot.board
        self.current_player = snapshot.current_player
        self.position_counts = snapshot.position_counts
        self.move_log = snapshot.move_log
        self.result = snapshot.result
        self.status = snapshot.status
        self.selected = None
        self.hint_move = None
        self.animation = None
        self.ai_delay = 0.0

    def set_hint(self) -> None:
        if self.result or self.is_ai_turn():
            return
        self.hint_move = choose_move(self.board, self.current_player, "hard", self.rng)
        if self.hint_move:
            self.flash("Hint marked on board.", GREEN)
        else:
            self.flash("No legal hint available.", BAD)

    def try_move(self, move: Move) -> bool:
        if self.result or self.animation:
            return False
        if self.board[move.row][move.col] != self.current_player:
            self.invalid("Choose one of your own crabs.")
            return False
        destination = compute_destination(self.board, move.row, move.col, move.direction)
        if not destination:
            self.invalid("That crab cannot slide there.")
            return False
        self.make_move(move, destination)
        return True

    def make_move(self, move: Move, destination: tuple[int, int]) -> None:
        old_board = self.board
        player = self.current_player
        self.push_undo()
        notation = move_notation(old_board, move)
        self.board = apply_move(old_board, move)
        self.move_log.append(f"{player_label(player)}: {notation}")
        self.selected = None
        self.hint_move = None
        self.animation = Animation(player=player, start=(move.row, move.col), end=destination)
        self.sound.play("move")

        winner = check_winner(self.board)
        if winner:
            self.result = winner
            self.status = f"{player_label(winner)} wins."
            self.sound.play("win")
            return

        self.current_player = opponent(self.current_player)
        self.keyboard_cursor = first_piece(self.board, self.current_player) or self.keyboard_cursor
        terminal = terminal_result(self.board, self.current_player)
        if terminal:
            self.result = terminal
            if terminal == "draw":
                self.status = "Draw."
            else:
                self.status = f"{player_label(terminal)} wins. Opponent has no moves."
                self.sound.play("win")
            return

        self.record_position()
        if self.result:
            return
        self.status = f"{player_label(self.current_player)} to move."
        if self.is_ai_turn():
            self.ai_delay = 0.35

    def perform_ai_move(self) -> None:
        move = choose_move(self.board, self.ai_player, self.stake_key, self.rng)
        if not move:
            self.result = self.human_player
            self.status = f"{player_label(self.human_player)} wins. AI has no moves."
            self.sound.play("win")
            return
        destination = compute_destination(self.board, move.row, move.col, move.direction)
        if destination:
            self.make_move(move, destination)

    def record_position(self) -> None:
        key = position_key(self.board, self.current_player)
        self.position_counts[key] += 1
        if is_repetition_draw(self.position_counts, self.board, self.current_player):
            self.result = "draw"
            self.status = "Draw by threefold repetition."

    def invalid(self, message: str) -> None:
        self.flash(message, BAD)
        self.sound.play("invalid")

    def flash(self, message: str, _color: tuple[int, int, int]) -> None:
        self.flash_message = message
        self.flash_timer = 1.35

    def cycle_piece(self) -> None:
        pieces = [
            (row, col)
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
            if self.board[row][col] == self.current_player
        ]
        if not pieces:
            return
        if self.keyboard_cursor not in pieces:
            self.keyboard_cursor = pieces[0]
            return
        index = pieces.index(self.keyboard_cursor)
        self.keyboard_cursor = pieces[(index + 1) % len(pieces)]

    def toggle_keyboard_selection(self) -> None:
        row, col = self.keyboard_cursor
        if self.selected:
            move = move_for_destination(self.board, *self.selected, self.keyboard_cursor)
            if move:
                self.try_move(move)
            else:
                self.selected = None
            return
        if self.board[row][col] == self.current_player:
            self.selected = self.keyboard_cursor

    def move_cursor(self, direction: str) -> None:
        row, col = self.keyboard_cursor
        dr, dc = DIRS[direction]
        self.keyboard_cursor = (
            max(0, min(BOARD_SIZE - 1, row + dr)),
            max(0, min(BOARD_SIZE - 1, col + dc)),
        )

    def cell_at(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        x, y = pos
        if not (BOARD_X <= x < BOARD_X + BOARD_PIXELS and BOARD_Y <= y < BOARD_Y + BOARD_PIXELS):
            return None
        return (int((y - BOARD_Y) // CELL_SIZE), int((x - BOARD_X) // CELL_SIZE))

    def draw(self) -> None:
        self.screen.fill(BG)
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()
        pygame.display.flip()

    def draw_menu(self) -> None:
        self.menu_buttons = []
        title = self.font_title.render("Crab Checkers", True, INK)
        self.screen.blit(title, (MARGIN, 26))
        subtitle = self.font.render("Choose the table, stake, and characters.", True, MUTED)
        self.screen.blit(subtitle, (MARGIN + 4, 78))

        preview_rect = pygame.Rect(360, 132, 410, 410)
        draw_panel(self.screen, preview_rect, (246, 229, 203), GRID)
        draw_tiny_board(self.screen, preview_rect.inflate(-42, -42), self.board)
        draw_lamp(self.screen, (preview_rect.centerx, preview_rect.y + 12))

        self.draw_character_slot(36, 132, PLAYER_A)
        self.draw_character_slot(806, 132, PLAYER_B)

        self.add_menu_button("mode:ai", 52, 568, 145, 54, "Vs AI", "Player vs table", self.mode == "ai")
        self.add_menu_button("mode:pvp", 206, 568, 145, 54, "2 Players", "Local duel", self.mode == "pvp")
        for index, stake in enumerate(STAKES):
            x = 382 + index * 132
            self.add_menu_button(
                f"stake:{stake.key}",
                x,
                568,
                122,
                54,
                stake.label.replace(" Stake", ""),
                "Stake",
                self.stake_key == stake.key,
                enabled=self.mode == "ai",
            )
        self.add_menu_button(
            f"side:{PLAYER_A}",
            806,
            568,
            96,
            54,
            "Play A",
            "Red",
            self.human_player == PLAYER_A,
            enabled=self.mode == "ai",
        )
        self.add_menu_button(
            f"side:{PLAYER_B}",
            912,
            568,
            96,
            54,
            "Play B",
            "Blue",
            self.human_player == PLAYER_B,
            enabled=self.mode == "ai",
        )
        self.add_menu_button("start", 1018, 568, 74, 54, "Start", "", False)

        draw_wrapped(
            self.screen,
            get_stake(self.stake_key).description,
            self.font_small,
            MUTED,
            pygame.Rect(382, 630, 390, 48),
        )
        draw_wrapped(
            self.screen,
            "Future jokers are planned as table modifiers. The first pass keeps them preview-only.",
            self.font_small,
            MUTED,
            pygame.Rect(806, 630, 280, 48),
        )

    def draw_character_slot(self, x: int, y: int, player: str) -> None:
        rect = pygame.Rect(x, y, 250, 410)
        selected = self.selected_menu_side == player
        draw_panel(self.screen, rect, PANEL, GOLD if selected else GRID, width=3 if selected else 2)
        header = self.font_big.render(f"Player {player_label(player)}", True, INK)
        self.screen.blit(header, (x + 18, y + 16))
        slot_button = Button(f"slot:{player}", pygame.Rect(x, y, 250, 330), "", selected=selected)
        self.menu_buttons.append(slot_button)

        character = get_character(self.characters[player])
        draw_character_portrait(self.screen, character.key, pygame.Rect(x + 42, y + 60, 166, 130), character.color)
        name = self.font.render(character.name, True, INK)
        self.screen.blit(name, (x + 18, y + 202))
        draw_wrapped(self.screen, character.tagline, self.font_small, MUTED, pygame.Rect(x + 18, y + 232, 212, 44))
        power = self.font_small.render(character.power_name, True, INK)
        self.screen.blit(power, (x + 18, y + 282))
        draw_wrapped(self.screen, character.power_text, self.font_tiny, MUTED, pygame.Rect(x + 18, y + 304, 212, 42))

        for index, candidate in enumerate(CHARACTERS):
            row = index // 2
            col = index % 2
            bx = x + 18 + col * 108
            by = y + 350 + row * 42
            self.add_menu_button(
                f"char:{candidate.key}",
                bx,
                by,
                98,
                32,
                candidate.short_name,
                "",
                self.characters[player] == candidate.key,
            )

    def add_menu_button(
        self,
        key: str,
        x: int,
        y: int,
        w: int,
        h: int,
        label: str,
        sublabel: str,
        selected: bool,
        enabled: bool = True,
    ) -> None:
        button = Button(key, pygame.Rect(x, y, w, h), label, sublabel, selected, enabled)
        self.menu_buttons.append(button)
        draw_button(self.screen, button, self.font_small, self.font_tiny)

    def draw_game(self) -> None:
        self.game_buttons = []
        self.arrow_buttons = {}
        self.draw_table_background()
        self.draw_character_panel(24, 116, PLAYER_A)
        self.draw_character_panel(BOARD_X + BOARD_PIXELS + MARGIN, 116, PLAYER_B)
        self.draw_board()
        self.draw_controls()
        self.draw_history()
        if self.result:
            self.draw_result_overlay()

    def draw_table_background(self) -> None:
        header = self.font_big.render("Crab Checkers", True, INK)
        self.screen.blit(header, (MARGIN, 26))
        mode_label = "Local 2P" if self.mode == "pvp" else get_stake(self.stake_key).label
        status = self.font.render(f"{mode_label} | {self.status}", True, MUTED)
        self.screen.blit(status, (MARGIN, 64))
        if self.flash_timer > 0:
            flash = self.font.render(self.flash_message, True, BAD)
            self.screen.blit(flash, (BOARD_X, 84))

    def draw_character_panel(self, x: int, y: int, player: str) -> None:
        rect = pygame.Rect(x, y, LEFT_PANEL if player == PLAYER_A else RIGHT_PANEL - 20, 184)
        character = get_character(self.characters[player])
        active = self.current_player == player and not self.result
        draw_panel(self.screen, rect, PANEL, GOLD if active else GRID, width=3 if active else 2)
        draw_character_portrait(self.screen, character.key, pygame.Rect(x + 16, y + 28, 112, 106), character.color)
        label = self.font_big.render(f"{player_label(player)}: {character.short_name}", True, INK)
        self.screen.blit(label, (x + 140, y + 26))
        draw_wrapped(self.screen, character.tagline, self.font_small, MUTED, pygame.Rect(x + 140, y + 64, rect.w - 154, 42))
        future = self.font_tiny.render(character.power_name + " locked", True, MUTED)
        self.screen.blit(future, (x + 140, y + 124))

    def draw_board(self) -> None:
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_PIXELS, BOARD_PIXELS)
        pygame.draw.rect(self.screen, GRID, board_rect.inflate(12, 12), border_radius=8)
        pygame.draw.rect(self.screen, (246, 226, 196), board_rect.inflate(6, 6), border_radius=6)

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(
                    BOARD_X + col * CELL_SIZE,
                    BOARD_Y + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRID, rect, 1)

        self.draw_coordinates()
        self.draw_highlights()
        self.draw_pieces()
        self.draw_drag_ghost()
        self.draw_keyboard_cursor()

    def draw_coordinates(self) -> None:
        for col in range(BOARD_SIZE):
            letter = self.font_tiny.render(chr(ord("a") + col), True, MUTED)
            x = BOARD_X + col * CELL_SIZE + CELL_SIZE // 2 - letter.get_width() // 2
            self.screen.blit(letter, (x, BOARD_Y + BOARD_PIXELS + 8))
        for row in range(BOARD_SIZE):
            number = self.font_tiny.render(str(row + 1), True, MUTED)
            y = BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2 - number.get_height() // 2
            self.screen.blit(number, (BOARD_X - 18, y))

    def draw_highlights(self) -> None:
        if self.selected:
            row, col = self.selected
            rect = cell_rect(row, col)
            pygame.draw.rect(self.screen, GOLD, rect.inflate(-8, -8), 4, border_radius=8)
            for direction, dest in legal_destinations(self.board, row, col).items():
                center = cell_center(*dest)
                pygame.draw.circle(self.screen, (255, 248, 190), center, 16)
                pygame.draw.circle(self.screen, GREEN, center, 16, 3)
                self.draw_arrow_button(direction, dest)
        if self.hint_move:
            dest = compute_destination(self.board, self.hint_move.row, self.hint_move.col, self.hint_move.direction)
            if dest:
                pygame.draw.circle(self.screen, (255, 236, 132), cell_center(*dest), 25, 4)

    def draw_arrow_button(self, direction: str, dest: tuple[int, int]) -> None:
        center = cell_center(*dest)
        offset = {
            "up": (0, -26),
            "down": (0, 26),
            "left": (-26, 0),
            "right": (26, 0),
        }[direction]
        rect = pygame.Rect(center[0] + offset[0] - 15, center[1] + offset[1] - 15, 30, 30)
        self.arrow_buttons[direction] = rect
        pygame.draw.rect(self.screen, WHITE, rect, border_radius=6)
        pygame.draw.rect(self.screen, GREEN, rect, 2, border_radius=6)
        draw_triangle(self.screen, direction, rect.center, GREEN, 9)

    def draw_pieces(self) -> None:
        anim_dest = self.animation.end if self.animation else None
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                player = self.board[row][col]
                if player == EMPTY:
                    continue
                if anim_dest == (row, col):
                    continue
                draw_crab_piece(self.screen, cell_center(row, col), player)

        if self.animation:
            start = cell_center(*self.animation.start)
            end = cell_center(*self.animation.end)
            t = min(1.0, ease_out(self.animation.progress))
            center = (
                int(start[0] + (end[0] - start[0]) * t),
                int(start[1] + (end[1] - start[1]) * t),
            )
            draw_crab_piece(self.screen, center, self.animation.player)

    def draw_drag_ghost(self) -> None:
        if not self.drag_start or not self.drag_pos:
            return
        sx, sy = cell_center(*self.drag_start)
        dx = self.drag_pos[0] - sx
        dy = self.drag_pos[1] - sy
        if abs(dx) < 14 and abs(dy) < 14:
            return
        direction = drag_direction(dx, dy)
        dest = compute_destination(self.board, self.drag_start[0], self.drag_start[1], direction)
        if dest:
            ghost = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(ghost, (255, 255, 255, 96), (CELL_SIZE // 2, CELL_SIZE // 2), 27)
            pygame.draw.circle(ghost, (72, 150, 92, 190), (CELL_SIZE // 2, CELL_SIZE // 2), 27, 4)
            rect = ghost.get_rect(center=cell_center(*dest))
            self.screen.blit(ghost, rect)

    def draw_keyboard_cursor(self) -> None:
        if self.result:
            return
        rect = cell_rect(*self.keyboard_cursor)
        pygame.draw.rect(self.screen, INK, rect.inflate(-12, -12), 2, border_radius=6)

    def draw_controls(self) -> None:
        x = BOARD_X
        y = BOARD_Y + BOARD_PIXELS + 42
        controls = [
            ("menu", "Menu"),
            ("restart", "Restart"),
            ("undo", "Undo"),
            ("hint", "Hint"),
            ("mute", "Sound On" if self.sound.enabled else "Muted"),
        ]
        for key, label in controls:
            button = Button(key, pygame.Rect(x, y, 92, 38), label, "")
            self.game_buttons.append(button)
            draw_button(self.screen, button, self.font_small, self.font_tiny)
            x += 100

        help_text = "Drag, click destination, arrow buttons, keyboard arrows, Tab, Space. H hint, U undo, R restart."
        draw_wrapped(
            self.screen,
            help_text,
            self.font_tiny,
            MUTED,
            pygame.Rect(BOARD_X, y + 48, BOARD_PIXELS, 42),
        )

    def draw_history(self) -> None:
        x = BOARD_X + BOARD_PIXELS + MARGIN
        y = 326
        rect = pygame.Rect(x, y, RIGHT_PANEL - 20, 198)
        draw_panel(self.screen, rect, PANEL, GRID)
        title = self.font.render("Move History", True, INK)
        self.screen.blit(title, (x + 14, y + 12))
        recent = self.move_log[-7:]
        for index, line in enumerate(recent):
            txt = self.font_small.render(line, True, MUTED)
            self.screen.blit(txt, (x + 16, y + 46 + index * 21))

        mod_rect = pygame.Rect(x, y + 218, RIGHT_PANEL - 20, 108)
        draw_panel(self.screen, mod_rect, (244, 232, 211), GRID)
        mod_title = self.font.render("Future Jokers", True, INK)
        self.screen.blit(mod_title, (x + 14, y + 230))
        for index, modifier in enumerate(MODIFIERS[:2]):
            txt = self.font_tiny.render(modifier.name + ": locked", True, MUTED)
            self.screen.blit(txt, (x + 16, y + 264 + index * 22))

    def draw_result_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 24, 20, 125))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(WINDOW_WIDTH // 2 - 190, WINDOW_HEIGHT // 2 - 120, 380, 220)
        draw_panel(self.screen, rect, PANEL, GOLD, width=4)
        if self.result == "draw":
            title = "Draw"
            detail = "The same position appeared three times."
        else:
            title = f"Player {player_label(self.result or '')} wins"
            detail = self.status
        txt = self.font_big.render(title, True, INK)
        self.screen.blit(txt, txt.get_rect(center=(rect.centerx, rect.y + 50)))
        draw_wrapped(self.screen, detail, self.font, MUTED, pygame.Rect(rect.x + 34, rect.y + 84, rect.w - 68, 54))
        hint = self.font_small.render("R restart | Esc menu | U undo", True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(rect.centerx, rect.y + 165)))


def first_piece(board: tuple[str, ...], player: str) -> tuple[int, int] | None:
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == player:
                return row, col
    return None


def cell_rect(row: int, col: int) -> pygame.Rect:
    return pygame.Rect(BOARD_X + col * CELL_SIZE, BOARD_Y + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)


def cell_center(row: int, col: int) -> tuple[int, int]:
    return (BOARD_X + col * CELL_SIZE + CELL_SIZE // 2, BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2)


def drag_direction(dx: int | float, dy: int | float) -> str:
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


def ease_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) * (1 - value)


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, int, int],
    border: tuple[int, int, int],
    width: int = 2,
) -> None:
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, width, border_radius=8)


def draw_button(surface: pygame.Surface, button: Button, font: pygame.font.Font, small: pygame.font.Font) -> None:
    fill = (255, 244, 218) if button.enabled else (211, 202, 190)
    border = GOLD if button.selected else GRID
    if button.key == "start":
        fill = (235, 177, 74)
        border = INK
    pygame.draw.rect(surface, fill, button.rect, border_radius=8)
    pygame.draw.rect(surface, border, button.rect, 3 if button.selected else 2, border_radius=8)
    color = INK if button.enabled else MUTED
    text = font.render(button.label, True, color)
    y_offset = -7 if button.sublabel else 0
    surface.blit(text, text.get_rect(center=(button.rect.centerx, button.rect.centery + y_offset)))
    if button.sublabel:
        sub = small.render(button.sublabel, True, MUTED)
        surface.blit(sub, sub.get_rect(center=(button.rect.centerx, button.rect.centery + 14)))


def draw_wrapped(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    line_gap: int = 2,
) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= rect.w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    y = rect.y
    for line in lines:
        if y + font.get_height() > rect.bottom:
            break
        surface.blit(font.render(line, True, color), (rect.x, y))
        y += font.get_height() + line_gap


def draw_tiny_board(surface: pygame.Surface, rect: pygame.Rect, board: tuple[str, ...]) -> None:
    cell = min(rect.w, rect.h) // BOARD_SIZE
    origin_x = rect.centerx - cell * BOARD_SIZE // 2
    origin_y = rect.centery - cell * BOARD_SIZE // 2
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            square = pygame.Rect(origin_x + col * cell, origin_y + row * cell, cell, cell)
            color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
            pygame.draw.rect(surface, color, square)
            pygame.draw.rect(surface, GRID, square, 1)
            player = board[row][col]
            if player != EMPTY:
                draw_crab_piece(surface, square.center, player, radius=max(8, cell // 4))


def draw_character_portrait(
    surface: pygame.Surface,
    key: str,
    rect: pygame.Rect,
    color: tuple[int, int, int],
) -> None:
    sketch = pygame.Surface(rect.size, pygame.SRCALPHA)
    if key == "bear":
        draw_bear(sketch, sketch.get_rect(), color)
    elif key == "hat":
        draw_hat_player(sketch, sketch.get_rect(), color)
    else:
        draw_lantern_keeper(sketch, sketch.get_rect(), color)
    surface.blit(sketch, rect)


def draw_bear(surface: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
    cx, cy = rect.center
    pygame.draw.ellipse(surface, (249, 239, 218), (cx - 58, cy - 42, 116, 88))
    pygame.draw.ellipse(surface, color, (cx - 70, cy - 34, 38, 44), 5)
    pygame.draw.ellipse(surface, color, (cx + 32, cy - 34, 38, 44), 5)
    pygame.draw.circle(surface, INK, (cx - 24, cy - 4), 4)
    pygame.draw.circle(surface, INK, (cx + 24, cy - 4), 4)
    pygame.draw.ellipse(surface, INK, (cx - 13, cy + 10, 26, 16))
    pygame.draw.arc(surface, INK, (cx - 28, cy + 14, 56, 30), 0.2, math.pi - 0.2, 2)
    for i in range(7):
        pygame.draw.line(surface, INK, (cx - 58 + i * 18, cy - 42), (cx - 68 + i * 17, cy - 55), 2)


def draw_hat_player(surface: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
    cx, cy = rect.center
    pygame.draw.ellipse(surface, (247, 237, 218), (cx - 44, cy - 36, 82, 92))
    pygame.draw.rect(surface, color, (cx - 62, cy - 54, 124, 24), border_radius=8)
    pygame.draw.rect(surface, INK, (cx - 42, cy - 82, 84, 40), border_radius=8)
    pygame.draw.rect(surface, color, (cx - 36, cy - 76, 72, 30), border_radius=6)
    pygame.draw.line(surface, INK, (cx - 24, cy - 8), (cx - 10, cy - 4), 3)
    pygame.draw.line(surface, INK, (cx + 10, cy - 4), (cx + 24, cy - 8), 3)
    pygame.draw.arc(surface, INK, (cx - 22, cy + 8, 44, 28), 0, math.pi, 2)
    pygame.draw.line(surface, INK, (cx - 52, cy + 44), (cx + 50, cy + 52), 4)


def draw_lantern_keeper(surface: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
    cx, cy = rect.center
    pygame.draw.rect(surface, color, (cx - 36, cy - 42, 72, 86), border_radius=8)
    pygame.draw.rect(surface, (255, 238, 166), (cx - 22, cy - 22, 44, 42), border_radius=4)
    pygame.draw.arc(surface, INK, (cx - 30, cy - 62, 60, 38), math.pi, 2 * math.pi, 3)
    pygame.draw.line(surface, INK, (cx - 36, cy - 42), (cx - 20, cy - 22), 3)
    pygame.draw.line(surface, INK, (cx + 36, cy - 42), (cx + 20, cy - 22), 3)
    pygame.draw.line(surface, INK, (cx - 40, cy + 46), (cx + 40, cy + 46), 4)


def draw_lamp(surface: pygame.Surface, top_center: tuple[int, int]) -> None:
    x, y = top_center
    pygame.draw.line(surface, INK, (x, y - 40), (x, y + 20), 3)
    pygame.draw.rect(surface, (255, 238, 166), (x - 26, y + 20, 52, 62), border_radius=8)
    pygame.draw.rect(surface, INK, (x - 26, y + 20, 52, 62), 3, border_radius=8)
    pygame.draw.ellipse(surface, INK, (x - 30, y + 76, 60, 16))


def draw_crab_piece(
    surface: pygame.Surface,
    center: tuple[int, int],
    player: str,
    radius: int = 26,
) -> None:
    color = A_COLOR if player == PLAYER_A else B_COLOR
    shadow = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 45), (radius // 2, radius + 9, radius * 2, radius // 2))
    surface.blit(shadow, shadow.get_rect(center=(center[0], center[1] + 10)))
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, INK, center, radius, 3)
    pygame.draw.circle(surface, WHITE, (center[0] - radius // 3, center[1] - radius // 4), max(3, radius // 7))
    pygame.draw.circle(surface, WHITE, (center[0] + radius // 3, center[1] - radius // 4), max(3, radius // 7))
    pygame.draw.circle(surface, INK, (center[0] - radius // 3, center[1] - radius // 4), max(1, radius // 12))
    pygame.draw.circle(surface, INK, (center[0] + radius // 3, center[1] - radius // 4), max(1, radius // 12))
    pygame.draw.arc(surface, INK, (center[0] - radius // 2, center[1], radius, radius // 2), 0.1, math.pi - 0.1, 2)
    pygame.draw.line(surface, INK, (center[0] - radius, center[1]), (center[0] - radius - 10, center[1] - 8), 3)
    pygame.draw.line(surface, INK, (center[0] + radius, center[1]), (center[0] + radius + 10, center[1] - 8), 3)


def draw_triangle(
    surface: pygame.Surface,
    direction: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
    size: int,
) -> None:
    x, y = center
    if direction == "up":
        points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
    elif direction == "down":
        points = [(x, y + size), (x - size, y - size), (x + size, y - size)]
    elif direction == "left":
        points = [(x - size, y), (x + size, y - size), (x + size, y + size)]
    else:
        points = [(x + size, y), (x - size, y - size), (x - size, y + size)]
    pygame.draw.polygon(surface, color, points)


if __name__ == "__main__":
    CrabCheckersApp().run()
