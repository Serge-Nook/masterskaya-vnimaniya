import math

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage, QPainter

from mv.exercises.planning import Maze, bfs_path, generate_maze
from mv.exercises.attention import RedCircles
from mv.exercises.registry import EXERCISES, WORKSHOPS
from mv.scenes import make_change, make_scene


def test_registry():
    assert [ws["key"] for ws in WORKSHOPS] == ["attention", "planning", "calm"]
    assert len(EXERCISES) == 10
    for cls in EXERCISES.values():
        assert cls.title and cls.intro


@pytest.mark.parametrize("key", sorted(EXERCISES))
@pytest.mark.parametrize("level,diff", [(1, 1), (5, 2), (10, 3)])
def test_exercise_runs(ctx, key, level, diff):
    ex = EXERCISES[key](ctx)
    ex.resize(1280, 640)
    results = []
    ex.done.connect(results.append)
    ex.start(level, diff, hint=(level == 5), seed=level * 7)
    img = QImage(1280, 640, QImage.Format.Format_ARGB32)
    for _ in range(120):
        ex.tick(1 / 30)
        if ex.finished:
            break
    p = QPainter(img)
    ex.paint(p)
    p.end()
    for pt in (QPointF(640, 320), QPointF(100, 100), QPointF(1200, 600)):
        ex.press(pt)
        ex.move(pt, True)
        ex.release(pt)
    for _label, slot in ex.actions():
        assert callable(slot)
    ex.stop()


def test_red_circles_perfect(ctx):
    ex = RedCircles(ctx)
    ex.start(3, 2, seed=1)
    for it in [i for i in ex.items if i["target"]]:
        ex.press(QPointF(it["x"], it["y"]))
    assert ex.finished and ex.err_impulsive == 0


def test_red_circles_impulsive(ctx):
    ex = RedCircles(ctx)
    ex.start(3, 2, seed=2)
    wrong = next(i for i in ex.items if not i["target"])
    # уберём совпадения с целями, чтобы клик был точно по отвлекающему объекту
    for it in ex.items:
        if it is not wrong:
            it["x"], it["y"] = -500, -500
    ex.press(QPointF(wrong["x"], wrong["y"]))
    assert ex.err_impulsive == 1


@pytest.mark.parametrize("seed", range(10))
def test_maze_connected_and_solvable(ctx, seed):
    import random

    links = generate_maze(9, 6, random.Random(seed))
    assert len(links) == 54
    assert sum(len(v) for v in links.values()) // 2 == 53  # идеальный лабиринт — дерево
    path = bfs_path(links, (0, 0), (8, 5))
    assert path[0] == (0, 0) and path[-1] == (8, 5)

    ex = Maze(ctx)
    ex.start(1 + seed % 6, 2, seed=seed)
    ex.phase = "play"
    for cell, _ in ex.targets:
        for nxt in bfs_path(ex.links, ex.pos, cell)[1:]:
            ex.anim_t = 1.0
            if ex.finished:
                break
            ex.step(nxt[0] - ex.pos[0], nxt[1] - ex.pos[1])
    assert ex.finished


def test_scenes(app):
    import random

    for seed in range(60):
        s = make_scene(seed, 6)
        s2 = make_scene(seed, 6)
        assert [i.name for i in s.items] == [i.name for i in s2.items]
        changed, change = make_change(s, random.Random(seed), allow_move=True)
        assert change.kind in {"color", "remove", "replace", "add", "move"}
        assert changed is not s
