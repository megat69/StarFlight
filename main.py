"""
Just fly in the space.
"""
from ursina import *
import ursina.application
from random import uniform, randint
from math import sqrt
from pypresence import Presence
import time
import json


# Settings
with open("settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)
    SKYBOX_SCALE = settings["skybox_scale"]
    SHIP_MODEL = settings["ship_model"]
    VOLUME = settings["volume"]
    RICH_PRESENCE_ENABLED = settings["rich_presence_enabled"]
    MOUSE_SENSITIVITY = settings["mouse_sensitivity"]
    CONTROLLER_SENSITIVITY = tuple(settings["controller_sensitivity"])
    USING_CONTROLLER = settings["using_controller"]
    CONTROLLER_AXIS_INVERSION = (settings["controller_invert_y_axis"], settings["controller_invert_x_axis"])
    HUD = settings["hud"]
    POINTS_ENABLED = settings["points_enabled"]

    app = Ursina(fullscreen=settings["fullscreen_enabled"])
    window.exit_button.visible = False
    ursina.application.development_mode = False

class Controller(Entity):
    def __init__(self, points_enabled:bool=False, ship_model:int=None):
        super().__init__(position=(0, -2.5, 0))
        if HUD["hud_enabled"] is True and HUD["crosshair_enabled"] is True:
            # Crosshair
            self.cursor = Entity(
                parent=camera.ui,
                model='quad',
                color=color.white,
                scale=.004
            )

        # Player speed, height, and camera pivot
        self.speed = 1
        self.height = 1
        self.camera_pivot = Entity(parent=self, y=self.height)

        # Camera settings
        camera.parent = self.camera_pivot
        camera.position = (0,0,0)
        camera.rotation = (0,0,0)
        camera.fov = 90
        mouse.locked = True
        if USING_CONTROLLER is False: self.mouse_sensitivity = Vec2(MOUSE_SENSITIVITY, MOUSE_SENSITIVITY)

        # Ship inside
        if ship_model is not None:
            self.ship_inside = Entity(
                parent=camera.ui,
                model="quad",
                texture=f"assets/ship_model_{ship_model}.png",
                scale=(1.85, 1)
            )
            self.ship_number = ship_model
        else:
            self.ship_inside = None

        # Speed counter
        if HUD["hud_enabled"] is True and HUD["speed_counter_enabled"] is True:
            self.speed_counter = Text(
                f"Speed : {self.speed:.3f}",
                position = (-0.85, -0.45),
                color = color.rgb(163, 251, 255),
                font = "assets/font/chintzy_cpu_brk/chintzy.ttf"
            )

        if HUD["hud_enabled"] is True and HUD["closest_asteroid_enabled"] is True:
            # Closest asteroid indicator
            self.closest_asteroid_indicator = Text(
                "Closest asteroid : m",
                position=(0, -0.45),
                color=color.rgb(163, 251, 255),
                font="assets/font/chintzy_cpu_brk/chintzy.ttf",
                origin=(0, 0)
            )

        """# Compass
        self.compass = Text(
            "Facing : ",
            position=(0, -0.4),
            color=color.rgb(163, 251, 255),
            font="assets/font/chintzy_cpu_brk/chintzy.ttf",
            origin=(0, 0)
        )"""

        # Other settings
        self.gravity = 0
        self.alive = True

        if points_enabled is True:
            self.points = 0
            if HUD["hud_enabled"] is True and HUD["points_enabled"] is True:
                self.points_counter = Text(
                    f"{self.points} PTS",
                    position = (0.8, -0.45),
                    color = color.rgb(163, 251, 255),
                    font = "assets/font/chintzy_cpu_brk/chintzy.ttf"
                )
        else:
            self.points = None


    def update(self):
        if self.alive:
            if HUD["hud_enabled"] is True and HUD["speed_counter_enabled"] is True:
                # Updating the speed counter
                self.speed_counter.text = f"Speed : {self.speed:.3f}"

            if HUD["hud_enabled"] is True and HUD["closest_asteroid_enabled"] is True:
                def sort_first(elem):
                    """Sorting key."""
                    return elem[0]
                closest_asteroid = []
                for index, asteroid in enumerate(asteroids_list):
                    try:
                        if isinstance(asteroid, Asteroid):
                            closest_asteroid.append((distance(self, asteroid), asteroid))
                    except Exception:
                        pass
                closest_asteroid.sort(key=sort_first)
                # Checking on which side of the skybox it is
                skybox_distance = []
                for side in skybox["entities"]:
                    skybox_distance.append((distance(closest_asteroid[0][1], skybox["entities"][side]), side))
                skybox_distance.sort(key=sort_first)
                # Updating the closest asteroid indicator by finding the closest asteroid
                self.closest_asteroid_indicator.text = \
                    f"Closest asteroid : {closest_asteroid[0][0]:.0f}m - Direction : {skybox_distance[0][1].upper()}"

            self.direction = Vec3(self.forward).normalized()

            """# Displaying which side is behind you
            side_facing = raycast(self.position+Vec3(0,0.5,0), self.direction, ignore=(self, Asteroid), debug=True).entity
            name = "UNKNOWN"
            for face_name in skybox["entities"]:
                if side_facing == skybox["entities"][face_name]:
                    name = face_name
            self.compass.text = f"Facing : {name}"
            """

            # Speed modification
            if self.speed > 0.2 and (held_keys["control"] or held_keys["gamepad left shoulder"]): self.speed -= 0.25 * time.dt
            if self.speed < 2 and (held_keys["shift"] or held_keys["gamepad right shoulder"]):    self.speed += 0.25 * time.dt

            # Movement updates
            if USING_CONTROLLER is False:
                self.camera_pivot.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]
                self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
            else:
                self.camera_pivot.rotation_y -= held_keys["gamepad right stick x"] * time.dt * CONTROLLER_SENSITIVITY[1]\
                                   * (-1 if CONTROLLER_AXIS_INVERSION[1] is True else 1)
                self.camera_pivot.rotation_x += held_keys["gamepad right stick y"] * time.dt * CONTROLLER_SENSITIVITY[0]\
                                                * (-1 if CONTROLLER_AXIS_INVERSION[0] is True else 1)

            # This ↓ blocks the camera between -90 degrees and 90 degrees vertical
            if USING_CONTROLLER is False:
                self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

            feet_ray = raycast(self.position+Vec3(0,0.5,0), self.direction, ignore=(self,), distance=.5, debug=False)
            head_ray = raycast(self.position+Vec3(0,self.height-.1,0), self.direction, ignore=(self,), distance=.5, debug=False)
            if not feet_ray.hit and not head_ray.hit:
                self.position += camera.forward * self.speed * time.dt
            else:
                # If the raycast hits, then the player collided with something.
                # They are therefore dead.
                self.alive = False
                # Playing the death audio
                Audio("assets/player_death.wav", loop=False, autoplay=True)

                # Creating a square on the whole UI that blends in
                self.death_cover = Entity(parent=camera.ui, model="quad", color=color.rgb(0, 0, 0, 0), scale=3)
                self.death_cover.animate_color(color.rgb(0, 0, 0, 255), duration=2, curve=curve.out_expo)
                if HUD["hud_enabled"] is True and HUD["crosshair_enabled"] is True:
                    self.cursor.animate_color(color.rgb(255, 255, 255, 0), duration=2, curve=curve.out_expo)
                    destroy(self.cursor, 2)

                # Adding the death text
                self.death_text = Text(
                    "You are dead.",
                    color=color.rgb(0, 0, 0, 0),
                    origin=(0, 0)
                )
                if POINTS_ENABLED is True:
                    self.score_death_text = Text(
                        f"You scored {self.points} points.",
                        color=color.rgb(0, 0, 0, 0),
                        position = (0, -0.05),
                        origin=(0, 0)
                    )
                keybind = "'Shift' + 'Q'" if USING_CONTROLLER is False else "START"
                self.score_exit_text = Text(
                    f"Press {keybind} to exit.",
                    color=color.rgb(0, 0, 0, 0),
                    position = (0, -0.1),
                    origin=(0, 0)
                )
                self.death_text.animate_color(color.rgb(255, 255, 255, 255), duration=2, curve=curve.out_expo)
                if POINTS_ENABLED is True:
                    self.score_death_text.animate_color(color.rgb(255, 255, 255, 255), duration=4, curve=curve.out_expo)
                self.score_exit_text.animate_color(color.rgb(255, 255, 255, 255), duration=6, curve=curve.out_expo)
        elif USING_CONTROLLER is True and held_keys["gamepad start"]:
            quit(0)

    def add_points(self, amount:int=1):
        """
        Adds some points to the player.
        :param amount: The amount of points to add.
        """
        if self.points is not None:
            self.points += amount
            if HUD["hud_enabled"] is True and HUD["points_enabled"] is True:
                self.points_counter.text = f"{self.points} PTS"

                self.points_counter.position_x = 0.8 - len(str(self.points)) / 8

    def input(self, key):
        if (
            held_keys["space"]
            or held_keys["gamepad alt"]
            or held_keys["gamepad a"]
            or held_keys["gamepad left alt"]
            or held_keys["gamepad left trigger"] > 0.5
            or held_keys["gamepad right trigger"] > 0.5
        ) and self.ship_inside is not None\
                and HUD["hud_enabled"] is True and HUD["crosshair_enabled"] is True:
            # Hitscan code
            self.cursor.color = color.lime
            self.cursor.scale = (0.01, 0.30)
            self.cursor.y -= 0.15

            def return_to_standard():
                self.cursor.color = color.white
                self.cursor.scale = (0.004, 0.004)
                self.cursor.y += 0.15

            invoke(return_to_standard, delay=0.4)

class Asteroid(Button):
    """
    The asteroids of the game.
    """

    def __init__(self, position=None, scale=None, shiny:bool=False, movement_vector=None):
        # Assigns a random color to the asteroid
        if shiny is False:
            asteroid_color = color.rgb(randint(63, 67), randint(38, 46), randint(38, 46))
        else:
            # Gold color if the asteroid is shiny
            asteroid_color = color.gold
            # Also plays a little sound when one spawns
            Audio("assets/shiny_appeared.wav", loop=False, autoplay=True, volume=VOLUME["master"] * VOLUME["sfx"])

        # Asteroid creation
        super().__init__(
            parent=scene,
            model=f"assets/asteroides/{randint(1, 5)}.obj",
            texture=load_texture("assets/asteroides/Material.001_albedo.jpeg"),
            color=asteroid_color,
            position=position if position is not None else (0, 0, 0),
            scale=scale if scale is not None else 1,
            collider="sphere",
            highlight_color=asteroid_color
        )
        # Sets the fact that the asteroid is destroyable
        self.destroyable = True
        # Remembers if it is shiny or not
        self.shiny = shiny
        # Adds a rotation
        self.random_rotation_vector = Vec3(uniform(-2, 2), uniform(-2, 2), uniform(-2, 2))
        # Adds the movement if needed
        self.movement_vector = movement_vector

    def update(self):
        self.rotation += self.random_rotation_vector
        if self.movement_vector is not None:
            self.position += self.movement_vector * time.dt

    def input(self, key):
        if self.hovered:
            if key in (
                    "space", "gamepad alt", "gamepad left alt",
                    "gamepad a", "gamepad left trigger", "gamepad right trigger"
            ) and self.destroyable is True and (player is None or player.alive is True):
                self.visible = False
                self.destroyable = False
                self.collider = None

                # Gives the points to the player
                points = 1 if self.shiny is False else 5
                if self.movement_vector is not None:
                    points += 2
                player.add_points(points)

                # Plays the explosion sound
                # If there is no defined player, plays the sound at volume 0.25
                if player is None:
                    volume = 0.25
                else:
                    # If there is a player, the volume will depend on the distance with them ; the further they are,
                    # the quieter it will be
                    volume = 1 / distance(player, self) * 1.5
                # If this is a shiny asteroid, we play it louder
                if self.shiny is True:
                    volume *= 2
                elif volume > 0.75:
                    volume = 0.75
                # Locates the correct explosion sound depending on if the asteroid is shiny or not
                explosion_sound = "assets/explosion.mp3" if self.shiny is False else "assets/golden_asteroid.wav"
                # Finally plays the audio
                Audio(explosion_sound, loop=False, autoplay=False, volume=volume * VOLUME["master"] * VOLUME["sfx"]).play()

                # Particle creation
                # Create a particle when the ball collides with something
                particle = Entity(model='assets/explosion/explosion.obj', position=self.position, scale=0,
                                  color=color.color(randint(0, 44), uniform(0.7, 1), uniform(0.89, 1)),
                                  add_to_scene_entities=False, rotation=(
                        randint(0, 360),
                        randint(0, 360),
                        randint(0, 360)
                    ))
                print(self.scale)
                particle.animate_scale(tuple(self.scale)[0] * 0.2, tuple(self.scale)[0] * 1.8, curve=curve.out_expo)
                particle.animate_color(color.clear, duration=2, curve=curve.out_expo)
                destroy(particle, delay=2)

                # Destroys the asteroid
                print("Asteroid destroyed.")
                destroy(self, 2)

if __name__ == "__main__":
    # Setting up Discord Rich Presence
    if RICH_PRESENCE_ENABLED is True:
        try:
            RPC = Presence("864140841341157406")
            RPC.connect()
            RPC_update_cooldown = 0
        except Exception as e:
            RICH_PRESENCE_ENABLED = False
            print("Rich Presence has been disabled, since the following error occured :", e)

    # Playing the game's music
    music = Audio("assets/music.mp3", loop=True, autoplay=True, volume=VOLUME["master"] * VOLUME["music"])

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
    skybox_args = {
        "double_sided": True,
        "scale": SKYBOX_SCALE,
        "collider": "box"
    }
    # Back
    skybox["entities"]["back"] = Entity(model="plane", texture=skybox["textures"]["back"], **skybox_args)
    # Front
    skybox["entities"]["front"] = Entity(model="plane", texture=skybox["textures"]["front"], **skybox_args)
    # Left
    skybox["entities"]["left"] = Entity(model="plane", texture=skybox["textures"]["left"], **skybox_args)
    # Right
    skybox["entities"]["right"] = Entity(model="plane", texture=skybox["textures"]["right"], **skybox_args)
    # Top
    skybox["entities"]["top"] = Entity(model="plane", texture=skybox["textures"]["top"], **skybox_args)
    # Bottom
    skybox["entities"]["bottom"] = Entity(model="plane", texture=skybox["textures"]["bottom"], **skybox_args)
    # Rotating them properly
    skybox["entities"]["back"].rotation = (90, 90, 0)
    skybox["entities"]["front"].rotation = (90, 90, 0)
    skybox["entities"]["left"].rotation = (0, 90, 90)
    skybox["entities"]["right"].rotation = (0, 90, 90)
    skybox["entities"]["top"].rotation = (0, 0, 0)
    skybox["entities"]["bottom"].rotation = (0, 0, 0)

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

    # Creation of the player
    player = Controller(points_enabled=POINTS_ENABLED, ship_model=SHIP_MODEL)

    # Creates a list of asteroids and spawns them randomly somewhere in the playground
    asteroids_list = [
        Asteroid(
            position=(
                uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3),
                uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3),
                uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3)
            ),
            scale=uniform(0.1, 1)
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
        global RICH_PRESENCE_ENABLED

        # Updates the RPC cooldown
        if RICH_PRESENCE_ENABLED is True:
            try:
                RPC_update_cooldown -= time.dt
                if RPC_update_cooldown <= 0:
                    RPC.update(
                        state="Playing in a peaceful atmosphere...",
                        details=f"Current points : {player.points}",
                        start=time.time()
                    )
                    RPC_update_cooldown = 15
            except Exception as e:
                RICH_PRESENCE_ENABLED = False
                print("Rich Presence has been disabled, since the following error occured :", e)

        if player.alive is False: return

        # Skybox placement
        skybox["entities"]["back"].position = tuple_add(tuple(player.position), (-SKYBOX_SCALE / 2, 0, 0))
        skybox["entities"]["front"].position = tuple_add(tuple(player.position), (SKYBOX_SCALE / 2, 0, 0))
        skybox["entities"]["left"].position = tuple_add(tuple(player.position), (0, 0, SKYBOX_SCALE / 2))
        skybox["entities"]["right"].position = tuple_add(tuple(player.position), (0, 0, -SKYBOX_SCALE / 2))
        skybox["entities"]["top"].position = tuple_add(tuple(player.position), (0, SKYBOX_SCALE / 2, 0))
        skybox["entities"]["bottom"].position = tuple_add(tuple(player.position), (0, -SKYBOX_SCALE / 2, 0))

        # Randomly spawns asteroids
        asteroid_spawn_cooldown -= time.dt
        if asteroid_spawn_cooldown <= 0 or len(asteroids_list) <= 8:
            print("Asteroid spawned !")
            # Adding a movement vector sometimes
            movement_vector = None
            if uniform(0, 1) > 0.8:
                movement_vector = Vec3(
                    uniform(-2, 2),
                    uniform(-2, 2),
                    uniform(-2, 2)
                )

            # Spawining the asteroid
            asteroids_list.append(
                Asteroid(
                    position=tuple_add((
                        uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3),
                        uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3),
                        uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3)
                    ), player.position),
                    scale=uniform(0.1, 1),
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
                ) > 4 * (SKYBOX_SCALE / 3):
                    destroy(asteroid)
                    asteroids_list.pop(index)
            except Exception:
                asteroids_list.pop(index)

    app.run()
