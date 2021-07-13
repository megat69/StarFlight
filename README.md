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
The settings are available in the `settings.json` file.
