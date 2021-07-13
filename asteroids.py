from ursina import *
from random import randint, uniform
import json

with open("settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)
    VOLUME = settings["volume"]

class Asteroid(Button):
    """
    The asteroids of the game.
    """

    def __init__(self, position=None, scale=None, player=None, shiny:bool=False, movement_vector=None):
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
        # Loads the link to the player
        self.player = player
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
            ) and self.destroyable is True and (self.player is None or self.player.alive is True):
                self.visible = False
                self.destroyable = False
                self.collider = None

                # Gives the points to the player
                points = 1 if self.shiny is False else 5
                if self.movement_vector is not None:
                    points += 2
                self.player.add_points(points)

                # Plays the explosion sound
                # If there is no defined player, plays the sound at volume 0.25
                if self.player is None:
                    volume = 0.25
                else:
                    # If there is a player, the volume will depend on the distance with them ; the further they are,
                    # the quieter it will be
                    volume = 1 / distance(self.player, self) * 1.5
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
