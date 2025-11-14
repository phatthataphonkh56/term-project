from ursina import *
import math
import time


class Player(Entity):
    def __init__(self):
        super().__init__(
            model='apx_70_-_low_poly_model.glb',
            scale=(0.45, 0.6, 0.45),
            position=(0, 0, 0),
            rotation_y=-90,
            collider='box'
        )
        self.lane = 0
        self.target_x = 0
        self.lane_distance = 2
        self.move_speed = 4
        self.alive = True

        self.tilt_angle = 0
        self.tilt_target = 0
        self.tilt_speed = 10

        self.shadow = Entity(
            parent=self,
            model='circle',
            color=color.black33,
            scale=(1.2, 1.2, 1.2),
            position=(0, -0.18, 0),
            rotation_x=90
        )

    def input(self, key):
        if not self.alive:
            return
        if key == 'a' and self.lane > -0.75:
            self.lane -= 0.75
            self.tilt_target = -15
        if key == 'd' and self.lane < 0.75:
            self.lane += 0.75
            self.tilt_target = 15

        self.target_x = self.lane * self.lane_distance

    def update(self):
        if self.alive:
            self.x = lerp(self.x, self.target_x, time.dt * self.move_speed)

            self.tilt_angle = lerp(self.tilt_angle, self.tilt_target, time.dt * self.tilt_speed)
            self.rotation_y = -90 + self.tilt_angle

            if abs(self.tilt_target - self.tilt_angle) < 1:
                self.tilt_target = 0