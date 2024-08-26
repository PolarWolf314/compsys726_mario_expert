"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import math
from enum import IntEnum
from enum import Enum

import cv2
import numpy as np
from pyboy.utils import WindowEvent

from mario_environment import MarioEnvironment


class SpriteMap(IntEnum):
    AIR = 0
    MARIO = 1
    # ITEMS
    COIN = 5
    MUSHROOM = 6
    STAR = 8
    # BLOCKS
    GROUND = 10
    COIN_BRICK = 10
    USED_POWERUP_BLOCK = 10
    MOVING_PLATFORM = 11
    BRICK = 12
    POWERUP_BLOCK = 13
    PIPE = 14
    # ENEMIES
    GOOMBA = 15
    KOOPA = 16
    FIGHTER_FLY = 18
    KOOPA_BOMB_SHELL = 25


class Action(IntEnum):
    DOWN = 0
    LEFT = 1
    RIGHT = 2
    UP = 3
    A = 4  # jump
    JUMP = 4
    B = 5  # fireball
    SPRINT = 5


class MemoryMap(IntEnum):
    MARIO_Y_POSITION = int("C201", 16)
    MARIO_X_POSITION = int("C202", 16)


class GameAreaAttributes(IntEnum):
    # Width and height of game area
    WIDTH = 20
    HEIGHT = 16


class MarioActions(Enum):
    """
    An enum class to represent custom actions for the Mario game.

    Each value is a tuple where the first element determines how long the action
    should be performed and the second element is a list of buttons to press.
    """

    SPRINT_AND_RUN = (
        1,
        [
            Action.RIGHT,
            Action.SPRINT,
        ],
    )
    TAP_JUMP = (1, [Action.JUMP])
    SHORT_JUMP = (5, [Action.JUMP])
    MEDIUM_JUMP = (10, [Action.JUMP])
    LONG_JUMP = (15, [Action.JUMP])


class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        act_freq: int = 1,
        emulation_speed: int = 1,
        headless: bool = False,
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[int] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        release_button: list[int] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button

    def run_action(self, action: tuple[int, list]) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        self.pyboy.send_input(self.valid_actions[Action.RIGHT])

        self.pyboy.send_input(self.valid_actions[Action.SPRINT])

        self.pyboy.tick()

        for duration in range(action[0]):
            for a in action[1]:
                self.pyboy.send_input(self.valid_actions[a])

            for _ in range(self.act_freq):
                self.pyboy.tick()

            for a in action[1]:
                self.pyboy.send_input(self.release_button[a])


class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path

        self.environment = MarioController(headless=headless)

        self.video = None

        # storing the path for mario to move
        self.path = []

    def get_mario_position(self, game_area: np.ndarray) -> tuple[int, int]:
        """
        Get the position of Mario in the game area
        Returns:
            tuple: The position of Mario in the game area
        """
        # scan the game area
        for y in range(GameAreaAttributes.HEIGHT):
            for x in range(GameAreaAttributes.WIDTH):
                if game_area[y][x] == SpriteMap.MARIO:
                    return (x + 1, y + 1)

        return (x, y)

    def is_enemy_ahead(
        self, game_area: np.ndarray, distance_check: int, height_check: int
    ) -> bool:

        mario_x_position, mario_y_position = self.get_mario_position(game_area)

        for x in range(distance_check):
            for y in range(height_check):
                if (mario_y_position + y) >= GameAreaAttributes.HEIGHT or (
                    mario_y_position - y
                ) < 0:
                    continue
                if game_area[mario_y_position - y][mario_x_position + x] in [
                    SpriteMap.GOOMBA.value,
                    SpriteMap.KOOPA.value,
                ]:
                    return True
        return False

    def is_fighter_fly_ahead(
        self, game_area: np.ndarray, distance_check: int, height_check: int
    ) -> bool:
        mario_x_position, mario_y_position = self.get_mario_position(game_area)

        for x in range(distance_check):
            for y in range(height_check):
                if (mario_y_position + y) >= GameAreaAttributes.HEIGHT or (
                    mario_y_position - y
                ) < 0:
                    continue
                if game_area[mario_y_position - y][mario_x_position + x] in [
                    SpriteMap.FIGHTER_FLY.value,
                ]:
                    return True
        return False

    def is_obstacle_ahead(
        self, game_area: np.ndarray, distance_check: int, height_check: int
    ) -> bool:
        mario_x_position, mario_y_position = self.get_mario_position(game_area)

        for x in range(distance_check):
            for y in range(height_check):
                if (mario_y_position + y) >= GameAreaAttributes.HEIGHT or (
                    mario_y_position - y
                ) < 0:
                    continue
                if game_area[mario_y_position - y][mario_x_position + x] in [
                    SpriteMap.USED_POWERUP_BLOCK.value,
                    SpriteMap.PIPE.value,
                    SpriteMap.MOVING_PLATFORM.value,
                ]:
                    return True

        return False

    def is_pipe_ahead(
        self, game_area: np.ndarray, distance_check: int, height_check: int = 0
    ) -> bool:
        mario_x_position, mario_y_position = self.get_mario_position(game_area)
        for x in range(distance_check):
            if game_area[mario_y_position - height_check][mario_x_position + x] in [
                SpriteMap.PIPE.value
            ]:
                return True
        return False

    def is_pit_ahead(self, game_area: np.ndarray, distance_check: int) -> bool:
        mario_x_position, mario_y_position = self.get_mario_position(game_area)
        for x in range(distance_check):
            if game_area[GameAreaAttributes.HEIGHT - 1][mario_x_position + x] in [
                SpriteMap.AIR.value
            ]:
                return True
        return False

    def choose_action(self) -> tuple[int, list]:
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()

        if self.is_pipe_ahead(game_area, 2):
            print("Pipe ahead")
            return MarioActions.SHORT_JUMP.value

        if self.is_fighter_fly_ahead(game_area, 2, 3):
            print("Fighter Fly ahead")
            return MarioActions.SPRINT_AND_RUN.value

        if self.is_enemy_ahead(game_area, 3, 2):
            print("Enemy ahead")
            return MarioActions.TAP_JUMP.value

        if self.is_enemy_ahead(game_area, 6, 6) and self.is_obstacle_ahead(
            game_area, 5, 6
        ):
            print("Enemy and obstacle ahead")
            return MarioActions.LONG_JUMP.value

        if self.is_pit_ahead(game_area, 3):
            print("Pit ahead")
            return MarioActions.TAP_JUMP.value

        if self.is_obstacle_ahead(game_area, 4, 2):
            print("Obstacle ahead")
            return MarioActions.MEDIUM_JUMP.value

        # Implement your code here to choose the best action
        # time.sleep(0.1)

        return MarioActions.SPRINT_AND_RUN.value

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action)

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()
