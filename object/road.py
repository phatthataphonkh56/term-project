from ursina import *
import time


class Road(Entity):
    def __init__(self, z):
        super().__init__(
            model='road_hd.glb',
            scale=0.3,
            position=(0, -0.1, z),
            rotation=(0, 180, 0)
        )

    def upd(self, speed, road_length, roads):
        self.z -= time.dt * speed
        if self.z < -road_length * 0.3:
            self.z += road_length * len(roads)