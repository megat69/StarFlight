"""
A first person controller.
"""
from ursina import *
from random import randint

SENSITIVITY = 70

class Controller(Entity):
    def __init__(self, points_enabled:bool=False):
        super().__init__(position=(0, -2.5, 0))

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

        # Speed counter
        self.speed_counter = Text(
            f"Speed : {self.speed:.3f}",
            position = (-0.85, -0.45),
            color = color.rgb(163, 251, 255),
            font = "assets/font/chintzy_cpu_brk/chintzy.ttf"
        )

        # Camera settings
        camera.parent = self.camera_pivot
        camera.position = (0,0,0)
        camera.rotation = (0,0,0)
        camera.fov = 90
        mouse.locked = True
        self.mouse_sensitivity = Vec2(SENSITIVITY, SENSITIVITY)

        # Other settings
        self.gravity = 0
        self.alive = True

        if points_enabled is True:
            self.points = 0
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
            # Updating the speed counter
            self.speed_counter.text = f"Speed : {self.speed:.3f}"
            self.speed_counter.color = color.rgb(randint(161, 165), randint(249, 252), randint(220, 255))

            # Speed modification
            if self.speed > 0.2 and held_keys["control"]:  self.speed -= 0.15 * time.dt
            if self.speed < 2 and held_keys["shift"]:    self.speed += 0.15 * time.dt

            # Movement updates
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

            self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
            self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

            self.direction = Vec3(self.forward).normalized()

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
                self.cursor.animate_color(color.rgb(255, 255, 255, 0), duration=2, curve=curve.out_expo)
                destroy(self.cursor, 2)

                # Adding the death text
                self.death_text = Text(
                    "You are dead.",
                    color=color.rgb(0, 0, 0, 0),
                    origin=(0, 0)
                )
                self.score_death_text = Text(
                    f"You scored {self.points} points.",
                    color=color.rgb(0, 0, 0, 0),
                    position = (0, -0.05),
                    origin=(0, 0)
                )
                self.score_exit_text = Text(
                    "Press 'Shift' + 'Q' to exit.",
                    color=color.rgb(0, 0, 0, 0),
                    position = (0, -0.1),
                    origin=(0, 0)
                )
                self.death_text.animate_color(color.rgb(255, 255, 255, 255), duration=2, curve=curve.out_expo)
                self.score_death_text.animate_color(color.rgb(255, 255, 255, 255), duration=4, curve=curve.out_expo)
                self.score_exit_text.animate_color(color.rgb(255, 255, 255, 255), duration=6, curve=curve.out_expo)

    def add_points(self, amount:int=1):
        """
        Adds some points to the player.
        :param amount: The amount of points to add.
        """
        if self.points is not None:
            self.points += amount
            self.points_counter.text = f"{self.points} PTS"

            self.points_counter.position_x = 0.8 - len(str(self.points)) / 25

    def input(self, key):
        pass