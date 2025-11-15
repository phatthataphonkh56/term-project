from ursina import *
import random
import time
import math

# --- (MODIFIED) ---
# We no longer load textures here.
# main.py will pass the texture list to us.
# ------------------

class Obstacle(Entity):
    # --- (FIX) Added textures_list parameter ---
    def __init__(self, z, x, textures_list=None):
        
        # --- (MODIFIED) Use the passed-in texture list ---
        if not textures_list:
            textures_list = ['white_cube'] # Failsafe
        tex = random.choice(textures_list)
        # ---------------------------------------------

        self.type = 'static' # Start as static, can be changed
        self.base_lane = x
        
        super().__init__(
            model='cube',
            texture=tex,
            color=color.white,
            # --- (MODIFIED) Made walls narrower to match gates ---
            scale=(1.4, 2, 1),
            # --------------------------------------------------
            position=(x, 1.05, z),
            collider='box'
        )

        self.move_speed = 0
        self.next_switch_time = 0

    def upd(self, speed):
        # All obstacles move towards the player
        self.z -= time.dt * speed

        # Handle movement for non-static types
        if self.type == 'moving':
            self.x = self.base_lane + math.sin(time.time() * self.move_speed) * 0.8

        elif self.type == 'lane_switch':
            if time.time() >= self.next_switch_time:
                # --- (MODIFIED) Use new wider lanes ---
                self.x = random.choice([-2, 0, 2])
                # ------------------------------------
                self.next_switch_time = time.time() + random.uniform(1, 2)

    # --- (MODIFIED) Added textures_list parameter ---
    def reset(self, z, x, speed, textures_list):
        # Reset position
        self.position = (x, 1.05, z)
        self.base_lane = x
        
        # --- (MODIFIED) Use the passed-in texture list ---
        if not textures_list:
            textures_list = ['white_cube']
        self.texture = random.choice(textures_list)
        # ---------------------------------------------

        # --- Difficulty Scaling ---
        # As speed increases, obstacles get more complex
        
        # 1. Determine type based on speed
        # At speed 20, 25% chance of complex.
        # At speed 40, 75% chance of complex.
        chance = min(0.75, (speed - 20) * 0.025) 
        if random.random() < chance:
            self.type = random.choice(['moving', 'lane_switch'])
        else:
            self.type = 'static'

        # 2. Set movement speeds
        if self.type == 'moving':
            # Move speed scales with game speed
            self.move_speed = random.uniform(1, 2) * (speed / 20)
        
        if self.type == 'lane_switch':
            self.next_switch_time = time.time() + random.uniform(1, 2)
            
        self.enabled = True