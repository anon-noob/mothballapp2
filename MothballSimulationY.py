from numpy import float32 as f32
from Enums import ExpressionType
from BaseMothballSimulation import BasePlayer, MothballSequence

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
        "stoppers": [],
        "returners": ["outty", "outsty", "outy", "outvy", "help", "duration", "height", "blip", "print"],
        "calculators": ["repeat", "r", "poss", "inertialistener", "il"],
        "setters": ["setposy", "sety", "y", "setvy", "vy", "inertia","setceiling", "ceil", "precision", "setprecision", 'pre', 'addposy', 'addy', 'addvy']
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
        self.last_returned_value = self.add_to_output(ExpressionType.Z_LABEL, label, self.y, centered_at)

    def outvy(self, centered_at: float = 0.0, label: str = "vy"):
        self.last_returned_value = self.add_to_output(ExpressionType.Z_LABEL, label, self.vy, centered_at)
    
    def setposy(self, value: float):
        self.y = value
    
    def inertia(self, value: float):
        self.inertia_threshold = value

    def outty(self, centered_at: float = 0, label: str = "top y"):
        self.last_returned_value = self.add_to_output(ExpressionType.Z_LABEL, label, self.y + 1.8, centered_at)
    
    def outsty(self, centered_at: float = 0, label: str = "top y (sneak)"):
        self.last_returned_value = self.add_to_output(ExpressionType.Z_LABEL, label, self.y + 1.5, centered_at)
    
    def slime(self, height: float = 0.0):
        self.move(1, state=self.SLIME)
        self.y = height

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
    
    def addposy(self, value: float, /):
        self.y += value

    def addvy(self, value: float, /):
        self.vy += value
    
    def duration(self, floor: float = 0.0, ceiling: float = 0.0, /, inertia: float = None, jump_boost: int = 0):
        if inertia is None:
            inertia = self.inertia_threshold
        
        vy = 0.42 + 0.1 * jump_boost
        y = 0
        ticks = 0

        while y > floor or vy > 0:
            y = y + vy
            if ceiling != 0.0 and y > ceiling - 1.8:
                y = ceiling - 1.8
                vy = 0
            vy = (vy - 0.08) * 0.98
            if abs(vy) < inertia:
                vy = 0
            ticks += 1

        if vy >= 0:
            self.add_to_output(ExpressionType.WARNING, string_or_num='Impossible jump height. Too high.')
            return

        ceiling = f' {ceiling}bc' if ceiling != 0.0 else ''
        self.add_to_output(ExpressionType.GENERAL_LABEL, f"Duration of a {floor}b{ceiling} jump: {ticks} ticks")

    def height(self, duration: int = 12, ceiling: float = 0.0, /, inertia: float = None, jump_boost: int = 0):
        if inertia is None:
            inertia = self.inertia_threshold
        
        vy = 0.42 + 0.1 * jump_boost
        y = 0
        ticks = 0

        for i in range(duration):
            y = y + vy
            if ceiling != 0.0 and y > ceiling - 1.8:
                y = ceiling - 1.8
                vy = 0
            vy = (vy - 0.08) * 0.98
            if abs(vy) < inertia:
                vy = 0
            ticks += 1

        ceiling = f' {ceiling}bc' if ceiling != 0.0 else ''
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, f"Height after {duration} ticks{ceiling} ", round(y, self.precision))

    def blip(self, blips: int = 1, blip_height: float = 0.0625, /, init_height: float = None, init_vy: float = None, *, inertia: float = None, jump_boost: int = 0):

        if init_height is None:
            init_height = blip_height
        if init_vy is None:
            init_vy = 0.42 + 0.1 * jump_boost    
        if inertia is None:
            inertia = self.inertia_threshold
        
        blips_done = 0
        vy = init_vy
        y = init_height
        jump_ys = [init_height]
        max_heights = []
        vy_prev = 0
        i = 0
        failed = False

        while blips_done < blips or vy > 0:

            y += vy
            vy = (vy - 0.08) * 0.98

            if y + vy < blip_height:

                if y + vy > 0:
                    failed = True
                    jump_ys.append(y + vy)
                    break
                
                jump_ys.append(y)
                vy = 0.42
                blips_done += 1
            
            if abs(vy) < inertia:
                vy = 0

            if vy_prev > 0 and vy <= 0:
                max_heights.append(y)

            vy_prev = vy
            i += 1


        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, "Blips", blips_done)
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, "Blip height", blip_height)
        self.add_to_output(ExpressionType.Z_LABEL, "Initial y", init_height)
        self.add_to_output(ExpressionType.Z_LABEL, "Initial vy", init_vy)
        
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, "Max height", max(max_heights))

        if failed:
            max_heights.append("Fail")

        padding1 = max(5, len(str(len(jump_ys))))
        padding2 = max(11, self.precision+2)
        self.add_to_output(ExpressionType.TEXT, string_or_num=f"{'Blip':<{padding1}} | {'Jumped From':<{padding2}} | Peak Heights")

        for i in range(0, len(jump_ys)):
            self.add_to_output(ExpressionType.TEXT, string_or_num=f"{i:<{padding1}} | {self.truncate_number(jump_ys[i]):<{padding2}} | {self.truncate_number(max_heights[i]) if not isinstance(max_heights[i], str) else max_heights[i]}")
        

    FUNCTIONS = {
        "jump": jump, "j": jump,
        "outy": outy,
        "outvy": outvy,
        "sety": setposy, "y": setposy,
        "addposy": addposy, "addy": addposy,
        "addvy": addvy,
        "inertia": inertia,
        "air": air, "a": air,
        "outty": outty, "outtopy": outty,
        "outsty": outsty, "outsneaktopy": outsty,
        "slime": slime,
        "setceiling": setceiling, "setceil": setceiling, "ceil": setceiling,
        "vy": setvy, "setvy": setvy,
        "possibilities": possibilities, "poss": possibilities,
        "up": up,
        "down": down,
        "duration": duration,
        "height": height,
        "blip": blip
    }

    ALIASES = BasePlayer.ALIASES
    for alias, func in FUNCTIONS.items():
        if func.__name__ in ALIASES: 
            ALIASES[func.__name__].append(alias)
        else:
            ALIASES[func.__name__] = [alias]

    FUNCTIONS = BasePlayer.FUNCTIONS | FUNCTIONS

    def show_default_output(self):
        self.add_to_output(ExpressionType.Z_LABEL, "Y", self.y)
        self.add_to_output(ExpressionType.Z_LABEL,"VY", self.vy)

if __name__ == "__main__":
    p = PlayerSimulationY()
    # s = "jump(15) outy slime outy a(7) outy"
    s = "pre(7) blip(10,px,px)"
    # s = "jump"
    # s = "print(helo worlD) outy outvy"
    p.simulate(s)
    p.show_output()