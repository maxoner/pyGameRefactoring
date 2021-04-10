#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional, Tuple, List, Union
import pygame
import random
import math

from pygame import display


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


class Polyline:
    """
    Описывает ломаную, состоящую из набора точек со скоростями
    Набор точек на экране
    """
    points: List[Vec2d]
    speeds: List[Vec2d]

    __display: Display

    def __init__(self, points: List[Vec2d],
                speeds: List[Vec2d], display: Display) -> None:
        self.points = points
        self.speeds = speeds
        self.__display = display

    def set_points(self) -> None:
        """функция перерасчета координат опорных точек"""
        i = 0
        for point, speed in zip(self.points, self.speeds):
            newpoint = point + speed
            self.points[i] = newpoint
            i += 1
            if newpoint.x > self.__display.size[0] or newpoint.x < 0:
                self.speeds[i] = Vec2d(-self.speeds[i].x, self.speeds[i].y)
            if newpoint.y > self.__display.size[1] or newpoint.y < 0:
                self.speeds[i] = Vec2d(self.speeds[i].x, -self.speeds[i].y)

    def draw_points(self, 
                    style: str = "points", 
                    width: int = 3, 
                    color: Tuple[int, int, int] = (255, 255, 255) ) -> None:
        """функция отрисовки точек на экране"""
        if style == "line":
            for p_n in range(-1, len(self.points) - 1):
                pygame.draw.line(self.__display, color,
                             (int(self.points[p_n].x), int(self.points[p_n].y)),
                             (int(self.points[p_n + 1].x), int(self.points[p_n + 1].y)), 
                             width)

        elif style == "points":
            for point in self.points:
                pygame.draw.circle(self.__display, color,
                                   point.int_pair(), width)
        

class Knot(Polyline):
    """
    Описывает замкнутую кривую, которая строится по точкам
    """
    def get_point(self, alpha: float, deg: Optional[int]=None) -> Vec2d:
        """
        возвращает координаты следующей точки гладкой кривой, походу это кривая безье
        """
        if deg is None:
            deg = len(self.points) - 1
        if deg == 0:
            return self.points[0]
        return self.points[deg] * alpha + self.get_point(alpha, deg - 1) * (1 - alpha) #у сука, не хвостовая!
    
    def get_points(self) -> List[Vec2d]:
        """
        Возвращает все точки
        """
        count = len(self.points)
        alpha = 1 / count
        return [self.get_point(i * alpha) for i in range(count)]

    def get_knot(self) -> List[Vec2d]:
        if len(self.points) < 3:
            return []

        res = []
        for i in range(-2, len(self.points) - 2):
            res += [
                0.5 * (self.points[i] + self.points[i + 1]), 
                self.points[i + 1],  
                0.5 * (self.points[i+1] + self.points[i + 2])
                ]

        return res


class Display:
    size: Tuple[int,int]

    __display : pygame.display

    def __init__(self, screen_dim: Tuple[int,int], 
                caption: str = "MyScreenSaver") -> None:
        self.__display = pygame.display.set_mode(screen_dim)
        pygame.display.set_caption(caption)
        self.size = SCREEN_DIM

    def draw_help(self, steps) -> None:
        """функция отрисовки экрана справки программы"""
        self.__display.fill((50, 50, 50))
        font1 = pygame.font.SysFont("courier", 24)
        font2 = pygame.font.SysFont("serif", 24)
        data = []
        data.append(["F1", "Show Help"])
        data.append(["R", "Restart"])
        data.append(["P", "Pause/Play"])
        data.append(["Num+", "More points"])
        data.append(["Num-", "Less points"])
        data.append(["", ""])
        data.append([str(steps), "Current points"])

        pygame.draw.lines(self.__display, (255, 50, 50, 255), True, [
            (0, 0), (800, 0), (800, 600), (0, 600)], 5)
        for i, text in enumerate(data):
            self.__display.blit(font1.render(
                text[0], True, (128, 128, 255)), (100, 100 + 30 * i))
            self.__display.blit(font2.render(
                text[1], True, (128, 128, 255)), (200, 100 + 30 * i))


def main_loop():
    pygame.init()
    gameDisplay = Display(SCREEN_DIM)
    working = True
    pause = False
    show_help = False
    
    steps=35

    hue = 0
    color = pygame.Color(0)
    knot = Knot([],[],display = gameDisplay)

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
                    steps += 1
                if event.key == pygame.K_F1:
                    show_help = not show_help
                if event.key == pygame.K_KP_MINUS:
                    steps -= 1 if steps > 1 else 0

            if event.type == pygame.MOUSEBUTTONDOWN:
                knot.points.append(Vec2d(*event.pos))
                knot.speeds.append(Vec2d(random.random() * 2, random.random() * 2))

        gameDisplay.fill((0, 0, 0))
        hue = (hue + 1) % 360
        color.hsla = (hue, 100, 50, 100)
        draw_points(points)
        draw_points(get_knot(points, steps), "line", 3, color)
        if not pause:
            set_points(points, speeds)
        if show_help:
            draw_help()

        pygame.display.flip()

    pygame.display.quit()
    pygame.quit()
    exit(0)

    pass


if __name__ == "__main__":
    main_loop()