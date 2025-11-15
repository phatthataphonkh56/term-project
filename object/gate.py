from ursina import *
import random
import time

class Gate(Entity):
    def __init__(self, z=0, x=0):
        super().__init__(
            model='cube', # Keep model for collider
            texture='white_cube',  # Use white_cube to allow coloring
            color=color.gray, # Default color
            # --- (MODIFIED) Adjusted scale for thinner doors ---
            scale=(1.4, 2, 0.2), # Thinner door
            # ---------------------------------------------------
            position=(x, 1.05, z),
            collider='box'
        )
        # --- (MODIFIED) Increased transparency slightly ---
        self.alpha = 0.5
        # --------------------------------------------------
        
        self.value = 0
        
        # Add the text to display the value
        self.value_text = Text(
            parent=self,
            text='',
            scale=15, 
            position=(0, 0, -0.6), # Centered
            origin=(0,0),
            color=color.white,
            font='object/MODENINE.TTF' 
        )
        # --- (MODIFIED) Disabled the text background ---
        self.text_bg = Entity(
            parent=self.value_text,
            model='quad',
            color=color.black66,
            scale=(0.3, 0.1),
            position=(0,0,0.01), # Just behind the text
            enabled=False # <-- DISABLED
        )

    def upd(self, speed):
        self.z -= time.dt * speed

    def reset(self, z, x, value, speed):
        self.position = (x, 1.05, z)
        self.value = value
        
        self.value_text.text = f"{value:+}"
        if value > 0:
            self.value_text.color = color.lime # Brighter green
            self.color = color.green
            self.alpha = 0.5
        else:
            self.value_text.color = color.red
            self.color = color.red
            self.alpha = 0.5
            
        self.enabled = True