"""
Just fly in the space.
"""
from ursina import *
import ursina.application
from ursina.shaders import lit_with_shadows_shader
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
    ADVANCED_SETTINGS = settings["advanced_settings"]

    app = Ursina(fullscreen=settings["fullscreen_enabled"])
    window.exit_button.visible = False
    ursina.application.development_mode = False

    if settings["framerate_cap"] is not None:
        from panda3d.core import ClockObject
        globalClock.setMode(ClockObject.MLimited)
        globalClock.setFrameRate(settings["framerate_cap"])


class Controller(Entity):
    def __init__(self, points_enabled:bool=False, ship_model:int=None):
        super().__init__(position=(0, -2.5, 0))
        if HUD["hud_enabled"] is True and HUD["crosshair_enabled"] is True:
            # Crosshair
            self.cursor = Entity(
                parent=camera.ui,
                model='quad',
                color=color.rgba(*ADVANCED_SETTINGS["crosshair_RGBA"]),
                scale=.004
            )

            self.bloom = Entity(parent=camera.ui, model="circle",
                                color=color.rgb(*ADVANCED_SETTINGS["laser_RGBA"][:-1], 0),
                                scale=0.3
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
                f"{ADVANCED_SETTINGS['speed_counter']['text']}{self.speed:.3f}",
                position = tuple(ADVANCED_SETTINGS['speed_counter']['position']),
                color = color.rgb(*ADVANCED_SETTINGS["main_color_RGBA"]),
                font = ADVANCED_SETTINGS["main_font_path"]
            )

        if HUD["hud_enabled"] is True and HUD["closest_asteroid_enabled"] is True:
            # Closest asteroid indicator
            self.closest_asteroid_indicator = Text(
                ADVANCED_SETTINGS["closest_asteroid"]["text"]+"?m",
                position=tuple(ADVANCED_SETTINGS["closest_asteroid"]["position"]),
                color=color.rgb(*ADVANCED_SETTINGS["main_color_RGBA"]),
                font=ADVANCED_SETTINGS["main_font_path"],
                origin=(0, 0)
            )

        """# Compass
        self.compass = Text(
            "Facing : ",
            position=(0, -0.4),
            color=color.rgb(*ADVANCED_SETTINGS["main_color_RGBA"]),
            font=ADVANCED_SETTINGS["main_font_path"],
            origin=(0, 0)
        )"""

        # Other settings
        self.gravity = 0
        self.alive = True

        if points_enabled is True:
            self.points = 0
            if HUD["hud_enabled"] is True and HUD["points_enabled"] is True:
                self.points_counter = Text(
                    str(self.points) + ADVANCED_SETTINGS["points"]["text"],
                    position = tuple(ADVANCED_SETTINGS["points"]["position"]),
                    color = color.rgb(*ADVANCED_SETTINGS["main_color_RGBA"]),
                    font = ADVANCED_SETTINGS["main_font_path"]
                )
        else:
            self.points = None

    def update(self):
        if self.alive:
            if HUD["hud_enabled"] is True and HUD["speed_counter_enabled"] is True:
                # Updating the speed counter
                self.speed_counter.text = f"{ADVANCED_SETTINGS['speed_counter']['text']}{self.speed:.3f}"

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
                    ADVANCED_SETTINGS["closest_asteroid"]["text"] + \
                    f"{closest_asteroid[0][0]:.0f}m - Direction : {skybox_distance[0][1].upper()}"

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
                self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]
                self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
            else:
                self.rotation_y -= held_keys["gamepad right stick x"] * time.dt * CONTROLLER_SENSITIVITY[1]\
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
                Audio(ADVANCED_SETTINGS["audio"]["player_death"], loop=False, autoplay=True)

                # Creating a square on the whole UI that blends in
                self.death_cover = Entity(parent=camera.ui, model="quad", color=color.rgb(0, 0, 0, 0), scale=3)
                self.death_cover.animate_color(color.rgb(0, 0, 0, 255), duration=2, curve=curve.out_expo)
                if HUD["hud_enabled"] is True and HUD["crosshair_enabled"] is True:
                    self.cursor.animate_color(color.rgb(255, 255, 255, 0), duration=2, curve=curve.out_expo)
                    destroy(self.cursor, 2)

                # Adding the death text
                self.death_text = Text(
                    ADVANCED_SETTINGS["death_texts"]["text1"],
                    color=color.rgb(*ADVANCED_SETTINGS["death_texts"]["start_color_RGBA"]),
                    origin=(0, 0)
                )
                if POINTS_ENABLED is True:
                    self.score_death_text = Text(
                        ADVANCED_SETTINGS["death_texts"]["text2"].format(round(self.points)),
                        color=color.rgb(*ADVANCED_SETTINGS["death_texts"]["start_color_RGBA"]),
                        position = (0, -0.05),
                        origin=(0, 0)
                    )
                keybind = "'Shift' + 'Q'" if USING_CONTROLLER is False else "START"
                self.score_exit_text = Text(
                    ADVANCED_SETTINGS["death_texts"]["text3"].format(keybind),
                    color=color.rgb(*ADVANCED_SETTINGS["death_texts"]["start_color_RGBA"]),
                    position = (0, -0.1),
                    origin=(0, 0)
                )
                self.death_text.animate_color(color.rgb(*ADVANCED_SETTINGS["death_texts"]["end_color_RGBA"]),
                                              duration=ADVANCED_SETTINGS["death_texts"]["blend_duration"],
                                              curve=curve.out_expo)
                if POINTS_ENABLED is True:
                    self.score_death_text.animate_color(color.rgb(*ADVANCED_SETTINGS["death_texts"]["end_color_RGBA"]),
                                                        duration=ADVANCED_SETTINGS["death_texts"]["blend_duration"] * 2,
                                                        curve=curve.out_expo)
                self.score_exit_text.animate_color(color.rgb(*ADVANCED_SETTINGS["death_texts"]["end_color_RGBA"]),
                                                   duration=ADVANCED_SETTINGS["death_texts"]["blend_duration"] * 3,
                                                   curve=curve.out_expo)
        elif USING_CONTROLLER is True and held_keys["gamepad start"]:
            quit(0)

    def add_points(self, amount:int=1):
        """
        Adds some points to the player.
        :param amount: The amount of points to add.
        """
        if self.points is not None:
            self.points += amount * self.speed
            if HUD["hud_enabled"] is True and HUD["points_enabled"] is True:
                self.points_counter.text = str(round(self.points)) + ADVANCED_SETTINGS["points"]["text"]

                self.points_counter.position_x = self.points + ADVANCED_SETTINGS["points"]["position"][0]\
                                                 - len(str(self.points)) / 8

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
            self.cursor.color = color.rgb(*ADVANCED_SETTINGS["laser_RGBA"])
            self.cursor.scale = (0.01, 0.30)
            self.cursor.y -= ADVANCED_SETTINGS["laser_duration"]


            self.bloom.animate_color(color.rgb(*ADVANCED_SETTINGS["laser_RGBA"][:-1], ADVANCED_SETTINGS["laser_bloom_effect_alpha"]),
                                     duration=ADVANCED_SETTINGS["laser_duration"])
            invoke(self.bloom.animate_color, color.rgb(*ADVANCED_SETTINGS["laser_RGBA"][:-1], 0),
                   duration=ADVANCED_SETTINGS["laser_duration"], delay=ADVANCED_SETTINGS["laser_duration"])

            def return_to_standard():
                self.cursor.color = color.rgb(*ADVANCED_SETTINGS["crosshair_RGBA"])
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
            asteroid_color = color.rgb(randint(
                *ADVANCED_SETTINGS["asteroid_colors"]["R"]
            ), randint(
                *ADVANCED_SETTINGS["asteroid_colors"]["G"]
            ), randint(
                *ADVANCED_SETTINGS["asteroid_colors"]["B"]
            ))
        else:
            # Gold color if the asteroid is shiny
            asteroid_color = color.rgb(*ADVANCED_SETTINGS["asteroid_colors"]["gold"])
            # Also plays a little sound when one spawns
            Audio(ADVANCED_SETTINGS["audio"]["shiny_appeared"], loop=False, autoplay=True, volume=VOLUME["master"] * VOLUME["sfx"])

        # Asteroid creation
        super().__init__(
            parent=scene,
            model=ADVANCED_SETTINGS["models"]["asteroides"]+f"{randint(1, 5)}.obj",
            texture=load_texture(ADVANCED_SETTINGS["models"]["asteroides_texture"]),
            color=asteroid_color,
            position=position if position is not None else (0, 0, 0),
            scale=scale if scale is not None else 1,
            collider="sphere",
            highlight_color=asteroid_color
            ,shader=lit_with_shadows_shader
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

                # Adds the light
                light = PointLight(parent=scene, position=self.position, shadows=False)
                destroy(light, 0.8)

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
                explosion_sound = ADVANCED_SETTINGS["audio"]["explosion"] if self.shiny is False\
                    else ADVANCED_SETTINGS["audio"]["golden_asteroid_explosion"]
                # Finally plays the audio
                Audio(explosion_sound, loop=False, autoplay=True, volume=volume * VOLUME["master"] * VOLUME["sfx"])

                # Particle creation
                # Create a particle when the ball collides with something
                particle = Entity(model=ADVANCED_SETTINGS["models"]["explosion"], position=self.position, scale=0,
                                  color=color.color(randint(
                                      *ADVANCED_SETTINGS["explosion_particle"]["color"]["H"]
                                  ), uniform(
                                      *ADVANCED_SETTINGS["explosion_particle"]["color"]["S"]
                                  ), uniform(
                                      *ADVANCED_SETTINGS["explosion_particle"]["color"]["V"]
                                  )),
                                  add_to_scene_entities=False, rotation=(
                        randint(0, 360),
                        randint(0, 360),
                        randint(0, 360)
                    ))
                particle.animate_scale(
                    tuple(self.scale)[0] * ADVANCED_SETTINGS["explosion_particle"]["scale"]["min"],
                    tuple(self.scale)[0] * ADVANCED_SETTINGS["explosion_particle"]["scale"]["max"],
                    curve=curve.out_expo
                )
                particle.animate_color(
                    color.color(randint(
                        *ADVANCED_SETTINGS["explosion_particle"]["color"]["H"]
                    ), uniform(
                        *ADVANCED_SETTINGS["explosion_particle"]["color"]["S"]
                    ), uniform(
                        *ADVANCED_SETTINGS["explosion_particle"]["color"]["V"]
                    ), 0), duration=ADVANCED_SETTINGS["explosion_particle"]["duration"],
                    curve=curve.out_expo
                )
                destroy(particle, delay=ADVANCED_SETTINGS["explosion_particle"]["duration"])

                # Screenshake if distance with player is below 2.5 and if not shiny
                if distance(self, player) < ADVANCED_SETTINGS["screenshake"]["distance"] and self.shiny is False:
                    camera.shake(duration=ADVANCED_SETTINGS["screenshake"]["duration"],
                                 magnitude=ADVANCED_SETTINGS["screenshake"]["magnitude"])

                    bloom = Entity(model="sphere", position=self.position,
                                   color=color.rgb(*ADVANCED_SETTINGS["explosion_bloom"]["start_RGBA"]), scale=self.scale)
                    bloom.animate_scale(3, duration=ADVANCED_SETTINGS["explosion_bloom"]["duration"])
                    bloom.animate_color(color.rgb(*ADVANCED_SETTINGS["explosion_bloom"]["end_RGBA"]),
                                        duration=ADVANCED_SETTINGS["explosion_bloom"]["duration"])
                    destroy(bloom, delay=ADVANCED_SETTINGS["explosion_bloom"]["duration"])

                # Destroys the asteroid
                print("Asteroid destroyed.")
                destroy(self, ADVANCED_SETTINGS["explosion_particle"]["duration"])

if __name__ == "__main__":
    # Setting up Discord Rich Presence
    if RICH_PRESENCE_ENABLED is True:
        try:
            RPC = Presence("864140841341157406")
            RPC.connect()
            RPC_update_cooldown = 0
        except Exception as e:
            RICH_PRESENCE_ENABLED = False
            print("Rich Presence has been disabled, since the following error occurred :", e)

    # Playing the game's music
    music = Audio(ADVANCED_SETTINGS["audio"]["music"], loop=True, autoplay=True, volume=VOLUME["master"] * VOLUME["music"])

    # Create a skybox
    skybox = {
        "textures": {
            "back": load_texture(ADVANCED_SETTINGS["skybox_location"] + "back.png"),
            "bottom": load_texture(ADVANCED_SETTINGS["skybox_location"] + "bottom.png"),
            "front": load_texture(ADVANCED_SETTINGS["skybox_location"] + "front.png"),
            "left": load_texture(ADVANCED_SETTINGS["skybox_location"] + "left.png"),
            "right": load_texture(ADVANCED_SETTINGS["skybox_location"] + "right.png"),
            "top": load_texture(ADVANCED_SETTINGS["skybox_location"] + "top.png")
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

    ambient_light = AmbientLight(parent=scene, position=(0, 0, 0))

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
        ) for _ in range(ADVANCED_SETTINGS["default_asteroid_amount"])
    ]

    asteroid_spawn_cooldown_min = ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["min"]
    asteroid_spawn_cooldown_max = ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["max"]
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
                        start=int(time.time())
                    )
                    RPC_update_cooldown = 15
            except Exception as e:
                RICH_PRESENCE_ENABLED = False
                print("Rich Presence has been disabled, since the following error occurred :", e)

        if player.alive is False: return

        # Skybox placement
        skybox["entities"]["back"].position = tuple_add(tuple(player.position), (-SKYBOX_SCALE / 2, 0, 0))
        skybox["entities"]["front"].position = tuple_add(tuple(player.position), (SKYBOX_SCALE / 2, 0, 0))
        skybox["entities"]["left"].position = tuple_add(tuple(player.position), (0, 0, SKYBOX_SCALE / 2))
        skybox["entities"]["right"].position = tuple_add(tuple(player.position), (0, 0, -SKYBOX_SCALE / 2))
        skybox["entities"]["top"].position = tuple_add(tuple(player.position), (0, SKYBOX_SCALE / 2, 0))
        skybox["entities"]["bottom"].position = tuple_add(tuple(player.position), (0, -SKYBOX_SCALE / 2, 0))
        ambient_light.position = tuple(player.position)

        # Randomly spawns asteroids
        asteroid_spawn_cooldown -= time.dt
        if asteroid_spawn_cooldown <= 0 or len(asteroids_list) <= ADVANCED_SETTINGS["minimum_asteroids_alive"]:
            print("Asteroid spawned !")
            # Adding a movement vector sometimes
            movement_vector = None
            if uniform(0, 1) > ADVANCED_SETTINGS["moving_asteroids_spawn_rate"]:
                movement_vector = Vec3(
                    uniform(
                        ADVANCED_SETTINGS["moving_asteroids_vector"]["min"],
                        ADVANCED_SETTINGS["moving_asteroids_vector"]["max"]
                    ),
                    uniform(
                        ADVANCED_SETTINGS["moving_asteroids_vector"]["min"],
                        ADVANCED_SETTINGS["moving_asteroids_vector"]["max"]
                    ),
                    uniform(
                        ADVANCED_SETTINGS["moving_asteroids_vector"]["min"],
                        ADVANCED_SETTINGS["moving_asteroids_vector"]["max"]
                    )
                )

            # Spawning the asteroid
            def spawn_asteroid():
                global asteroids_list
                asteroids_list.append(
                    Asteroid(
                        position=tuple_add((
                            uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3),
                            uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3),
                            uniform(-SKYBOX_SCALE / 3, SKYBOX_SCALE / 3)
                        ), player.position),
                        scale=uniform(
                            ADVANCED_SETTINGS["asteroid_scale"]["min"],
                            ADVANCED_SETTINGS["asteroid_scale"]["max"]
                        ),
                        shiny = uniform(0, 1) > ADVANCED_SETTINGS["golden_asteroids_spawn_rate"],
                        movement_vector=movement_vector
                    )
                )
            spawn_asteroid()
            while distance(player, asteroids_list[-1]) < 2:
                destroy(asteroids_list[-1])
                asteroids_list.pop()
                spawn_asteroid()

            # Increment the cooldown
            if asteroid_spawn_cooldown_min > ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["final_cooldown_between_spawns"]:
                asteroid_spawn_cooldown_min -= uniform(
                    ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["cooldown_reduction"]["min"],
                    ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["cooldown_reduction"]["max"]
                )
                asteroid_spawn_cooldown_max -= uniform(
                    ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["cooldown_reduction"]["min"],
                    ADVANCED_SETTINGS["asteroid_spawn_cooldown"]["cooldown_reduction"]["max"]
                )
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
