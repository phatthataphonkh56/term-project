from ursina import *
import math
import time
import os # <-- No longer needed
import pygame
# --- (REMOVED) All os path logic ---
pygame.mixer.init()
class Player(Entity):
    def __init__(self):
        super().__init__(
            # --- (SIMPLIFIED) ---
            # This path is now relative to the asset_folder (term-project)
            model='game_asset/pixel_car.glb', 
            # --------------------
            scale=(0.55, 0.55, 0.5),
            position=(0, 0.1, 1.8),
            rotation_y=90,
            collider='box'
        )
        self.paused = False

        self.honk = pygame.mixer.Sound("game_asset/horn.wav")
        self.honk.set_volume(0.5)
        self.explode_sound = pygame.mixer.Sound("game_asset/explode_sound.wav")
        self.explode_sound.set_volume(0.5)
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
        
        # ---------- SYSTEM: UNDERGROUND ----------
        self.is_diving = False
        self.max_diving_time = 3
        self.diving_timer = 0
        self.final_y = 0.1
        self.cooldown_time = 5
        self.cooldown_timer = 0

        # UI cooldown bar
        self.cooldown_bar = Entity(parent=camera.ui, model='quad', color=color.azure,
                                   scale=(0.3, 0.03), position=(-0.85, -0.45), origin=(-0.5, 0))
        self.cooldown_bar_bg = Entity(parent=camera.ui, model='quad', color=color.gray,
                                      scale=(0.3, 0.03), position=(-0.85, -0.45), origin=(-0.5, 0), z=1)

        self.shadow = Entity(
            parent=self,
            model='circle',
            color=color.black33,
            scale=(1.2, 1.2, 1.2),
            position=(0, -0.18, 0),
            rotation_x=90
        )

    def update(self):
        if self.paused:
            return
        
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

        # =========================================
        #            UNDERGROUND SYSTEM
        # =========================================
        t_pressed = held_keys['t']
        # กด T เพื่อมุด / โผล่ขึ้น
        if t_pressed and not hasattr(self, 't_lock'):   # detect single press
            # ----------------- ถ้ากำลังมุด → โผล่ขึ้น -----------------
            if self.is_diving:
                self.is_diving = False
                self.final_y = 0.1
                self.cooldown_timer = self.cooldown_time  # เริ่ม cooldown ใหม่ทันที

            # ----------------- ถ้าอยู่บนดิน → มุดลง -----------------
            else:
                if self.cooldown_timer <= 0:      # มุดได้เฉพาะตอน cooldown หมด
                    self.is_diving = True
                    self.diving_timer = self.max_diving_time
                    self.final_y = -1.2
            self.t_lock = True
        if not t_pressed and hasattr(self, 't_lock'):
            del self.t_lock
        # ----------------- ขณะมุดอยู่ -----------------
        if self.is_diving:

            self.diving_timer -= time.dt
            # หมดเวลามุด → เด้งขึ้นอัตโนมัติ
            if self.diving_timer <= 0:
                self.is_diving = False
                self.final_y = 0.1
                self.cooldown_timer = self.cooldown_time

        # ----------------- ถ้าอยู่บนดิน → ลด cooldown -----------------
        else:
            if self.cooldown_timer > 0:
                self.cooldown_timer -= time.dt
                if self.cooldown_timer < 0:
                    self.cooldown_timer = 0
        self.y = lerp(self.y, self.final_y, time.dt * 5)
        # ----------------- อัปเดตหลอด cooldown -----------------
        if self.cooldown_timer > 0:
            ratio = 1 - (self.cooldown_timer / self.cooldown_time)
        else:
            ratio = 1

        self.cooldown_bar.scale_x = 0.3 * ratio

        #----------------Honk-------------------
        if held_keys['h']:
            self.honk.play()
