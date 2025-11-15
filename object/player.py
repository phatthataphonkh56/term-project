from ursina import *
import math
import time
import os # <-- No longer needed

# --- (REMOVED) All os path logic ---

class Player(Entity):
    def __init__(self):
        super().__init__(
            # --- (SIMPLIFIED) ---
            # This path is now relative to the asset_folder (term-project)
            model='pixel_car.glb', 
            # --------------------
            scale=(0.5, 0.5, 0.45),
            position=(0, 0.5, 0),
            rotation_y=90,
            collider='box'
        )
        
        # --- Joystick movement variables ---
        self.alive = True
        self.move_speed = 5
        # --- (MODIFIED) Widen the player's movement range ---
        self.max_x = 2.5 
        # ----------------------------------------
        
        self.tilt_angle = 0
        self.tilt_target = 0
        self.tilt_speed = 10
        self.max_tilt = 20 # Max tilt angle
        
        self.shadow = Entity(
            parent=self,
            model='circle',
            color=color.black33,
            scale=(1.2, 1.2, 1.2),
            position=(0, -0.18, 0),
            rotation_x=90
        )

    def update(self):
        if not self.alive:
            return

        # --- Continuous "Joystick" Movement ---
        move_direction = 0
        if held_keys['a']:
            move_direction -= 1
            self.tilt_target = self.max_tilt # Tilt left
        if held_keys['d']:
            move_direction += 1
            self.tilt_target = -self.max_tilt # Tilt right
            
        if move_direction == 0:
            self.tilt_target = 0 # Return to center

        # Update position
        new_x = self.x + (move_direction * self.move_speed * time.dt)
        
        # Clamp position to the road limits
        self.x = clamp(new_x, -self.max_x, self.max_x)
        # ------------------------------------------

        # --- Tilt Logic ---
        self.tilt_angle = lerp(self.tilt_angle, self.tilt_target, time.dt * self.tilt_speed)
        
        # Apply the tilt by rotating on the Z-axis
        # The base Y-rotation is 90 (facing right)
        self.rotation = (0, -self.tilt_angle, 0)