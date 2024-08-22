"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
from enum import IntEnum

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


class MemoryMap(IntEnum):
    MARIO_Y_POSITION = int("C201", 16)
    MARIO_X_POSITION = int("C202", 16)


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
        act_freq: int = 10,
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

    def run_action(self, action: list) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        for a in action:
            self.pyboy.send_input(self.valid_actions[a])

        for _ in range(self.act_freq):
            self.pyboy.tick()

        for a in action:
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
        for y in range(16):
            for x in range(20):
                if game_area[y][x] == SpriteMap.MARIO:
                    return (x, y)

        return (x, y)

    def get_end_of_frame_position(self) -> tuple[int, int]:
        """
        Get the position of the end of the frame in the game area where mario can stand on
        Returns:
            tuple: The position of the end of the frame in the game area
        """
        end_frame_x_position = 9

        # from the bottom of the frame see where the first ground block is
        for y in range(18, 0, -1):
            if (
                self.environment.game_area()[y][end_frame_x_position]
                == SpriteMap.GROUND
            ):
                return (end_frame_x_position, y)

        return (end_frame_x_position, 0)

    def mario_sprint_and_run(self) -> list[int]:
        """
        Function to make mario sprint and run
        Returns:
            tuple: The action to make mario sprint and run
        """

        return [
            self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_RIGHT),
            self.environment.valid_actions.index(WindowEvent.PRESS_BUTTON_B),
        ]

    def is_enemy_ahead(self, game_area: np.ndarray) -> bool:

        print(game_area.shape)
        mario_x_position, mario_y_position = self.get_mario_position(game_area)
        print(mario_x_position, mario_y_position)

        for x in range(7):
            for y in range(16):
                if game_area[y][mario_x_position + x] in [
                    SpriteMap.GOOMBA.value,
                    SpriteMap.KOOPA.value,
                    SpriteMap.FIGHTER_FLY.value,
                ]:
                    return True
        return False

    def choose_action(self) -> list:
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()
        print(game_area)

        if self.is_enemy_ahead(game_area):
            return [self.environment.valid_actions.index(WindowEvent.PRESS_BUTTON_A)]
        # Implement your code here to choose the best action
        # time.sleep(0.1)

        return self.mario_sprint_and_run()

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Always sprint and run to the right
        self.environment.run_action(self.mario_sprint_and_run())

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
