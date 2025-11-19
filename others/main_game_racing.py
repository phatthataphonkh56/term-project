from ursina import *
import random
import time
import os

from object.player import Player
from object.road import Road
from object.background import Background
from object.obstacle import Obstacle
from object.collectible import Collectible # Import new class

# --- 1. Get the script's directory ---
script_dir = os.path.dirname(os.path.abspath(__file__))

# --- 2. Define the pixelation shader ---
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

# --- 3. Initialize Ursina app with settings ---
app = Ursina(
    fullscreen=True,
    samples=0,
    borderless=True,
    icon='my_icon.ico'  # <-- You would add this line
)

# --- 4. Setup initial game objects ---
player = Player()
ROAD_LENGTH = 50
NUM_ROADS = 50
roads = [Road(z=i * ROAD_LENGTH) for i in range(NUM_ROADS)]
background_texture_path = os.path.join(script_dir, 'city_backg.jpg')
background_u = Background(texture_n=background_texture_path)

# --- 5. Entity Pool Setup ---
NUM_OBSTACLES = 15
NUM_COLLECTIBLES = 10

# Initialize the pools. They are "disabled" at first.
obstacle_pool = []
for i in range(NUM_OBSTACLES):
    obs = Obstacle(z=0, x=0)
    obs.enabled = False 
    obstacle_pool.append(obs)

collectible_pool = []
for i in range(NUM_COLLECTIBLES):
    coll = Collectible(z=0, x=0)
    coll.enabled = False
    collectible_pool.append(coll)

# This tracks the Z position of the "front" of the spawning conga line
farthest_obstacle_z = 0
all_lanes = [-1.5, 0, 1.5] # Define lane positions globally

# --- 6. Camera Setup ---
camera.position = (0, 3, -9)
camera.rotation_x = 9
camera.shader = manual_pixel_shader
target_resolution = (480, 270) # Low-res for pixel effect
camera.set_shader_input('resolution', target_resolution)

# --- 7. UI Setup ---
game_over_text = Text('', origin=(0, 0), scale=2, color=color.red)
score_text = Text('Score: 0', position=(-0.85, 0.45), scale=1.2)

# --- 8. Game State Variables ---
speed = 20
score = 0
next_speed_increase_score = 500

# --- 9. Game Functions ---

def explosion(position):
    """ Creates a one-shot explosion animation. """
    explosion_path = os.path.join(script_dir, 'explode.gif')
    explosion_anim = Animation(
        explosion_path, 
        parent=camera.ui, 
        position=(0,0),
        scale=1.8, 
        fps=12, 
        loop=False
    )
    destroy(explosion_anim, delay=2)

def recycle_obstacle_smart(obs, current_speed):
    """ Recycles a single obstacle, placing it intelligently. """
    global farthest_obstacle_z

    # 1. Set new Z pos (the "conga line")
    # Gap shrinks as speed increases, clamped to a minimum of 20
    gap = max(20, 50 - (current_speed - 20) * 0.75) 
    new_z = farthest_obstacle_z + gap + random.uniform(-3, 3)
    farthest_obstacle_z = new_z # This is the z for the *next* row.

    # 2. Find available lanes at this Z-depth
    # We check for other obstacles *near* this new Z position
    occupied_lanes = [
        o.x for o in obstacle_pool 
        if o.enabled and o != obs and abs(o.z - new_z) < 10
    ]
    available_lanes = [l for l in all_lanes if l not in occupied_lanes]
    
    # 3. Decide what to do
    if not available_lanes:
        # This means all 3 lanes are full! IMPOSSIBLE WALL.
        # So, we disable this obstacle. It becomes the "gap".
        obs.enabled = False
    else:
        # We have at least one open lane. Place the obstacle.
        new_x = random.choice(available_lanes)
        obs.reset(new_z, new_x, current_speed)
        
    # --- (FIXED) Collectible Spawning Logic ---
    # AFTER placing the obstacle, find all *truly* safe lanes
    # This is run every time, even if we made a gap
    occupied_lanes_final = [
        o.x for o in obstacle_pool 
        if o.enabled and abs(o.z - new_z) < 10 # Check all obstacles at this Z
    ]
    safe_lanes = [l for l in all_lanes if l not in occupied_lanes_final]

    if safe_lanes:
        # Try to place a collectible in one of the safe lanes
        try_place_collectible(new_z, safe_lanes)

def try_place_collectible(z, safe_lanes):
    """ Finds a disabled collectible and places it in a random safe lane. """
    coll = next((c for c in collectible_pool if not c.enabled), None)
    if coll:
        x = random.choice(safe_lanes)
        coll.reset(z, x)

def initialize_game_world():
    """ Sets up the initial state of obstacles and collectibles. """
    global farthest_obstacle_z
    
    # Disable all entities
    for obs in obstacle_pool: obs.enabled = False
    for coll in collectible_pool: coll.enabled = False

    # Spawn the initial "conga line" of obstacles
    farthest_obstacle_z = 30 # Start spawning 30 units ahead
    for i in range(NUM_OBSTACLES):
        # We call the recycler to place them one by one
        recycle_obstacle_smart(obstacle_pool[i], 20) 

def restart_game():
    """ Resets the game to its initial state. """
    global speed, score, next_speed_increase_score, farthest_obstacle_z

    player.alive = True
    player.x, player.z = 0, 0
    player.enabled = True
    player.rotation = (0, 90, 0) # Reset rotation
    player.tilt_angle = 0
    
    speed = 20
    score = 0
    next_speed_increase_score = 500
    game_over_text.text = ''

    # Re-build the game world
    initialize_game_world()

    print("Game Restarted")

# --- 10. Main Update Loop ---
def update():
    global speed, score, next_speed_increase_score

    if not player.alive:
        if held_keys['space']:
            restart_game()
        return

    # --- Score & Difficulty ---
    # Score increases faster at higher speeds
    score += time.dt * (speed / 2)
    score_text.text = f"Score: {int(score)}"

    # Increase speed based on score
    if score >= next_speed_increase_score:
        speed += 2
        # Increase the score needed for the *next* level
        next_speed_increase_score += int(next_speed_increase_score * 0.5) 
        print(f"Speed increased: {speed}! Next at {next_speed_increase_score} points.")

    # --- Update Game Objects ---
    for road in roads:
        road.upd(speed, ROAD_LENGTH, roads)

    # --- Update Obstacles ---
    for obs in obstacle_pool:
        if not obs.enabled:
            continue # Skip disabled obstacles

        obs.upd(speed)
        
        # Recycle if it's behind the player
        if obs.z < player.z - 15:
            recycle_obstacle_smart(obs, speed)

        # Check for collision
        if player.intersects(obs).hit:
            player.alive = False
            explosion(player.position)
            player.enabled = False
            game_over_text.text = f"GAME OVER!\nFINAL SCORE: {int(score)}\n\nPress SPACE to restart"
            break
            
    # --- Update Collectibles ---
    for coll in collectible_pool:
        if not coll.enabled:
            continue
        
        coll.upd() # Make it spin
        
        # Recycle if it's behind
        if coll.z < player.z - 15:
            coll.enabled = False # Just disable it, it will be re-used
            
        # Check for collection
        if player.intersects(coll).hit:
            score += 100 # <-- This is where you add points
            coll.enabled = False # "Collect" it
            # Optional: Add a sound effect
            # Audio('coin.wav', autoplay=True) 

# --- 11. Start the Game ---
initialize_game_world() # Set up the world on first launch
app.run()