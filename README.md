# StarFlight
Starflight is little game made with the [Ursina](https://www.ursinaengine.org/) game engine. Everything else is in the name :P

The goal of the game is to destroy as many asteroids as possible, and you die when you touch them.

The golden asteroids are worth 5 points, the standard ones 1 point, and add 2 if the asteroid was moving.

The whole goal of the game is to ***relax***.

The game is available for both Linux and Windows, with sadly no support for Mac OS whatsoever. Before running it, please install the requirements by doing `pip install -r requirements.txt` in the project folder.

## Controls
### Keyboard & Mouse
- Press `Shift` to increase the throttle and `Ctrl` to decrease it.
- Use the mouse to look around ; the ship will always go in the direction you are looking at.
- Press `Space` to fire.

### Controller
- Press `L` to decrease the throttle and `R` to increase it.
- Use the right stick to look around ; the ship will always go in the direction you are looking at.
- Press `b` to fire, or `X` for PlayStation controllers.
- **BEWARE : If you want to use a controller, you'll have to edit the `controller.py` file and set the variable `USING_CONTROLLER` (line 9) to `True` !**

## Customisation
You can change some of the settings in the code itself, including :
- The mouse sensivity : edit the `controller.py` file and set the variable `MOUSE_SENSITIVITY` (line 7) to whatever value you're comfortable with.
- The controller sensivity : edit the `controller.py` file and set the variable `CONTROLLER_SENSITIVITY` (line 8) to whatever value you're comfortable with, the first one being the horizontal sensitivity, the second the vertical sensitivity.
- The render distance (Default is 20) : edit the `main.py` file and set the variable `skybox_scale` (line 16) to whatever value you're comfortable with. Keep in mind that the higher the value is, the slower your game will be (in terms of performance and pace).
- The spaceship model : edit the `main.py` file and set the variable `SHIP_MODEL` (line 17) to the number of the ship you want. By default, this number is kept between 0 and 2, but you can also add your own ships in the `assets/` folder if you name them `ship_model_NUMBER.png` and select this number on the line 17. You can also set this value to `None`, and in that case, you won't be in a ship, which leads to a more relaxing experience.
