import data
import game
import pygame as pg


if __name__ == '__main__':
    pg.init()
    data.load()
    game.init()
    game.loop()
    pg.quit()
