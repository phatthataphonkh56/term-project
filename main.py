from ursina import *
import random
import time
import os

from object.player import Player
from object.road import Road
from object.background import Background
from object.obstacle import Obstacle
from object.gate import Gate 
import pygame
pygame.mixer.init()
pygame.mixer.music.load("game_asset/bgm.wav")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(loops=-1)



app = Ursina(
    fullscreen=True,
    samples=0,
    borderless=True,
)
# --------------------------------
# --- Find textures *once* ---
wall_textures = []
if os.path.exists('obstacle_pic'):
    try:
        for file in os.listdir('obstacle_pic'):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                wall_textures.append(file) 
    except Exception as e:
        print(f"Error loading obstacle textures: {e}")
        
if not wall_textures:
    print("Warning: No obstacle textures found. Using 'white_cube' as fallback.")
    wall_textures = ['white_cube']
# ----------------------------------

# --- Shader code (Unchanged) ---
pixelation_shader_code = '''
#version 130
uniform sampler2D tex;
uniform vec2 resolution;
in vec2 uv;
out vec4 color;
void main() {
    vec2 block_uv = floor(uv * resolution) / resolution;
    color = texture(tex, block_uv);
}
'''
manual_pixel_shader = Shader(fragment=pixelation_shader_code)
# -----------------------------

player = Player()
ROAD_LENGTH = 50
NUM_ROADS = 50
roads = [Road(z=i * ROAD_LENGTH) for i in range(NUM_ROADS)]
background_u = Background('game_asset/city_backg.jpg')

# --- Entity Pool Setup (Unchanged) ---
NUM_OBSTACLES = 15
NUM_GATES = 30 

obstacle_pool = []
for i in range(NUM_OBSTACLES):
    obs = Obstacle(z=0, x=0, textures_list=wall_textures)
    obs.enabled = False 
    obstacle_pool.append(obs)

gate_pool = [] 
for i in range(NUM_GATES):
    gate = Gate(z=0, x=0) 
    gate.enabled = False
    gate_pool.append(gate)
# ------------------------------------

camera.position = (0, 3, -9)
camera.rotation_x = 9
camera.shader = manual_pixel_shader
target_resolution = (480, 270)
camera.set_shader_input('resolution', target_resolution)

# --- UI Setup (Unchanged) ---

skill_text = Text(
    parent=camera.ui,
    text="T Underground\nH Honk\nP Pause the game",
    position=(-0.85, -0.35),
    scale=1.1,
    color=color.azure,
    font='object/MODENINE.TTF'
)

# --- High Score ---
high_score = 0
high_score_file = "game_asset/highscore.txt"

if high_score_file:
    try:
        with open(high_score_file, "r") as f:
            high_score = int(f.read().strip())
    except:
        high_score = 0



game_over_text = Text(
    parent=camera.ui, 
    text='', 
    origin=(0, 0), 
    scale=2, 
    color=color.red, 
    font='object/MODENINE.TTF' 
)
high_score_text = Text(
    parent=camera.ui,
    text=f"High Score: {high_score}",
    position=(-0.85, 0.45),
    scale=1.2,
    color=color.yellow,
    font='object/MODENINE.TTF'
)
score_text = Text(
    parent=camera.ui, 
    text='Score: 0', 
    position=(-0.85, 0.42), 
    scale=1.2, 
    background=False, 
    font='object/MODENINE.TTF' 
)
# --- (NEW) Score Multiplier UI ---
multiplier_text = Text(
    parent=camera.ui,
    text='x1',
    position=(-0.85, 0.39), # Below the score
    scale=1.2,
    background=False,
    color=color.cyan,
    font='object/MODENINE.TTF'
)


# --- Pause System ---
paused = False

pause_text = Text(
    parent=camera.ui,
    text='PAUSED',
    origin=(0,0),
    scale=2,
    color=color.azure,
    enabled=False,
    font='object/MODENINE.TTF'
)
# ---------------------------------

speed = 20
score = 0
next_speed_increase_score = 500
score_level_step = 400 

# --- (NEW) Multiplier Variables ---
score_multiplier = 1
next_multiplier_score = 1000 # First multiplier at 1000 points
# ----------------------------------

spawn_timer = 0.5 
spawn_interval = 1.5 
last_spawn_type = '' # To prevent spawning gates twice in a row

# --- Explosion function (Unchanged) ---
def explosion(position):
    try:
        if os.path.exists('game_asset/explode.gif'):
            explosion_anim = Animation(
                'game_asset/explode.gif', 
                parent=camera.ui, position=(0,0),
                scale=1.8, fps=12, loop=False, autoplay=True
            )
            destroy(explosion_anim, delay=2)
        else:
            print("Warning: 'explode.gif' not found.")
    except ImportError:
        print("Warning: 'imageio' module not installed. Skipping explosion animation.")
        print("Install it by running: pip install imageio")
    except Exception as e:
        print(f"Explosion error: {e}")
# -------------------------------------------

# --- Helper function to check spawn zone (Unchanged) ---
def is_spawn_zone_clear(z, margin=20):
    """Checks if a 'bubble' around the spawn Z is clear of entities."""
    all_entities = obstacle_pool + gate_pool
    for entity in all_entities:
        if entity.enabled and abs(entity.z - z) < margin:
            return False # Zone is not clear
    return True # Zone is clear
# -------------------------------------------


# --- (REWORKED) "Pattern-Based" Spawner ---
def recycle_entity(current_speed):
    """Spawns a pre-designed 'pattern' of entities."""
    global last_spawn_type
    
    # 1. Check if zone is clear
    spawn_z = player.z + 100 # Spawn 100 units ahead
    if not is_spawn_zone_clear(spawn_z):
        return 
    
    # 2. Define our "chunks" (patterns)
    all_patterns = ['single_wall', 'double_wall_gap', 'center_squeeze', 'gate_row']
    
    # --- (NEW) Prevent spawning two gate rows back-to-back ---
    if last_spawn_type == 'gate_row':
        all_patterns.remove('gate_row')
    
    spawn_pattern = random.choice(all_patterns)
    last_spawn_type = spawn_pattern # Remember what we spawned
    
    # 3. Get free entities from the pool and place them
    all_lanes = [-2, 0, 2]
    
    if spawn_pattern == 'single_wall':
        entity = next((o for o in obstacle_pool if not o.enabled), None)
        if entity:
            lane = random.choice(all_lanes)
            x_offset = random.uniform(-0.3, 0.3)
            entity.reset(spawn_z, lane + x_offset, current_speed, wall_textures)

    elif spawn_pattern == 'double_wall_gap':
        # Find 2 free obstacles
        entities = [o for o in obstacle_pool if not o.enabled]
        if len(entities) >= 2:
            lanes_to_spawn = random.sample(all_lanes, 2)
            for i in range(2):
                lane = lanes_to_spawn[i]
                x_offset = random.uniform(-0.3, 0.3)
                entities[i].reset(spawn_z, lane + x_offset, current_speed, wall_textures)
    
    elif spawn_pattern == 'center_squeeze':
        # Find 2 free obstacles
        entities = [o for o in obstacle_pool if not o.enabled]
        if len(entities) >= 2:
            # Spawn on left and right lanes
            x_offset_1 = random.uniform(-0.3, 0.3)
            entities[0].reset(spawn_z, -2 + x_offset_1, current_speed, wall_textures)
            x_offset_2 = random.uniform(-0.3, 0.3)
            entities[1].reset(spawn_z, 2 + x_offset_2, current_speed, wall_textures)

    elif spawn_pattern == 'gate_row':
        # Find 3 free gates
        free_gates = [g for g in gate_pool if not g.enabled]
        if len(free_gates) < 3:
            # Not enough gates, spawn a single wall instead
            last_spawn_type = 'single_wall' # Correct our memory
            entity = next((o for o in obstacle_pool if not o.enabled), None)
            if entity:
                lane = random.choice(all_lanes)
                x_offset = random.uniform(-0.3, 0.3)
                entity.reset(spawn_z, lane + x_offset, current_speed, wall_textures)
            return # Exit
        
        gates_to_spawn = free_gates[:3]
        
        # Decide on the door combo (1 good or 2 good)
        lanes = [-2, 0, 2]
        
        # Base values
        good_val = 200 + int((current_speed - 20) * 5)
        bad_val = -100 - int((current_speed - 20) * 2.5)
        
        values = []
        if random.random() < 0.5: # One good door
            values = [good_val, bad_val, bad_val]
        else: # Two good doors
            values = [good_val, good_val, bad_val]
        
        random.shuffle(values)
        
        # Reset and place the 3 gates
        for i in range(3):
            gate = gates_to_spawn[i]
            x_pos = lanes[i]
            value = values[i]
            gate.reset(spawn_z, x_pos, value, current_speed)
# -------------------------------------------
def toggle_pause():
    global paused
    paused = not paused
    player.paused = paused   
    pause_text.enabled = paused
    if paused:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()

# --- (MODIFIED) Restart Game ---
def restart_game():
    global speed, score, next_speed_increase_score, spawn_timer, spawn_interval
    global score_multiplier, next_multiplier_score, last_spawn_type

    player.alive = True
    player.x = 0
    player.tilt_angle = 0
    player.tilt_target = 0
    player.enabled = True
    speed = 20
    score = 0
    next_speed_increase_score = 500 # For speed
    
    # --- (NEW) Reset multiplier ---
    score_multiplier = 1
    next_multiplier_score = 1000 # For multiplier
    multiplier_text.text = 'x1'
    # ------------------------------
    pygame.mixer.music.stop()
    pygame.mixer.music.play(loops=-1)
    game_over_text.text = ''
    
    spawn_timer = 0.5
    spawn_interval = 1.5
    last_spawn_type = ''

    for obs in obstacle_pool: obs.enabled = False
    for gate in gate_pool: gate.enabled = False

    print("Game Restarted")

# --- (MAIN UPDATE LOOP) ---
def update():
    global speed, score, next_speed_increase_score, spawn_timer, spawn_interval
    global score_multiplier, next_multiplier_score
    global paused,high_score
    
    if held_keys['p']:
        toggle_pause()
        time.sleep(0.25)  

    if paused:
        return

    if not player.alive:
        if held_keys['space']:
            restart_game()
        return

    # --- (MODIFIED) Score now uses multiplier ---
    score += (time.dt * (speed / 2)) * score_multiplier
    # --------------------------------------------
    score_text.text = f"Score: {int(score)}"

    if int(score) > high_score:
        high_score_text.text = f"High Score: {int(score)}"

    if score < 0:
        pygame.mixer.music.pause()
        player.explode_sound.play()
        player.alive = False
        explosion(player.position)
        player.enabled = False
        game_over_text.text = f"GAME OVER!\nFINAL SCORE: {int(score)}\n\nPress SPACE to restart"
        return
    # --- Difficulty level-up logic ---
    if score >= next_speed_increase_score:
        speed += 2
        next_speed_increase_score += score_level_step 
        print(f"Speed increased: {speed}! Next at {next_speed_increase_score} points.")
        
    # --- (NEW) Multiplier level-up logic ---
    if score >= next_multiplier_score:
        score_multiplier += 1
        next_multiplier_score += 1000 # Next multiplier in another 1000 points
        multiplier_text.text = f'x{score_multiplier}'
        print(f"Multiplier Increased: x{score_multiplier}!")
    # -------------------------------------

    # --- Timer-based Spawning ---
    spawn_timer -= time.dt
    if spawn_timer <= 0:
        recycle_entity(speed) # Call the spawner
        
        # More aggressive spawn interval
        spawn_interval = max(0.35, 1.5 - (speed - 20) * 0.04) 
        spawn_timer = spawn_interval
    # --------------------------------

    for road in roads:
        road.upd(speed, ROAD_LENGTH, roads)

    # --- Update Obstacles (Unchanged) ---
    for obs in obstacle_pool:
        if not obs.enabled:
            continue 
        obs.upd(speed)
        if obs.z < player.z - 15:
            obs.enabled = False
        if player.intersects(obs).hit:
            pygame.mixer.music.pause()
            player.alive = False
            explosion(player.position)
            player.explode_sound.play()
            player.enabled = False
            game_over_text.text = f"GAME OVER!\nFINAL SCORE: {int(score)}\n\nPress SPACE to restart"
            if int(score) > high_score:
                high_score = int(score)
                with open(high_score_file, "w") as f:
                    f.write(str(high_score))
            break
            
    # --- Update Gates (Unchanged) ---
    for gate in gate_pool:
        if not gate.enabled:
            continue
        gate.upd(speed) 
        if gate.z < player.z - 15:
            gate.enabled = False 
        if player.intersects(gate).hit:
            score += gate.value 
            gate.enabled = False 
            # (Optional) Add a sound!
            # if os.path.exists('coin.wav'):
            #     Audio('coin.wav', autoplay=True) 

app.run()