from mv.exercises.attention import ListenAndDo, RedCircles, StopGame, WhatChanged
from mv.exercises.calm import Breathing, Rainbow, Warmup
from mv.exercises.planning import Backpack, Maze, Puzzle
from mv.i18n import N_

WORKSHOPS = [
    {"key": "attention", "title": N_("Внимание"), "picture": "star", "voice": "ws_attention",
     "exercises": [RedCircles, WhatChanged, ListenAndDo, StopGame]},
    {"key": "planning", "title": N_("Усидчивость"), "picture": "backpack", "voice": "ws_planning",
     "exercises": [Maze, Puzzle, Backpack]},
    {"key": "calm", "title": N_("Спокойствие"), "picture": "rainbow", "voice": "ws_calm",
     "exercises": [Breathing, Rainbow, Warmup]},
]

EXERCISES = {cls.key: cls for ws in WORKSHOPS for cls in ws["exercises"]}


def workshop(key: str) -> dict:
    return next(ws for ws in WORKSHOPS if ws["key"] == key)
