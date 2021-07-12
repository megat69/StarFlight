"""
Just fly in the space.
"""
from ursina import *
import ursina.application
from random import uniform, randint
from controller import Controller
from asteroids import Asteroid
from math import sqrt
from pypresence import Presence
import time

app = Ursina(fullscreen=True)
window.exit_button.visible = False
ursina.application.development_mode = False

# Setting up Discord Rich Presence
RPC = Presence("864140841341157406")
RPC.connect()
RPC_update_cooldown = 0

# Playing the game's music
music = Audio("assets/music.mp3", loop=True, autoplay=True)

# Create a skybox
skybox = {
    "textures": {
        "back": load_texture(f"assets/skybox/back.png"),
        "bottom": load_texture(f"assets/skybox/bottom.png"),
        "front": load_texture(f"assets/skybox/front.png"),
        "left": load_texture(f"assets/skybox/left.png"),
        "right": load_texture(f"assets/skybox/right.png"),
        "top": load_texture(f"assets/skybox/top.png")
    },
    "entities": {}
}
skybox_scale = 20

# Back
skybox["entities"]["back"] = Entity(
    model="plane",
    texture=skybox["textures"]["back"],
    double_sided=True,
    scale=skybox_scale
)
# Front
skybox["entities"]["front"] = Entity(
    model="plane",
    texture=skybox["textures"]["front"],
    double_sided=True,
    scale=skybox_scale
)
# Left
skybox["entities"]["left"] = Entity(
    model="plane",
    texture=skybox["textures"]["left"],
    double_sided=True,
    scale=skybox_scale
)
# Right
skybox["entities"]["right"] = Entity(
    model="plane",
    texture=skybox["textures"]["right"],
    double_sided=True,
    scale=skybox_scale
)
# Top
skybox["entities"]["top"] = Entity(
    model="plane",
    texture=skybox["textures"]["top"],
    double_sided=True,
    scale=skybox_scale
)
# Bottom
skybox["entities"]["bottom"] = Entity(
    model="plane",
    texture=skybox["textures"]["bottom"],
    double_sided=True,
    scale=skybox_scale
)
# Rotating them properly
skybox["entities"]["back"].rotation = (90, 90, 0)
skybox["entities"]["front"].rotation = (90, 90, 0)
skybox["entities"]["left"].rotation = (0, 90, 90)
skybox["entities"]["right"].rotation = (0, 90, 90)
skybox["entities"]["top"].rotation = (0, 0, 0)
skybox["entities"]["bottom"].rotation = (0, 0, 0)

# Creation of the player
player = Controller(points_enabled=True, ship_model=0)

# Fading in the scene
scene_hider = Entity(parent=camera.ui, model="quad", color=color.rgb(0, 0, 0, 255), scale=3)
scene_hider.animate_color(color.rgb(0, 0, 0, 0), duration=7, curve=curve.out_expo)
destroy(scene_hider, 7)

def tuple_add(tuple_a:tuple, tuple_b:tuple):
    """
    Adds the content of two tuples together.
    If they don't have the same size, the remaining contents of the longest will be scrapped.
    :return: Tuple.
    """
    temp = []
    for i in range(min(len(tuple_a), len(tuple_b))):
        temp.append(tuple_a[i] + tuple_b[i])

    return tuple(temp)

# Creates a list of asteroids and spawns them randomly somewhere in the playground
asteroids_list = [
    Asteroid(
        position=(
            uniform(-skybox_scale/3, skybox_scale/3),
            uniform(-skybox_scale/3, skybox_scale/3),
            uniform(-skybox_scale/3, skybox_scale/3)
        ),
        scale=uniform(0.1, 1),
        player = player
    ) for _ in range(10)
]

asteroid_spawn_cooldown_min = 6
asteroid_spawn_cooldown_max = 8
asteroid_spawn_cooldown = uniform(asteroid_spawn_cooldown_min, asteroid_spawn_cooldown_max)

def update():
    global asteroid_spawn_cooldown
    global asteroid_spawn_cooldown_min
    global asteroid_spawn_cooldown_max
    global RPC_update_cooldown

    # Updates the RPC cooldown
    RPC_update_cooldown -= time.dt
    if RPC_update_cooldown <= 0:
        RPC.update(
            state="Playing in a peaceful atmosphere...",
            details=f"Current points : {player.points}",
            start=time.time()
        )
        RPC_update_cooldown = 15

    if player.alive is False: return

    # Skybox placement
    skybox["entities"]["back"].position = tuple_add(tuple(player.position), (-skybox_scale/2, 0, 0))
    skybox["entities"]["front"].position = tuple_add(tuple(player.position), (skybox_scale/2, 0, 0))
    skybox["entities"]["left"].position = tuple_add(tuple(player.position), (0, 0, skybox_scale/2))
    skybox["entities"]["right"].position = tuple_add(tuple(player.position), (0, 0, -skybox_scale/2))
    skybox["entities"]["top"].position = tuple_add(tuple(player.position), (0, skybox_scale/2, 0))
    skybox["entities"]["bottom"].position = tuple_add(tuple(player.position), (0, -skybox_scale/2, 0))

    # Randomly spawns asteroids
    asteroid_spawn_cooldown -= time.dt
    if asteroid_spawn_cooldown <= 0 or len(asteroids_list) <= 8:
        print("Asteroid spawned !")
        # Adding a movement vector sometimes
        movement_vector = None
        if uniform(0, 1) > 0.8:
            movement_vector = Vec3(
                uniform(-2, -2),
                uniform(-2, -2),
                uniform(-2, -2)
            )

        # Spawining the asteroid
        asteroids_list.append(
            Asteroid(
                position=tuple_add((
                    uniform(-skybox_scale / 3, skybox_scale / 3),
                    uniform(-skybox_scale / 3, skybox_scale / 3),
                    uniform(-skybox_scale / 3, skybox_scale / 3)
                ), player.position),
                scale=uniform(0.1, 1),
                player = player,
                shiny = uniform(0, 1) > 0.9,
                movement_vector=movement_vector
            )
        )

        # Increment the cooldown
        if asteroid_spawn_cooldown_min > 1:
            asteroid_spawn_cooldown_min -= uniform(0, 0.5)
            asteroid_spawn_cooldown_max -= uniform(0, 0.5)
        asteroid_spawn_cooldown = uniform(asteroid_spawn_cooldown_min, asteroid_spawn_cooldown_max)

    # Destroying asteroids too far away
    # Goes all the way through the list of asteroids and destroys them if too far away
    for index, asteroid in enumerate(asteroids_list):
        # Calculates the distance between them : If the distance between the asteroid and the player is superior to
        # four thirds of the skybox scale, it gets deleted
        try:
            if sqrt(
                    (player.position[0] - asteroid.position[0])**2 +
                    (player.position[1] - asteroid.position[1])**2 +
                    (player.position[2] - asteroid.position[2])**2
            ) > 4 * (skybox_scale / 3):
                destroy(asteroid)
                asteroids_list.pop(index)
        except Exception:
            asteroids_list.pop(index)

app.run()
