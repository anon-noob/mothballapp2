"""
The Reference Window, using `RenderViewer` to display text, for a reference sheet of values and common gotchas.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow
)

from TextCell import MDLinter, RenderViewer

class MainWindow(QMainWindow):
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict):
        super().__init__()
        self.generalOptions = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.setWindowTitle("About")
        self.setGeometry(100, 100, 900, 600)

        self.pages = {}

        self.text_browser = RenderViewer(generalOptions,colorOptions,textOptions,self)

        self.setCentralWidget(self.text_browser)

        self.loadDocument()

    def loadDocument(self):
        md = """# Reference Values
Here, you will find the most commonly used values for various things, such as block slipperiness, air drag, etc.

## Inertia
Version 1.8:  `0.005`
Version 1.9+: `0.003`

Version 1.8 to 1.21.4: single axis inertia
Version 1.21.5+:       two axis inertia

You can set the inertia value to any number using `inertia()`, or you can use `version()` and have it set the value for you, depending on the verison.
Single axis means that inertia is checked on each individual axis. Two-axis instead checks your total speed calculated from your `x` and `z` speed.

## Block Slipperiness
Default:        0.6
Ice/Packed Ice: 0.98
Blue Ice:       0.989
Slime*:         0.8

You can set the slip value to any number using `slip()`, or use a keyword argument in a movement function, such as `walk(slip=0.98)`.
* Slime has weird mechanics where the player is always continually bouncing when not sneaking, hence this `0.8` slip only works accurately on the first tick.
** When airborne, the slip is set to `1`.

## Potion Effects
The formula for the effect multiplier is `max(0, (1+0.2*speed)(1-0.15*slow))` with both `speed` and `slow` taking integer values from 0 to 255 inclusive. This only directly affects ground-based movement.
Slow 7 and above will yield a multiplier of `0`. This makes it so you can only move while airborne.

## Angle Optimization
Air Drag:                   0.91
Ground Drag*:               0.546   (=0.91*0.6)
Air Accel:                  0.02548 (=0.98*0.026)
Air Accel w/ strafe:        0.026
Ground Accel*:              0.1274  (=0.98*0.13)
Ground Accel w/ strafe*:    0.13
WAD Jump Speed*:            0.3274  (0.1274+0.2)
WDWA Jump Speed*:           0.3060548
WDWA Jump Angle*:           17.4786858

All of this is assuming sprinting.
*Values represent no potion effects and a block slipperiness of `0.6`. Below is how you can find these values, including with potions and slip values. Here, `pmul` stands for the potion's multiplier (see Potion Effects).

Ground Drag: 0.91*`slip`*`pmul`
Ground Accel: Run `sprint` and get the `vz`.
Ground Accel w/ strafe: Run `sprint45` and get the `vz`.
WAD Jump Speed: Run `sprintjump` and get the `vz`
WDWA Jump Speed and Angle: Run `sj.wa vec`.

Example of finding ground acceleration with strafe, with speed 2, slow 1, and a slip of 0.98.
```mothball
# Run this and take the vz #
speed(2) slow(1) slip(0.98) sprint45
```
```mothball/output
ze|VZ/: /0.0355031//
```

In the angle optimizer cell, to set inertia, find the appropiate Drag X/Drag Z cell and set it to 0. Then, add a new constraint which restricts the speed so that it is within the inertia threshold. 
For example, set `z(t) - z(t-1) < inertia_speed`. Inertia speed is calculated by `inertia_value/0.91/slip`.
"""
        self.text_browser.renderTextfromMarkdown(MDLinter(self.generalOptions, self.colorOptions, self.textOptions), md)



# if __name__ == "__main__":
#     import FileHandler
#     a=FileHandler.getCodeColorSettings()
#     b=FileHandler.getGeneralSettings()
#     c=FileHandler.getTextColorSettings()
#     app = QApplication(sys.argv)
#     window = MainWindow(b,a,c)
#     window.show()
#     sys.exit(app.exec_())