from ursina import *


class Background(Entity):
    def __init__(self, texture_n='city_backg.jpg'):
        super().__init__(
            model='quad',
            texture=texture_n,
            scale=(380, 300),
            position=(0, -2.5, 500)
        )