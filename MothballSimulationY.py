from numpy import float32 as f32
from typing import Literal
import re
import inspect
# from collections import Counter
from Enums import ExpressionType
from BaseMothballSimulation import BasePlayer, OverwriteError, MothballSequence

class PlayerSimulationY(BasePlayer):

    JUMP = 0
    GROUND = 1
    AIR = 2
    SLIME = 3

    WATER =  0b1
    LAVA =   0b10
    WEB =    0b100
    LADDER = 0b1000

    ALIAS_TO_MODIFIER = {"water": WATER,"wt": WATER,"lv": LAVA,"lava": LAVA,"web": WEB,"ladder": LADDER,"ld": LADDER,"vine": LADDER}
    
    _can_have_modifiers = ["up", "down", "jump", "air"]

    MODIFIERS = [WATER, LAVA, WEB, LADDER]

    FUNCTIONS_BY_TYPE = {
        "fast-movers": ["jump", "j", "air", "a", "slime"],
        "slow-movers": ["up", "down"],
        "setters": ["sety", "y", "setvy", "vy", "inertia","setceiling", "ceil"],
        "calculators": ["repeat", "r", "poss", "print", "inertialistener", "il"],
        "returners": ["outty", "outsty", "outy", "outvy", "help"]
    }

    def __init__(self) -> None:
        super().__init__()
        self.y = 0.0
        self.vy = 0.0

        self.state = self.GROUND

        self.modifiers = 0

        self.record = {}
        
        self.ceiling = None
        self.hit_ceiling = False

    def move(self, duration, jump_boost = 0, up = False, down = False, state = GROUND):
        
        for _ in range(duration):
            
            self.y += self.vy # (Pre order)
            if self.hit_ceiling:
                self.vy = 0
                self.y = self.ceiling - 1.8
                self.hit_ceiling = False

            # idk
            if self.previously_in_web:
                self.vy = 0

            if state == self.JUMP:
                self.vy = 0.42 + 0.1 * jump_boost
                # self.y = 0.0

            elif self.modifiers & self.WATER:
                a = self.vy * 0.8 - 0.02
                if abs(a) < self.inertia_threshold:
                    a = 0
                if up:
                    self.vy = a + 0.04 # Going up
                if down:
                    self.vy = a # Going down
            
            elif self.modifiers & self.LAVA:
                a = self.vy * 0.5 - 0.02
                if abs(a) < self.inertia_threshold:
                    a = 0
                if up:
                    self.vy = a + 0.04 # Going up
                if down:
                    self.vy = a # Going down
            
            else:
                if state == self.SLIME:
                    self.vy = -self.vy
                self.vy = (self.vy - 0.08) * 0.98
                if self.modifiers & self.LADDER:
                    if up:
                        self.vy = 0.12 * 0.98
                    elif down:
                        self.vy = max(-0.15, self.vy)
            
            # idk

            if abs(self.vy) < self.inertia_threshold and not self.modifiers & self.WATER:
                self.vy = 0

            if self.modifiers & self.WEB:
                self.vy = self.vy / 20

            self.previously_in_web = self.modifiers & self.WEB
            self.previously_in_water = self.modifiers & self.WATER
            self.previously_in_lava = self.modifiers & self.LAVA

            if self.ceiling and self.y + self.vy + 1.8 >= self.ceiling:
                self.vy = self.ceiling - self.y - 1.8
                self.hit_ceiling = True
            
            self.possibilities_helper()        
    
    def possibilities_helper(self):
        if not self.record:
            return
        
        if self.vy < 0:
            
            top_diff = self.y % 0.0625
            top = self.y - top_diff
            botdiff = (self.y + self.vy) % 0.0625
            bot = self.y + self.vy - botdiff + 0.0625

            self.add_to_output(ExpressionType.GENERAL_LABEL, f"Tick {self.record['tick']}", f"{self.y} ({top} to {bot})")
        self.record['tick'] += 1
    
    def get_inertia_speed(self):
        return self.inertia_threshold / f32(0.91)
    
    def jump(self, duration: int = 1, jump_boost: int = 0):
        self.move(1, state = self.JUMP, jump_boost = jump_boost)
        self.move(duration - 1, state = self.AIR)

    def air(self, duration: int = 1):
        self.move(duration, state=self.AIR)

    def outy(self, centered_at: float = 0.0, label: str = "outy"):
        self.add_to_output(ExpressionType.Z_LABEL, label, self.y, centered_at)

    def outvy(self, centered_at: float = 0.0, label: str = "vy"):
        self.add_to_output(ExpressionType.Z_LABEL, label, self.vy, centered_at)
    
    def sety(self, e: float):
        self.y = e
    
    def inertia(self, value: float):
        self.inertia_threshold = value

    def outty(self, centered_at: float = 0, label: str = "top y"):
        self.add_to_output(ExpressionType.Z_LABEL, label, self.y + 1.8, centered_at)
    
    def outsty(self, centered_at: float = 0, label: str = "top y (sneak)"):
        self.add_to_output(ExpressionType.Z_LABEL, label, self.y + 1.5, centered_at)
    
    def slime(self, height: float = 0.0):
        self.move(1, state=self.SLIME)
        self.y = height
    
    def repeat(self, sequence: MothballSequence, count: int = 1):
        for _ in range(count):
            self.simulate(sequence, return_defaults=False, locals=self.local_vars)
    
    def printdisplay(self, string:str = ""):
        self.add_to_output(ExpressionType.TEXT, string_or_num=string)

    def setceiling(self, height: float = 0.0):
        if height == 0.0:
            self.ceiling = None
        if height < 1.5:
            raise ValueError("Ceiling height is too low") # This will change with the scale attribute later on
        self.ceiling = height

    def setvy(self, value: float, /):
        self.vy = value
    
    def up(self, duration: int = 1):
        self.move(duration, up=True)
    
    def down(self, duration: int = 1):
        self.move(duration, down=True)
    
    def possibilities(self, sequence: MothballSequence):
        if not self.record: # JUST FOR NOW
            self.record = {"tick":1}
        else:
            raise TypeError(f"Nested posibilities functions are not allowed.")
        self.simulate(sequence, return_defaults=False)
        self.record = {}

    def ballhelp(self, func: str):
        "Gets help about function `func`"
        f = PlayerSimulationY.FUNCTIONS.get(func)
        if f is None:
            f = self.local_funcs.get(func)
            # print(self.local_funcs)
            # print(f)
            if f is None:
                raise NameError(f"Function {func} not found")
            

        f_sig = inspect.signature(f).parameters
        # print(f"Help with {func}\n-------------------")
        # print('Arguments:')
        self.add_to_output(ExpressionType.GENERAL_LABEL, f"Help with {func}:")
        self.add_to_output(ExpressionType.GENERAL_LABEL, f"  Arguments:")
        

        # print(f_sig.values())
        for y in f_sig.values(): # PLEASE ADD * and /
            # print(f"\t{y}")
            if y.name != "self":
                self.add_to_output(ExpressionType.GENERAL_LABEL, f"    {y}")
        
        # print(f.__doc__)
        self.add_to_output(ExpressionType.GENERAL_LABEL, f.__doc__)

    FUNCTIONS = {
        "jump": jump, "j": jump,
        "outy": outy,
        "outvy": outvy,
        "sety": sety, "y": sety,
        "inertia": inertia,
        "air": air, "a": air,
        "repeat": repeat, "r": repeat,
        "print": printdisplay,
        "outty": outty, "outtopy": outty,
        "outsty": outsty, "outsneaktopy": outsty,
        "slime": slime,
        "setceiling": setceiling, "setceil": setceiling, "ceil": setceiling,
        "vy": setvy, "setvy": setvy,
        "possibilities": possibilities, "poss": possibilities,
        "ballhelp": ballhelp, "help": ballhelp,
        "up": up,
        "down": down
    }

    def show_default_output(self):
        self.add_to_output(ExpressionType.Z_LABEL, "Y", self.y)
        self.add_to_output(ExpressionType.Z_LABEL,"VY", self.vy)

if __name__ == "__main__":
    p = PlayerSimulationY()
    # s = "jump(15) outy slime outy a(7) outy"
    s = "jump(12) outy y(0.125) jump(12) outy"
    # s = "jump"
    # s = "print(helo worlD) outy outvy"
    p.simulate(s)
    p.show_output()