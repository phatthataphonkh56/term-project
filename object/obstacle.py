from ursina import *
import random
import time
import math
import os

textures_list = [f"obstacle_pic/{file}" for file in os.listdir('obstacle_pic')]


class Obstacle(Entity):

    def __init__(self, z, obstacle_type='static'):
        self.type = obstacle_type
        lane_pos = random.choice([-1.5, 0, 1.5])
        tex = random.choice(textures_list)
        self.base_lane = random.choice([-1.5, 0, 1.5])

        super().__init__(
            model='cube',
            texture=tex,
            color=color.white,
            scale=(1.6, 2, 1),
            position=(lane_pos, 1.05, z),
            collider='box'
        )

        if self.type == 'moving':
            self.move_speed = random.uniform(1, 2)

        if self.type == 'lane_switch':
            self.next_switch_time = time.time() + random.uniform(1, 2)

    def upd(self, speed):
        self.z -= time.dt * speed

        if self.type == 'moving':
            self.x = self.base_lane + math.sin(time.time() * self.move_speed) * 0.8

        elif self.type == 'lane_switch':
            if time.time() >= self.next_switch_time:
                self.x = random.choice([-1.5, 0, 1.5])
                self.next_switch_time = time.time() + random.uniform(1, 2)

        if self.z < -10:
            self.z += 200
            self.base_lane = random.choice([-1.5, 0, 1.5])
            self.x = self.base_lane

            if self.type == 'moving':
                self.move_speed = random.uniform(1, 2)

            if self.type == 'lane_switch':
                self.next_switch_time = time.time() + random.uniform(1, 2)