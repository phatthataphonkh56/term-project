from ursina import *


class Background(Entity):
    def __init__(self, texture_n='game_asset/city_backg.jpg'):
        super().__init__(
            model='quad',
            texture=texture_n,
            scale=(380, 300),
            position=(0, -2.5, 500)
        )