#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1. Изучить документацию к библиотеке pygame и код программы. Понять механизм работы программы (как происходит отрисовка кривой, перерасчет точек сглаживания и другие нюансы реализации программы)

2. Провести рефакторниг кода, переписать программу в ООП стиле с использованием классов и наследования.

Реализовать класс 2-мерных векторов Vec2d [1]. В классе следует определить методы для основных математических операций, необходимых для работы с вектором: Vec2d.__add__ (сумма), Vec2d.__sub__ (разность), Vec2d.__mul__ (произведение на число). А также добавить возможность вычислять длину вектора с использованием функции len(a) и метод int_pair, который возвращает кортеж из двух целых чисел (текущие координаты вектора).
Реализовать класс замкнутых ломаных Polyline с методами отвечающими за добавление в ломаную точки (Vec2d) c её скоростью, пересчёт координат точек (recalc_points) и отрисовку ломаной (draw_points). Арифметические действия с векторами должны быть реализованы с помощью операторов, а не через вызовы соответствующих методов.
Реализовать класс Knot (наследник класса Polyline), в котором добавление и пересчёт координат инициируют вызов функции recalc_knot для расчёта точек кривой по добавляемым «опорным» точкам [2].
Все классы должны быть самостоятельными и не использовать внешние функции.
Реализовать дополнительный функционал (выполнение требований этого пункта предоставляет возможность потренировать свои навыки программирования и позволяет получить дополнительные баллы в этом задании). К дополнительным задачам относятся: реализовать возможность удаления «опорной» точки из кривой, реализовать возможность отрисовки на экране нескольких кривых, реализовать возможность ускорения/замедления скорости движения кривой(-ых).
"""

from __future__ import annotations
from collections import defaultdict
from functools import partial
import math
from typing import Any, List, Optional, Tuple
from operator import itemgetter
import pygame
import random


SCREEN_DIM = (800, 600)


class Vec2d:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.y = y
        self.x = x

    def __add__(self, vec: Vec2d) -> Vec2d:
        "возвращает сумму двух векторов"
        return Vec2d(self.x + vec.x, self.y + vec.y)

    def __sub__(self, vec: Vec2d) -> Vec2d:
        "возвращает разность векторов"
        return Vec2d(self.x - vec.x, self.y - vec.y) 

    def __mul__(self, num: float) -> Vec2d:
        "возвращает произведение вектора на число"
        return Vec2d(self.x * num, self.y * num)

    def __rmul__(self, num: float) -> Vec2d:
        return self.__mul__(num)

    def __len__(self) -> int:
        "возвращает длину вектора"
        return round(math.sqrt(self.x ** 2 + self.y ** 2))

    def int_pair(self) -> Tuple[int, int]:
        "возвращает целочисленную пару координат вектора"
        return round(self.x), round(self.y)

    def calc_distance_to(self, vec: Vec2d) -> float:
        "вычисляет манхетеннское расстояние между векторами"
        return abs(self.x - vec.x) + abs(self.y - vec.y)


class Display:
    """
    Инкапсулирует всю работу с дисплеем, 
    
    ведет себя как pygame.Surface 
    
    с дополнительными аттрибутами высоты и ширины экрана, 
    
    а также заданием подписи при инициализации
    """
    def __init__(self, screen_size: Tuple[int,int], caption: str) -> None:
        self.width = screen_size[0] 
        self.height = screen_size[1] 
        self.__surface = pygame.display.set_mode(screen_size)
        pygame.display.set_caption(caption)

    def __getattr__(self, name: str) -> Any:
        return self.__surface.__getattribute__(name)

    @staticmethod
    def flip(*args, **kwargs) -> None:
        pygame.display.flip(*args, **kwargs)

    @staticmethod
    def quit(*args, **kwargs) -> None:
        pygame.display.quit(*args, **kwargs)

    def get_surface(self):
        """возвращает сущность Surface, для разрешения несоответствия типов"""
        return self.__surface


class Polyline:
    """
    Описывает ломаную, состоящую из набора точек со скоростями

    Набор точек на экране
    """
    display: Display
    points: List[Vec2d]
    speeds: List[Vec2d]

    def __init__(self, display: Display) -> None:
        self.points = []
        self.speeds = []
        self.display = display

    def recalc_points(self) -> None:
        """
        функция перерасчета координат опорных точек
        """
        i = 0
        for point, speed in zip(self.points, self.speeds):
            newpoint = point + speed
            self.points[i] = newpoint
            if newpoint.x > self.display.width or newpoint.x < 0:
                self.speeds[i] = Vec2d(- self.speeds[i].x, self.speeds[i].y)
            if newpoint.y > self.display.height or newpoint.y < 0:
                self.speeds[i] = Vec2d(self.speeds[i].x, -self.speeds[i].y)
            i += 1

    def _draw_points(self, 
                    points: list,
                    style: str = "points", 
                    width: int = 3, 
                    color: Tuple[int, int, int] = (255, 255, 255) ) -> None:
        """
        функция отрисовки точек на экране
        """
        if style == "line":
            for p_n in range(-1, len(points) - 1):
                pygame.draw.line(self.display.get_surface(), color,
                             points[p_n].int_pair(),
                             points[p_n + 1].int_pair(), 
                             width)

        elif style == "points":
            for point in points:
                pygame.draw.circle(self.display.get_surface(), color,
                                   point.int_pair(), width)

    def draw_points(self, *args, **kwargs) -> None:
        self._draw_points(self.points, *args, **kwargs)
        

class Knot(Polyline):
    """
    Описывает замкнутую кривую, которая строится по точкам
    """
    knot_points_count: int
    knot_points: List[Vec2d]

    def __init__(self, display: Display, knot_points_count=35) -> None:
        super().__init__(display)
        self.knot_points_count = knot_points_count
        self.knot_points = []
        self.points = []
        self.speeds = []

    def add_base_point(self, point: Vec2d, speed: Vec2d) -> None:
        """Добавляет опорную точку и перерасчитывает кривую"""
        self.points.append(point)
        self.speeds.append(speed)
        self.recalc_knot()

    def delete_base_point(self, point: Vec2d) -> None:
        """Удаляет ближайшую к месту нажатия опорную точку текущей кривой"""
        del_candidates = sorted(
            [(i,dist) for i in range(len(self.points)) 
                if (dist := self.points[i].calc_distance_to(point)) <= 5],
            key=itemgetter(1)
            )

        if del_candidates:
            v, _ = del_candidates[0]
            self.points.pop(v)
            self.recalc_knot()

    def recalc_points(self) -> None:
        super().recalc_points()
        self.recalc_knot()

    def __get_knot_point(
            self, smooth_points: List[Vec2d], 
            alpha: float, deg: Optional[int]=None) -> Vec2d:
        """
        возвращает координаты следующей точки гладкой кривой безье
        """
        if deg is None:
            deg = len(smooth_points) - 1
        if deg == 0:
            return Vec2d(smooth_points[0].x, smooth_points[0].y)

        res = smooth_points[deg] * alpha + self.__get_knot_point(smooth_points, alpha, deg - 1) * (1 - alpha)
        return Vec2d(res.x, res.y)
    
    def __get_knot_points(self, smooth_points: List[Vec2d]) -> List[Vec2d]:
        """Возвращает все точки"""
        alpha = 1 / self.knot_points_count
        return [self.__get_knot_point(smooth_points, i * alpha) 
                    for i in range(self.knot_points_count)]

    def recalc_knot(self) -> None:
        """
        Добавляет промежуточные точки между опорными и строит точки кривой между ними
        """
        if len(self.points) < 3:
            self.knot_points = []

        else:

            res = []
            for i in range(-2, len(self.points) - 2):
                #точки между опорными
                smooth_points = [
                    0.5 * (self.points[i] + self.points[i + 1]), 
                    self.points[i + 1],  
                    0.5 * (self.points[i+1] + self.points[i + 2])
                    ]
                res.extend(self.__get_knot_points(smooth_points))
        
            self.knot_points = res 

    def draw_knot(self, *args, **kwargs) -> None:
        super()._draw_points(self.knot_points, *args, **kwargs)


class KnotsManager:
    """
    Инкапсулирует работу с несколькими кривыми: переключение, 
    перерасчет и рисование
    """
    curr_knot: int
    knots: defaultdict

    def __init__(self, max: int, displ: Display) -> None:
        self.knots = defaultdict(partial(Knot, display=displ))
        self.max = max
        self.curr_knot = -1

    def get_next(self) -> Knot:
        """Возвращает следующую кривую циклически"""
        if self.curr_knot == max:
            self.curr_knot = 0
        else:
            self.curr_knot += 1
        return self.knots[self.curr_knot] 

    def get_prev(self) -> Knot:
        """возвращает предыдущую кривую"""
        if self.curr_knot == 0:
            pass
        else:
            self.curr_knot -= 1
        return self.knots[self.curr_knot]

    def recalc_all(self) -> None:
        """прерасчитывает все кривые"""
        for i in self.knots.values():
            i.recalc_points()

    def draw_all(self, *args) -> None:
        """
        рисует опорные точки и кривые, 
        
        у текущей выбраной кривой подсвечивает точки зеленым
        """
        i = 0
        for knot in self.knots.values():
            if i == self.curr_knot:
                knot.draw_points(color=(148, 255, 11))
            else:
                knot.draw_points()
            knot.draw_knot(*args)
            i += 1


def draw_help():
    """функция отрисовки экрана справки программы"""
    gameDisplay.fill((50, 50, 50))
    data = []
    data.append(["F1", "Show Help"])
    data.append(["R", "Restart"])
    data.append(["P", "Pause/Play"])
    data.append(["Num+", "More points"])
    data.append(["Num-", "Less points"])
    data.append(["→", "Next Knot"])
    data.append(["←", "Previous Knot"])
    data.append(["↑", "Increase speed"])
    data.append(["↓", "Decrease speed"])
    data.append(["", ""])
    data.append([str(knot.knot_points_count), "Current points"])

    pygame.draw.lines(gameDisplay.get_surface(), (255, 50, 50, 255), True, [
        (0, 0), (800, 0), (800, 600), (0, 600)], 5)
    for i, text in enumerate(data):
        gameDisplay.blit(
                COURIER.render(text[0], True, (128, 128, 255)), 
                (100, 100 + 30 * i)
                )
        gameDisplay.blit(
                SERIF.render(text[1], True, (128, 128, 255)),
                (200, 100 + 30 * i)
                )


if __name__ == "__main__":
    pygame.init()
    COURIER = pygame.font.SysFont("courier", 24)
    SERIF = pygame.font.SysFont("serif", 24)
    gameDisplay = Display(SCREEN_DIM, caption="MyScreenSaver")

    knots = KnotsManager(max=10, displ=gameDisplay)
    knot = knots.get_next()
    working = True
    show_help = False
    pause = True

    hue = 0
    color = pygame.Color(0)

    while working:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                working = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    working = False
                if event.key == pygame.K_r:
                    knot.points = []
                    knot.speeds = []
                if event.key == pygame.K_p:
                    pause = not pause
                if event.key == pygame.K_KP_PLUS:
                    knot.knot_points_count += 1
                if event.key == pygame.K_F1:
                    show_help = not show_help
                if event.key == pygame.K_KP_MINUS:
                    knot.knot_points_count -= 1 if knot.knot_points_count > 1 else 0
                if event.key == pygame.K_RIGHT:
                    knot = knots.get_next()
                if event.key == pygame.K_LEFT:
                    knot = knots.get_prev()
                if event.key == pygame.K_UP:
                    knot.speeds = [ i*1.5 for i in knot.speeds]
                if event.key == pygame.K_DOWN:
                    knot.speeds = [ i*(1/1.5) for i in knot.speeds]
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    knot.add_base_point(
                        Vec2d(*event.pos), 
                        Vec2d(random.random() * 2, random.random() * 2))
                if event.button == 3:
                    knot.delete_base_point(Vec2d(*event.pos))

        gameDisplay.fill((0, 0, 0))
        hue = (hue + 1) % 360
        color.hsla = (hue, 100, 50, 100)
        knots.draw_all("line", 3, color)
        if not pause:
            knots.recalc_all()
        if show_help:
            draw_help()

        pygame.display.flip()

    pygame.display.quit()
    pygame.quit()
    exit(0)
