from ursina import *
import random
import time


from object.player import Player
from object.road import Road
from object.background import Background
from object.obstacle import Obstacle


app = Ursina()

player = Player()

ROAD_LENGTH = 50
NUM_ROADS = 50
roads = [Road(z=i * ROAD_LENGTH) for i in range(NUM_ROADS)]

background_u = Background(texture_n='city_backg.jpg')

types = ['static', 'moving', 'lane_switch']
obstacles = [Obstacle(z=30 + i * 40, obstacle_type=random.choice(types)) for i in range(3)]

camera.position = (0, 3, -9)
camera.rotation_x = 9

game_over_text = Text('', origin=(0, 0), scale=2, color=color.red)
score_text = Text('Score: 0', position=(-0.85, 0.45), scale=1.2)

speed = 20
difficulty_timer = 0
score = 0
spawn_timer = 0
spawn_interval = 8
max_obstacles = 30


def spawn_obstacle():
    new_z = player.z + random.randint(120, 200)
    obstacles.append(Obstacle(new_z))
    print("obstacle: ", len(obstacles))


def restart_game():
    global speed, difficulty_timer, score, spawn_timer, spawn_interval

    player.alive = True
    player.x, player.z = 0, 0
    player.lane = 0
    player.target_x = 0

    speed = 20
    spawn_timer = 0
    spawn_interval = 8
    difficulty_timer = 0
    score = 0
    game_over_text.text = ''

    for i, obs in enumerate(obstacles):
        obs.z = 30 + i * 40
        obs.x = random.choice([-1.5, 0, 1.5])

    while len(obstacles) > 3:
        obs = obstacles.pop()
        destroy(obs)

    print("Game Restarted")


def update():
    global speed, difficulty_timer, score, spawn_timer, spawn_interval

    if not player.alive:
        if held_keys['space']:
            restart_game()
        return

    difficulty_timer += time.dt
    if difficulty_timer >= 10:
        difficulty_timer = 0
        speed += 2
        print(f"Speed increased: {speed}")

    score += time.dt * 10
    score_text.text = f"Score: {int(score)}"

    for road in roads:
        road.upd(speed, ROAD_LENGTH, roads)

    for obs in obstacles:
        obs.upd(speed)
        if player.intersects(obs).hit:
            player.alive = False
            game_over_text.text = f"GAME OVER!\nFINAL SCORE: {int(score)}\n\nPress SPACE to restart"
            break

    spawn_timer += time.dt
    if spawn_timer >= spawn_interval and len(obstacles) < max_obstacles:
        spawn_timer = 0
        spawn_obstacle()


app.run()