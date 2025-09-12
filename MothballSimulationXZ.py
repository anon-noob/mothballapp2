from math import sin, cos, atan2 as arctan, sqrt, copysign, degrees as deg, asin, acos
from numpy import float32 as f32, uint64 as u64, int32 as i32
from typing import Literal
import re
import inspect
from BaseMothballSimulation import BasePlayer, MothballSequence
from Enums import ExpressionType
from collections import deque

class Tick:
    def __init__(self, w: bool, a: bool, s: bool, d: bool, sneak: bool, sprint: bool, space: bool, right_click: bool, last_turn: float):
        self.w = w
        self.a = a
        self.s = s
        self.d = d
        self.sneak = sneak
        self.sprint = sprint
        self.space = space
        self.right_click = right_click
        self.last_turn = last_turn
    
    def __repr__(self):
        return f"Tick({self.w=},{self.a=},{self.s=},{self.d=},{self.sneak=},{self.sprint=},{self.space=},{self.right_click=},{self.last_turn=})"

class PlayerSimulationXZ(BasePlayer):
    pi = 3.14159265358979323846

    # These are 45-strafe movement, and cannot have an input appended (WASD)
    _fortyfive_methods = ("walk45", "walkair45", "walkjump45", "sprint45", "sprintair45", "sprintjump45", "sneak45", "sneakair45", "sneakjump45", "sneaksprint45", "sneaksprintair45", "sneaksprintjump45")

    # These movement CAN have inputs (WASD)
    _can_have_input = ("walk", "walkair", "walkjump", "sprint", "sprintair", "sprintjump", "sneak", "sneakair", "sneakjump", "sneaksprint", "sneaksprintair", "sneaksprintjump")

    # These allow modifiers, which modify movement (see the attribute MODIFIERS)
    _can_have_modifiers = _fortyfive_methods + _can_have_input + ("stop", "stopjump", "stopair", "sneakstop", "sneakstopair", "sneakstopjump")
    

    mm_to_dist = dist_to_block = lambda mm: (mm + copysign(f32(0.6), mm))
    dist_to_mm = block_to_dist = lambda dist: (dist - copysign(f32(0.6), dist))

    sprintjump_boost = f32(0.2)

    # Player States Enums
    JUMP = 0
    GROUND = 1
    AIR = 2

    # Modifiers Enums (yes they're in binary)
    WATER =     0b1
    LAVA =      0b10
    WEB =       0b100
    BLOCK =     0b1000
    LADDER =    0b10000
    SOULSAND =  0b100000

    MODIFIERS = (WATER, WEB, LAVA, BLOCK, LADDER, SOULSAND)
    ALIAS_TO_MODIFIER = {"water": WATER,"wt": WATER,"lv": LAVA,"lava": LAVA,"web": WEB,"block": BLOCK,"bl": BLOCK,"ladder": LADDER,"ld": LADDER,"vine": LADDER, "soulsand": SOULSAND, "ss": SOULSAND}

    FUNCTIONS_BY_TYPE = {"fast-movers": [
        "sprint", "s", "sprint45", "s45", "sprintjump", "sprintjump45", "sj", "sj45", "sprintair", "sa", "sprintair45", "sa45", "sprintstrafejump", "sprintstrafejump45", "strafejump", "strafejump45", "stfj", "stfj45", "sneaksprint", "sneaksprintair", "sneaksprintjump", "sns", "snsa", "snsj", "sneaksprint45", "sneaksprintair45", "sneaksprintjump45", "sns45", "snsa45", "snsj45"
    ], "slow-movers": [
        "walk", "w", "walkair", "wa", "walkjump", "wj", "walk45", "w45", "walkair45", "wa45", "walkjump45", "wj45", "sneak", "sneak45", "sn", "sn45", "sneakair", "sneakair45", "sna", "sna45", "sneakjump", "snj", "sneakjump45", "snj45"
    ], "stoppers": [
        "stop", "stopground", "st", "stopair", "sta", "stopjump", "stj", "sneakstop", "sneakstopair", "sneakstopjump", "snst", "snsta", "snstj"
    ], "returners": [
        "outz", "zmm", "zb", "outvz", "outx", "xmm", "xb", "outvx", "vec", "help", "print", "effectsmultiplier", "effects", "printdisplay", "dimensions", "dim", "outangle", "outa", "outfacing", "outf", "outturn", "outt", 'macro'
    ], "calculators": [
        "bwmm", "xbwmm", "wall", "xwall", "inv", "xinv", "blocks", "xblocks", "repeat", "r", "possibilities", "poss", "xpossibilities", "xposs", "xzpossibilities", "xzposs", 'taps'
    ], "setters": [
        "face", "facing", "f", "turn", "setposz", "z", "setvz", "vz", "setposx", "x", "setvx", "vx", "setslip", "slip", "setprecision", "precision", "pre", "inertia", "sprintairdelay", "sdel", "version", "v", "anglequeue", "aq", "tq", "turnqueue", "speed", "slow", "slowness", "sndel", "sneakdelay", "var", "function", "custom_function", "func", "alias", "toggle", "singleaxisinertia","inertialistener", "il", "xinertialistener", "xil", "zinertialistener", "zil", "xzinertialistener", "xzil"
    ]}

    

    def __init__(self) -> None:
        super().__init__()
        self.x = 0.0
        self.z = 0.0
        self.vx = 0.0
        self.vz = 0.0

        self.default_ground_slip = f32(0.6)
        self.current_slip = f32(0.6)
        self.previous_slip = None

        self.total_angles = 65536

        self.rotation = f32(0.0)
        self.last_rotation = f32(0.0)
        self.last_turn = f32(0.0)

        self.angle_queue: deque[f32] = deque()
        self.turn_queue: deque[f32] = deque()
        self.air_sprint_delay = True
        self.sneak_delay = False
        self.inertia_axis = 1
        self.inputs = ""

        self.state = self.GROUND
        self.record = {}
        self.record_inertia = {}

        self.speed_effect = 0
        self.slow_effect = 0

        self.history: list[Tick] = []
        self.macros: dict[str, str] = {}

    def get_angle(self):
        "Returns the next angle from the rotation queue or if no angle is in the rotation queue, return the default facing."

        if self.angle_queue:
            self.rotation = self.angle_queue.popleft()
        if self.turn_queue:
            self.rotation += self.turn_queue.popleft()
        return self.rotation

    def move(self, duration: int, rotation: f32 = None, rotation_offset: float = 0.0, slip: f32 = None, is_sprinting: bool = False, is_sneaking: bool = False, speed: int = None, slow: int = None, state: Literal["ground", "air", "jump"] = "ground"):
        """
        Moves the player for `duration` ticks with a slip value of `slip`.

        The player will move facing `rotation` if given, otherwise, it will use the rotation queue and/or the default rotation.

        `rotation_offset` is used if you wish to preserve the facing despite the actual angle being different, particularly useful for displaying info while 45ing (`rotation_offset = 45`) or strafe jumping (`rotation_offset = 17.4786857811690446`).

        Although there is no hard restriction, in later versions, `is_sprinting` and `is_sneaking` can be set to `True` at the same time.
        """

        # Setting slipperiness here and treating it like air is analytically and numerically equivalent
        if self.modifiers  & self.WATER:
            slip=f32(0.8/0.91)
        elif self.modifiers & self.LAVA:
            slip=f32(0.5/0.91)
        
        sj_boost = self.sprintjump_boost
        if self.previous_slip is None:
            self.previous_slip = self.default_ground_slip

        if rotation_offset == 45:
            self.inputs = "wa"
        
        if speed is None:
            speed = self.speed_effect
        if slow is None:
            slow = self.slow_effect

        self.state = state
        # If sneaking is modified by ladders, always set the state to AIR
        if ((self.sneak_delay and self.previously_sneaking) or (not self.sneak_delay and is_sneaking)) and self.modifiers & self.LAVA:
            self.state = self.AIR

        override_rotation = False
        if (rotation is not None):
            override_rotation = True
            rotation = f32(rotation + rotation_offset)

        if not slip: # If slip is not given, assume its ground slip since air slip (0.1) is always passed into the argument
            slip = self.default_ground_slip
        
        for _ in range(duration):
            if not override_rotation:
                rotation = f32(self.get_angle() + rotation_offset)
                
            # MOVING THE PLAYER
            self.x += self.vx
            self.z += self.vz

            if self.modifiers & self.SOULSAND: # Like 13 df accurate minimum
                self.vx *= 0.4
                self.vz *= 0.4

            forward, strafe = self.movement_values()

            if self.reverse:
                forward *= f32(-1)
                strafe *= f32(-1)
                sj_boost *= -1

            # Finalize Momentum
            self.vx *= f32(0.91) * self.previous_slip
            self.vz *= f32(0.91) * self.previous_slip

            # Apply inertia or web
            if self.inertia_axis == 1:
                if abs(self.vx) < self.inertia_threshold or self.previously_in_web:
                    self.vx = 0.0
                if abs(self.vz) < self.inertia_threshold or self.previously_in_web:
                    self.vz = 0.0
            elif self.inertia_axis == 2:
                if sqrt(self.vz**2 + self.vx**2) < self.inertia_threshold or self.previously_in_web:
                    self.vx = 0.0
                    self.vz = 0.0

            # Get Movement Multiplier M
            M = self.movement_multiplier(slip, is_sprinting, speed, slow, self.state)

            # Sprint jump boost
            if self.state == self.JUMP and is_sprinting:
                facing = f32(rotation * f32(0.017453292)) # TO CHANGE
                self.vx -= self.mcsin(facing) * sj_boost
                self.vz += self.mccos(facing) * sj_boost

            # BLOCKING
            if self.modifiers & self.BLOCK:
                forward = f32(float(forward) * 0.2)
                strafe  = f32(float(strafe) * 0.2)

            # SNEAKING
            if (self.sneak_delay and self.previously_sneaking) or (not self.sneak_delay and is_sneaking):
                forward = f32(float(forward) * 0.3)
                strafe = f32(float(strafe) * 0.3)

            forward *= f32(0.98)
            strafe *= f32(0.98)

            distance = f32(strafe * strafe + forward * forward)

            # Avoid division by 0
            if distance >= f32(0.0001):

                # Normalize distance IF above 1
                distance = f32(sqrt(float(distance)))
                if distance < f32(1.0):
                    distance = f32(1.0)

                # Modifies strafe and forward to account for movement
                distance = M / distance
                forward = forward * distance
                strafe = strafe * distance

                # Adds rotated vectors to velocity
                sin_yaw = f32(self.mcsin(rotation * f32(PlayerSimulationXZ.pi) / f32(180.0)))
                cos_yaw = f32(self.mccos(rotation * f32(PlayerSimulationXZ.pi) / f32(180.0)))

                self.vx += float(strafe * cos_yaw - forward * sin_yaw)
                self.vz += float(forward * cos_yaw + strafe * sin_yaw)

            if self.modifiers & self.WEB:
                self.vx = self.vx / 4
                self.vz = self.vz / 4
            if self.modifiers & self.LADDER:
                self.vx = min(max(self.vx, -0.15),0.15)
                self.vz = min(max(self.vz, -0.15),0.15)
            
            
            # Prep for next tick
            self.previous_slip = slip
            self.previously_sprinting = is_sprinting
            self.previously_sneaking = is_sneaking
            self.previously_in_web = bool(self.modifiers & self.WEB)
            self.last_turn = rotation - self.last_rotation
            self.last_rotation = rotation

            # Record possibilities and history
            self.possibilities_helper()

            self.inertialistener_helper()

            self.history.append(Tick('w' in self.inputs, 'a' in self.inputs, 's' in self.inputs, 'd' in self.inputs, is_sneaking, is_sprinting, self.state == self.JUMP, bool(self.modifiers & self.BLOCK), self.last_turn))

    def get_inertia_speed(self):
        "Get the speed of hitting inertia, depending on whether the player is midair, on ground, and with what slipperiness."
        if self.state == self.AIR:
            return self.inertia_threshold / f32(0.91)
        else:
            return self.inertia_threshold / f32(f32(0.91) * self.current_slip)

    def inertialistener_helper(self):
        "Auxilary function for dealing with `inertialistener()` functions"
        if not self.record_inertia:
            return
        
        record_axis = self.record_inertia["type"]
        inertia_speed = self.get_inertia_speed()
        tolerance = abs(self.record_inertia["tolerance"]) + inertia_speed

        if record_axis == "x" or record_axis == "xz":
            if abs(self.vx) <= tolerance:
                if abs(self.vx) <= inertia_speed:
                    self.add_to_output(ExpressionType.X_INERTIA_HIT, f"Tick {self.record_inertia['tick']} Vx (Hit)", self.vx, inertia_speed)
                else:
                    self.add_to_output(ExpressionType.X_INERTIA_MISS, f"Tick {self.record_inertia['tick']} Vx (Miss)", self.vx, inertia_speed)

        if record_axis == "z" or record_axis == "xz":
            if abs(self.vz) <= tolerance:
                if abs(self.vz) <= inertia_speed:
                    self.add_to_output(ExpressionType.Z_INERTIA_HIT, f"Tick {self.record_inertia['tick']} Vz (Hit)", self.vz, inertia_speed)
                else:
                    self.add_to_output(ExpressionType.Z_INERTIA_MISS, f"Tick {self.record_inertia['tick']} Vz (Miss)", self.vz, inertia_speed)

        self.record_inertia['tick'] += 1
            
    def possibilities_helper(self):
        "Auxilary function for dealing with `possibilities()` functions"
        if not self.record:
            return
        
        record_axis = self.record["type"]
        
        x_offset = self.record.get("x offset", 0) * copysign(1, self.x)
        z_offset = self.record.get("z offset", 0) * copysign(1, self.z)
        x_increment = copysign(self.record.get("x increment", 0), self.x)
        z_increment = copysign(self.record.get("z increment", 0), self.z)
        min_dist = self.record["min_distance"]
        near_misses = self.record["miss"]

        if record_axis == "z":
            z_distance = self.z + f32(z_offset)
            z_pixel_offset = z_distance % z_increment
            if abs(z_pixel_offset) <= min_dist:

                self.add_to_output(ExpressionType.Z_LABEL, f"Tick {self.record['tick']}", z_distance, z_distance-z_pixel_offset)
            else:
                z_offset_miss = z_increment - z_pixel_offset
                if near_misses is not None and (abs(z_offset_miss) <= near_misses):
                    
                    self.add_to_output(ExpressionType.Z_LABEL, f"Tick {self.record['tick']}", z_distance + z_increment - z_pixel_offset - z_offset_miss, z_distance + z_increment - z_pixel_offset)


        elif record_axis == "x":
            x_distance = self.x + f32(x_offset)
            x_pixel_offset = x_distance % x_increment
            if abs(x_pixel_offset) <= min_dist:
                self.add_to_output(ExpressionType.X_LABEL, f"Tick {self.record['tick']}", x_distance, x_distance-x_pixel_offset)
            else:
                x_offset_miss = x_increment - x_pixel_offset
                if near_misses is not None and (abs(x_offset_miss) <= near_misses):
                    self.add_to_output(ExpressionType.X_LABEL, f"Tick {self.record['tick']}", x_distance + x_increment - x_pixel_offset - x_offset_miss, x_distance + x_increment - x_pixel_offset)

        elif record_axis == "xz":
            z_distance = self.z + f32(z_offset)
            z_pixel_offset = z_distance % z_increment
            x_distance = self.x + f32(x_offset)
            x_pixel_offset = x_distance % x_increment
            if abs(z_pixel_offset) <= min_dist and abs(x_pixel_offset) <= min_dist:
                self.add_to_output(ExpressionType.GENERAL_LABEL, f"Tick {self.record['tick']}")
                self.add_to_output(ExpressionType.X_LABEL, "  X", x_distance, x_distance-x_pixel_offset, strip_label=False)
                self.add_to_output(ExpressionType.Z_LABEL, "  Z", z_distance, z_distance-z_pixel_offset, strip_label=False)

            else:
                z_offset_miss = z_increment - z_pixel_offset
                x_offset_miss = x_increment - x_pixel_offset
                if near_misses is not None and not (abs(x_offset_miss) > near_misses or abs(z_offset_miss) > near_misses):
                    self.add_to_output(ExpressionType.GENERAL_LABEL, f"Tick {self.record['tick']}")
                    self.add_to_output(ExpressionType.X_LABEL, "  X", x_distance + x_increment - x_pixel_offset - x_offset_miss, x_distance + x_increment - x_pixel_offset, strip_label=False)
                    self.add_to_output(ExpressionType.Z_LABEL, "  Z", z_distance + z_increment - z_pixel_offset - z_offset_miss, z_distance + z_increment - z_pixel_offset, strip_label=False)
   
        self.record['tick'] += 1


    def movement_multiplier(self, slip, is_sprinting, speed, slow, state):
        """
        Calculates and returns the movement multiplier `M`.

        See https://www.mcpk.wiki/wiki/Horizontal_Movement_Formulas for the formula used to calculate `M`

        Notets on fluids: The equation for water is the same as air with S = 0.8/0.91 and M being either 1 or 0 multiplied by 0.98 or 1, similarly for lava, set S = 0.5/0.91
        """
        if self.modifiers & self.WATER or self.modifiers & self.LAVA: # It doesnt matter if you are in web
            M = f32(0.02)
        
        elif state == self.AIR:
            M = f32(0.02) # In water, walk and sprint are the same, potion effects do not affect water or air, shiftng is different

            if (self.air_sprint_delay and self.previously_sprinting) or (not self.air_sprint_delay and is_sprinting):
                M = f32(M + M * 0.3)

        else: # either on jump or on ground
            M = f32(0.1)

            # Deal with potion effects 
            if speed > 0:
                M = f32(M * (1.0 + f32(0.2) * float(speed)))
            if slow > 0:
                M = f32(M * max(1.0 + f32(-0.15) * float(slow), 0))

            if is_sprinting:
                M = f32(M * (1.0 + f32(0.3)))

            drag = f32(0.91) * slip
            M *= f32(0.16277136) / (drag * drag * drag)
        
        return M

    def movement_values(self):
        """
        Returns two values `forward` and `strafe` either valued at `-1`, `0`, or `1`, based on `self.inputs`.

        if "w" is in the inputs, `forward = 1`. If "a" is in inputs, `strafe = 1`, etc.
        """

        if "w" in self.inputs:
            forward = f32(1.0)
        elif "s" in self.inputs:
            forward = f32(-1.0)
        else:
            forward = f32(0.0)

        if "a" in self.inputs:
            strafe = f32(1.0)
        elif "d" in self.inputs:
            strafe = f32(-1.0)
        else:
            strafe = f32(0.0)

        return forward, strafe

############ START OF END USER'S FUNCTIONS ############

    def walk(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, slip=slip, state=self.GROUND, speed=speed, slow=slow)

    def walk45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, 45, slip=slip, state=self.GROUND, speed=speed, slow=slow)

    def sprint(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, slip=slip, is_sprinting=True, state=self.GROUND, speed=speed, slow=slow)

    def sprint45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, 45, slip=slip, is_sprinting=True, state=self.GROUND, speed=speed, slow=slow)

    def walkair(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, slip=1.0, state=self.AIR)

    def walkair45(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, 45, slip=1.0, state=self.AIR)
    
    def sprintair(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, slip=1.0, is_sprinting=True, state=self.AIR)
    
    def sprintair45(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, 45, slip=1.0, is_sprinting=True, state=self.AIR)

    def walkjump(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0: 
            self.move(1, rotation, slip=slip, state=self.JUMP, speed=speed, slow=slow)
            self.walkair(duration - 1, rotation)

    def walkjump45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.move(1, rotation, 45, slip=slip, state=self.JUMP, speed=speed, slow=slow)
            self.walkair45(duration - 1, rotation)

    def sprintjump(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.move(1, rotation, slip=slip, is_sprinting=True, state=self.JUMP, speed=speed, slow=slow)
            self.sprintair(duration - 1, rotation)

    def sprintjump45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.move(1, rotation, slip=slip, is_sprinting=True, state=self.JUMP, speed=speed, slow=slow)
            self.sprintair45(duration - 1, rotation)

    def sprintstrafejump(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.inputs = "wa"
            self.move(1, rotation, self.get_optimal_strafe_jump_angle(speed=speed, slow=slow, slip=slip), slip=slip, is_sprinting=True, state=self.JUMP, speed=speed, slow=slow)

            self.inputs = "w"
            self.sprintair(duration - 1, rotation)

    def sprintstrafejump45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.inputs = "wa"
            self.move(1, rotation, self.get_optimal_strafe_jump_angle(speed=speed, slow=slow, slip=slip), slip=slip, is_sprinting=True, state=self.JUMP, speed=speed, slow=slow)

            self.sprintair45(duration - 1, rotation)

    
    def sneak(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, slip=slip, is_sneaking=True, state=self.GROUND, speed=speed, slow=slow)

    def sneak45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, 45, slip=slip, is_sneaking=True, state=self.GROUND, speed=speed, slow=slow)
    
    def sneakair(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, slip=1.0, is_sneaking=True, state=self.AIR)
    
    def sneakair45(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, 45, slip=1.0, is_sneaking=True, state=self.AIR)
    
    def sneakjump(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.move(1, rotation, slip=slip, is_sneaking=True, state=self.JUMP, speed=speed, slow=slow)
            self.sneakair(duration - 1, rotation)

    def sneakjump45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.move(1, rotation, 45, slip=slip, is_sneaking=True, state=self.JUMP, speed=speed, slow=slow)
            self.sneakair45(duration - 1, rotation)
    
    def stop(self, duration: int = 1, /, *, slip: f32 = None):
        self.move(duration, slip=slip, state=self.GROUND)
    
    def stopair(self, duration: int = 1, /):
        self.move(duration, slip=1.0, state=self.AIR)
    
    def stopjump(self, duration: int = 1, /, *, slip: f32 = None):
        if duration > 0:
            self.move(1, slip=slip, state=self.JUMP)
            self.stopair(duration - 1)
    
    def sneakstop(self, duration: int = 1, /, *, slip: f32 = None):
        self.move(duration, slip=slip, state=self.GROUND, is_sneaking=True)
    
    def sneakstopair(self, duration: int = 1, /):
        self.move(duration, slip=1.0, state=self.AIR, is_sneaking=True)
    
    def sneakstopjump(self, duration: int = 1, /, *, slip: f32 = None):
        if duration > 0:
            self.move(1, slip=slip, state=self.JUMP, is_sneaking=True)
            self.stopair(duration - 1)
    
    def sneaksprint(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, slip=slip, is_sprinting=True, is_sneaking=True, state=self.GROUND, speed=speed, slow=slow)
    
    def sneaksprint45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        self.move(duration, rotation, 45, slip=slip, is_sprinting=True, is_sneaking=True, state=self.GROUND, speed=speed, slow=slow)
    
    def sneaksprintair(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, slip=1.0, is_sprinting=True, is_sneaking=True, state=self.AIR)
    
    def sneaksprintair45(self, duration: int = 1, rotation: f32 = None, /):
        self.move(duration, rotation, 45, slip=1.0, is_sprinting=True, is_sneaking=True, state=self.AIR)
    
    def sneaksprintjump(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.move(1, rotation, slip=slip, is_sprinting=True, is_sneaking=True, state=self.JUMP, speed=speed, slow=slow)
            self.sneaksprintair(duration - 1, rotation)
    
    def sneaksprintjump45(self, duration: int = 1, rotation: f32 = None, /, *, slip: f32 = None, speed: int = None, slow: int = None):
        if duration > 0:
            self.inputs = "wa"
            self.move(1, rotation, self.get_optimal_strafe_jump_angle(speed=speed, slow=slow, slip=slip, is_sneaking=True), slip=slip, is_sprinting=True, is_sneaking=True, state=self.JUMP, speed=speed, slow=slow)
            self.sneaksprintair45(duration - 1, rotation)

    # PRIVATE FUNCTION
    def get_optimal_strafe_jump_angle(self, speed: int = None, slow: int = None, slip: f32 = None, is_sneaking: bool = False):
        player = PlayerSimulationXZ.copy_player(self)
        player.x = 0.0
        player.z = 0.0
        player.vx = 0.0
        player.vz = 0.0
        player.angle_queue = []
        player.rotation = 0.0
        if speed is not None:
            player.speed_effect = speed
        if slow is not None:
            player.slow_effect = slow
        if slip is not None:
            player.default_ground_slip = slip
        
        if is_sneaking:
            player.simulate("snsj.wa")
        else:
            player.simulate("sj.wa")
        
        return abs(deg(arctan(-player.vx, player.vz)))

    # RETURNERS:
    def outz(self, centered_about: float = 0, /, label: str = "outz"):
        self.add_to_output(ExpressionType.Z_LABEL, label, self.z, centered_about)
    
    def zmm(self, centered_about: float = 0, /, label: str = "zmm"):
        self.add_to_output(ExpressionType.Z_LABEL, label, PlayerSimulationXZ.dist_to_mm(self.z), centered_about)
    
    def zb(self, centered_about: float = 0, /, label: str = "zb"):
        self.add_to_output(ExpressionType.Z_LABEL, label, PlayerSimulationXZ.dist_to_block(self.z), centered_about)
    
    def outvz(self, centered_about: float = 0, /, label: str = "vz"):
        self.add_to_output(ExpressionType.Z_LABEL, label, self.vz, centered_about)

    def outx(self, centered_about: float = 0, /, label: str = "outx"):
        self.add_to_output(ExpressionType.X_LABEL, label, self.x, centered_about)

    def xmm(self, centered_about: float = 0, /, label: str = "xmm"):
        self.add_to_output(ExpressionType.X_LABEL, label, PlayerSimulationXZ.dist_to_mm(self.x), centered_about)

    def xb(self, centered_about: float = 0, /, label: str = "xb"):
        self.add_to_output(ExpressionType.X_LABEL, label, PlayerSimulationXZ.dist_to_block(self.x), centered_about)

    def outvx(self, centered_about: float = 0, /, label: str = "vx"):
        self.add_to_output(ExpressionType.X_LABEL, label, self.vx, centered_about)

    def vec(self):
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, "Speed", sqrt(self.vx**2 + self.vz**2))
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, "Angle", deg(arctan(-self.vx, self.vz)))
    
    def outangle(self, centered_about: float = 0, /, label: str = "facing"):
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, label, self.rotation, centered_about)
    
    def outturn(self, centered_about: float = 0, /, label: str = "turn"):
        self.add_to_output(ExpressionType.GENERAL_LABEL_WITH_NUMBER, label, self.last_turn, centered_about)

    def effectsmultiplier(self, speed: int = None, slow: int = None):
        if speed is None:
            speed = self.speed_effect
        if slow is None:
            slow = self.slow_effect

        if speed < 0 or 256 < speed:
            raise ValueError(f"argument 'speed' should be an integer between 0 and 256 inclusive, not {speed}")
        if slow < 0 or 256 < slow:
            raise ValueError(f"argument 'slow' should be an integer between 0 and 256 inclusive, not {slow}")

        multiplier = max((1 + (0.2 * speed)) * (1 - (0.15 * slow)), 0) * 100
        self.add_to_output(ExpressionType.GENERAL_LABEL, f"Speed {speed} Slow {slow} ({int(round(multiplier))}% base speed)")

    def angleinfo(self, angle: f32 = f32(0.0)):
        angle_rad = angle * f32(self.pi) / f32(180)
        sin_index = u64(i32(angle_rad * f32(10430.378)) & 65535)
        cos_index = u64(i32(angle_rad * f32(10430.378) + f32(16384.0)) & 65535)
        sin_value = sin(sin_index * self.pi * 2.0 / 65536)
        cos_value = sin(cos_index * self.pi * 2.0 / 65536)
        cos_index_adj = (int(cos_index) - 16384) % 65536
        # sin_value = self.mcsin(angle_rad)
        # cos_value = self.mccos(angle_rad)
        sin_angle = deg(asin(sin_value))
        cos_angle = deg(asin(cos_value))
        normal = sqrt(sin_value**2.0 + cos_value**2.0)
        print(angle, 'Sin', 'Cos', 'Normal')
        print('value', sin_value, cos_value, normal)
        print('angle', sin_angle, cos_angle)
        print('index', sin_index, cos_index_adj, cos_index)
        # print(sin_value, cos_value, sqrt(sin_value ** 2.0 + cos_value ** 2.0))

    # SETTERS
    def face(self, angle_in_degrees: f32, /):
        "Sets the player's default facing in degrees"
        self.rotation = angle_in_degrees
    
    def turn(self, angle_in_degrees: f32, /):
        "Rotates the player's default facing in degrees"
        self.rotation += angle_in_degrees

    def setposz(self, value: float, /):
        "Sets the player's Z position"
        self.z = value
    
    def setvz(self, value: float, /):
        "Sets the player's Z velocity"
        self.vz = value

    def setposx(self, value: float, /):
        "Sets the player's X position"
        self.x = value
    
    def setvx(self, value: float, /):
        "Sets the player's X velocity"
        self.vx = value
    
    def setslip(self, value: f32, /):
        "Sets the player's ground slipperiness"
        self.default_ground_slip = value
    
    def inertia(self, value: f32, /, single_axis: bool = False):
        "Sets the player's inertia threshold"
        self.inertia_threshold = value
        if single_axis:
            self.inertia_axis = 1
        else:
            self.inertia_axis = 2

    def sprintairdelay(self, toggle: bool, /):
        """
        `toggle` will toggle off if it is the string `"false"`, else it will assume true.

        Toggles the player's sprint air delay. If toggled, it takes 1 tick longer to activate sprint in midair if the previous tick was unsprinted midair. 
        
        Versions 1.8 to 1.19 have a sprint air delay while later versions don't, so if you intend to calculate 1.20+ movement, set sprint air delay to `false`.
        """
        if toggle:
            self.air_sprint_delay = True
        else:
            self.air_sprint_delay = False
    
    def sneakdelay(self, toggle: bool, /):
        """
        `toggle` will toggle true if it is the string `"true"`, else it will assume false.

        Toggles the player's sneak delay. If toggled, it takes 1 tick longer to activate sneak if the previous tick didn't sneak. 
        
        Versions 1.8 to 1.19 dont have a sneak delay while later versions do, so if you intend to calculate 1.20+ movement, set sprint air delay to `true`.
        """
        if toggle:
            self.sneak_delay = True
        else:
            self.sneak_delay = False
    
    def singleaxisinertia(self, toggle: bool, /):
        """
        Set's inertia to affect individual axis.
        """
        if toggle:
            self.inertia_axis = 1
        else:
            self.inertia_axis = 2


    def version(self, string: str, /):
        "String should be in the form `1.n`, for example the minimum `1.8` is default. Max is currently `1.20`"
        components = string.split(".")
        if len(components) == 2:
            one, version_number = components
            patch_number = 0
        elif len(components) == 3:
            one, version_number, patch_number = components
        else:
            raise ValueError(f"{string} is not a valid version")

        one = int(one)
        version_number = int(version_number)
        patch_number = int(patch_number)
    
        if one != 1:
            raise ValueError(f"{string} is not a valid version")
        if version_number > 8:
            self.inertia(0.003)
        if version_number > 13:
            self.sneakdelay("true")
        if version_number > 19 or (version_number == 19 and patch_number > 3):
            self.sprintairdelay(False)
        if version_number == 21 and patch_number >= 5:
            self.inertia_axis = 2
    
    def speed(self, multiplier: int, /):
        """
        Gives the player speed, where `speed(0)` is equivalent to no speed effects and `speed(256)` is the maximum speed effect.
        
        `multiplier` is a positive integer from 0 to 256, raises ValueError if integer provided is not within this range.
        """
        if multiplier < 0 or 256 < multiplier:
            raise ValueError(f"speed() takes an integer between 0 and 256 inclusive, not {multiplier}")
        self.speed_effect = multiplier
    
    def slowness(self, multiplier: int, /):
        """
        Gives the player slowness, where `slow(0)` is equivalent to no slow effects and `slow(7)` is the maximum slowness effect.
        
        `multiplier` is a positive integer from 0 to 256, raises ValueError if integer provided is not within this range.

        Slowness is calculated with `max(1 + (-0.15) * multiplier, 0)` so `slow(7)` already gives the maximum slowness effect which would scale ground velocity by `0`. This also means that \\
        `slow(7) = slow(8) = ... = slow(256)`

        If the slowness effect was unbounded, then `slow(7)` and stronger effects would result in moving backwards.
        """
        if multiplier < 0 or 256 < multiplier:
            raise ValueError(f"slow() takes an integer between 0 and 256 inclusive, not {multiplier}")
        self.slow_effect = multiplier

    # Setting rotations
    def anglequeue(self, *angles: f32):
        """
        Adds `angles` to the rotation queue, each angle being used for 1 tick.
        
        In mothball syntax, `anglequeue(1,-2,3) walk(3)` is the same as `face(1) walk face(-2) walk face(3) walk`
        """
        for angle in angles:
            self.angle_queue.append(angle)
    
    def turnqueue(self, *angles: float):
        """
        Adds `angles` to the rotation queue, each tick turning `angle` degrees.
        
        In mothball syntax, `turnqueue(1,-2,3) walk(3)` is the same as `turn(1) walk turn(-2) walk turn(3) walk`
        """
        for angle in angles:
            self.turn_queue.append(angle)

    # Nested functions
    
    @BasePlayer.record_to_call_stack
    def possibilities(self, sequence: MothballSequence, min_distance: float, offset: float = 0.6, /, *, increment: float = 0.0625, miss: float = None):
        """
        Displays ticks where while `sequence` is run, the player reaches certain block milestones ONLY ON Z (as determined by `increment`, default 0.0625) less than or equal to `min_distance`, useful to check which tiers results in precise landings.
        
        Use `offset` to offset each tick accordingly. An offset of 0.6 (which is default) is for jumping from block to block. An offset of -0.6 is for z neos. An offset of 0 will just record pure distances, helpful for example doing "block avoid" jumps.

        `increment` is set to 0.0625 by default, but in modern versions you can set it to 0.03125 for useful results with newer blocks.

        if a float for 'miss` is provided, it will also display ticks that are `miss` away from reaching a milestone.
        """

        if not self.record: # JUST FOR NOW
            self.record = {"type":"z", "tick":1, "min_distance": min_distance, "z offset": offset, "z increment": increment, "miss": miss}
        else:
            raise TypeError(f"Nested posibilities functions are not allowed.")
        # self.call_stack.append("possibilities")
        self.simulate(sequence, return_defaults=False)
        # self.call_stack.pop()
        self.record = {}
    
    @BasePlayer.record_to_call_stack
    def xpossibilities(self, sequence: MothballSequence, min_distance: float, offset: float = 0.6, /, *, increment: float = 0.0625, miss: float = None):
        """
        Displays ticks where while `sequence` is run, the player reaches certain block milestones ONLY ON X (as determined by `increment`, default 0.0625) less than or equal to `min_distance`, useful to check which tiers results in precise landings.
        
        Use `offset` to offset each tick accordingly. An offset of 0.6 (which is default) is for jumping from block to block. An offset of 0 will just record pure distances, helpful for example doing "block avoid" jumps.

        `increment` is set to 0.0625 by default, but in modern versions you can set it to 0.03125 for useful results with newer blocks.

        if a float for 'miss` is provided, it will also display ticks that are `miss` away from reaching a milestone.
        """
        if not self.record:
            self.record = {"type": "x", "tick":1, "min_distance": min_distance, "x offset": offset, "x increment": increment, "miss": miss}
        else:
            raise TypeError(f"Nested posibilities functions are not allowed.")
        # self.call_stack.append("xpossibilities")
        self.simulate(sequence, return_defaults=False)
        # self.call_stack.pop()
        self.record = {}
    
    @BasePlayer.record_to_call_stack
    def xzpossibilities(self, sequence: MothballSequence, min_distance: float, x_offset: float = 0.6, z_offset: float = 0.6, /, *, x_increment: float = 0.0625, z_increment: float = 0.0625, miss: float = None):
        """
        Displays ticks where while `sequence` is run, the player reaches certain block milestones (as determined by `increment`, default 0.0625) less than or equal to `min_distance`, useful to check which tiers results in precise landings.
        
        Use `offset` to offset each tick accordingly. An offset of 0.6 (which is default) is for jumping from block to block. An offset of 0 will just record pure distances, helpful for example doing "block avoid" jumps.

        `increment` is set to 0.0625 by default, but in modern versions you can set it to 0.03125 for useful results with newer blocks.

        if a float for 'miss` is provided, it will also display ticks that are `miss` away from reaching a milestone.
        """

        if not self.record:
            self.record = {"type": "xz", "tick":1, "min_distance": min_distance, "x offset": x_offset, "z offset": z_offset, "x increment":x_increment, "z increment":z_increment, "miss": miss}
        else:
            raise TypeError(f"Nested posibilities functions are not allowed.")
        self.simulate(sequence, return_defaults=False)
        self.record = {}

    @BasePlayer.record_to_call_stack
    def inertialistener(self, sequence: MothballSequence, /, tolerance: float = 0.002):
        """
        Displays ticks where while `sequence` is run, the player's velocity on EACH axis is within `tolerance` of hitting inertia, or has hit inertia.

        Inertia is determined.
        """

        if not self.record_inertia:
            self.record_inertia = {"type":"xz", "tick":1, "tolerance":tolerance}
        else:
            raise TypeError(f"Nested inertia listener functions are not allowed.")
        self.simulate(sequence, return_defaults=False)
        self.record_inertia = {}

    @BasePlayer.record_to_call_stack
    def xinertialistener(self, sequence: MothballSequence, tolerance: float = 0.002):
        """
        Displays ticks where while `sequence` is run, the player's x-velocity is below the maximum velocity (as determined by `max_vel`, default 0.01), useful to check when players are close to hitting inertia in a sequence of ticks.

        `max_vel` is set to 0.01 by default, but you can set it higher for different types of inertia (eg. ground inertia).

        """

        if not self.record_inertia: # JUST FOR NOW
            self.record_inertia = {"type":"x", "tick":1, "tolerance":tolerance}
        else:
            raise TypeError(f"Nested inertia listener functions are not allowed.")
        self.simulate(sequence, return_defaults=False)
        self.record_inertia = {}

    @BasePlayer.record_to_call_stack
    def zinertialistener(self, sequence: MothballSequence, tolerance: float = 0.002):
        """
        Displays ticks where while `sequence` is run, the player's z-velocity is below the maximum velocity (as determined by `max_vel`, default 0.01), useful to check when players are close to hitting inertia in a sequence of ticks.

        `max_vel` is set to 0.01 by default, but you can set it higher for different types of inertia (eg. ground inertia).

        """

        if not self.record: # JUST FOR NOW
            self.record_inertia = {"type":"z", "tick":1, "tolerance":tolerance}
        else:
            raise TypeError(f"Nested inertia listener functions are not allowed.")
        self.simulate(sequence, return_defaults=False)
        self.record_inertia = {}

    # SOME EXTRA MISCS
    def dimensions(self, x: float, z: float, /): # NOT FINALIZED
        """
        Returns information regarding `x` by `z` block jump. Note that `x` and `z` are in terms of blocks, that is, assuming you jump from one corner of the block to the other corner.

        In the future, there may be different functions that allow `x` and `z` in terms of displacement or momentum used.
        """
        self.add_to_output(ExpressionType.TEXT, string_or_num="Jump Dimension Info")
        self.add_to_output(ExpressionType.TEXT, string_or_num=f"\tA {x} × {z} block jump is equivalent to")

        self.add_to_output(ExpressionType.TEXT, string_or_num=f"\t{self.truncate_number(PlayerSimulationXZ.dist_to_block(sqrt(PlayerSimulationXZ.block_to_dist(x)**2 + PlayerSimulationXZ.block_to_dist(z)**2)))} block jump.")

        self.add_to_output(ExpressionType.TEXT, string_or_num=f"\tAngle: {self.truncate_number(deg(arctan(PlayerSimulationXZ.block_to_dist(z), PlayerSimulationXZ.block_to_dist(x))))}")
    
    
    @staticmethod
    def copy_player(player: "PlayerSimulationXZ"):
        "Copies the player"
        p = PlayerSimulationXZ()
        p.angle_queue = player.angle_queue
        p.rotation = player.rotation
        p.state = player.state
        p.default_ground_slip = player.default_ground_slip
        p.previous_slip = player.previous_slip
        p.air_sprint_delay = player.air_sprint_delay
        p.sneak_delay = player.sneak_delay
        p.previously_sprinting = player.previously_sprinting
        p.speed_effect = player.speed_effect
        p.slow_effect = player.slow_effect
        p.local_vars = player.local_vars
        p.call_stack = player.call_stack

        return p

    @BasePlayer.record_to_call_stack
    def taps(self, *seq_or_num: MothballSequence):
        """
        Runs each sequence until the player fully stops **on the ground**, or based on the most recent modifiers used. If a number is passed, execute the previous sequence that many times.
        
        Sequences can be provided as standalone arguments which will run once, or it can have a number following it, indicating how many times to execute it.

        NOTE 1: Sneak delay is toggled off while executing taps.

        NOTE 2: To do air taps, provide all necessary air ticks, for example `taps(stj sa sta(10))` is not the same as `taps(sa)`

        Example: `taps(sneak, 3)`. Execute `sneak` and stop moving until the player is stationary, for a total of 3 times. In parkour notation, this is equivalent to "3st W" or "3 shift tap W"

        Example: `taps(walk, stj sneakair sta(10), 2)` executes `walk` once and `stj sneakair sta(10)` twice. In parkour notation, "1ut W 2ast W".
        
        Example: `taps(walk[water](5))` walk while in water for 5t, then stops in water since the player was in water.
        """
        d = {}
        last_seq = ""
        after_num = False
        for i in seq_or_num:
            
            if i.isnumeric():
                if after_num or not d:
                    raise SyntaxError(f"Numbers must follow after a sequence. {f'{i} comes after a number' if d else f'{i} has no sequence to follow'}.")
                d[last_seq] = int(i)
                after_num = True
            elif self.isfloat(i):
                raise TypeError(f"Number should be an integer, not a float ({i})")
            else:
                last_seq = i
                d[last_seq] = 1
                after_num = False
        
        had_sneak_delay = self.sneak_delay
        self.sneak_delay = False
        for k,v in d.items():
            for _ in range(v):
                self.simulate(k, return_defaults=False)
                modifier_list = []
                for i,j in zip(self.MODIFIERS, ("water", "lava", "web", "block","ladder")):
                    if self.modifiers & i:
                        modifier_list.append(j)
                modifiers = ",".join(modifier_list)
                # self.modifiers
                while self.vx != 0 or self.vz != 0:
                    self.simulate(f"stop[{modifiers}]", return_defaults=False)
                    # self.stop()
        if had_sneak_delay:
            self.sneak_delay = True
        
        # self.call_stack.pop()

    
    def optimize(self, x: float, z: float, sequence: str, conversion = lambda x: x, /) -> tuple[float, float] | float:
        p1 = PlayerSimulationXZ.copy_player(self)
        p1.inertia_threshold = 0.0
        p1.simulate(sequence)

        p2 = PlayerSimulationXZ.copy_player(self)
        p2.inertia_threshold = 0.0
        p2.vz = 1.0
        p2.vx = 1.0
        p2.simulate(sequence)

        if x:
            if p1.x == p2.x:
                raise ZeroDivisionError(f"Float division by 0, perhaps you reset your position at the end of a sequence or nested same axis optimize functions?")
            vx = (p1.x - conversion(x)) / (p1.x - p2.x)
        if z:
            if p1.z == p2.z:
                raise ZeroDivisionError(f"Float division by 0, perhaps you reset your position at the end of a sequence or nested same axis optimize functions?")
            vz = (p1.z - conversion(z)) / (p1.z - p2.z)
        
        if x and z:
            return vx, vz
        elif x:
            return vx
        elif z:
            return vz
    
    @BasePlayer.record_to_call_stack
    def bwmm(self, zmm: float, sequence: MothballSequence, /):
        "Attempts to find the speed such that executing `sequence` results in using `zmm` blocks of momentum on the Z axis. A warning is raised if the simulation using the calculated speed doesn't match `zmm`, meaning that inertia was encountered while simulating."
        vz = self.optimize(None, zmm, sequence, PlayerSimulationXZ.mm_to_dist)


        self.simulate(f" z(0) vz({vz}) outvz(label=Vz Needed) {sequence} zmm(label=Zmm Used) ", return_defaults=False)

        if abs(PlayerSimulationXZ.dist_to_mm(self.z) - zmm) > 1e-5:
            self.add_to_output(ExpressionType.WARNING, string_or_num="encountered inertia on Z while optimizing!")

    @BasePlayer.record_to_call_stack
    def wall(self, z: float, sequence: MothballSequence, /):
        "Attempts to find the speed such that executing `sequence` results in a displacement of `z` on the Z axis. A warning is raised if the simulation using the calculated speed doesn't match `z`, meaning that inertia was encountered while simulating."
        vz = self.optimize(None, z, sequence)


        self.simulate(f" z(0) vz({vz}) outvz(label=Vz Needed) {sequence} outz(label=Z dist)")
        

        if abs(self.z - z) > 1e-5:
            self.add_to_output(ExpressionType.WARNING, string_or_num="encountered inertia on Z while optimizing!")
    
    @BasePlayer.record_to_call_stack
    def blocks(self, zb: float, sequence: MothballSequence, /):
        "Attempts to find the speed such that executing `sequence` results in traversing `zb` blocks on the Z axis. A warning is raised if the simulation using the calculated speed doesn't match `zb`, meaning that inertia was encountered while simulating."
        vz = self.optimize(None, zb, sequence, PlayerSimulationXZ.block_to_dist)


        self.simulate(f" z(0) vz({vz}) outvz(label=Vz Needed) {sequence} zb(label=Z blocks)")
        

        if abs(PlayerSimulationXZ.dist_to_block(self.z) - zb) > 1e-5:
            self.add_to_output(ExpressionType.WARNING, string_or_num="encountered inertia on Z while optimizing!")
    
    @BasePlayer.record_to_call_stack
    def xbwmm(self, xmm: float, sequence: MothballSequence, /):
        "Attempts to find the speed such that executing `sequence` results in using `xmm` blocks of momentum on the X axis. A warning is raised if the simulation using the calculated speed doesn't match `xmm`, meaning that inertia was encountered while simulating."
        vx = self.optimize(xmm, None, sequence, PlayerSimulationXZ.mm_to_dist)


        self.simulate(f" x(0) vx({vx}) outvx(label=Vx Needed) {sequence} xmm(label=Xmm Used) ", return_defaults=False)


        if abs(PlayerSimulationXZ.dist_to_mm(self.x) - xmm) > 1e-5:
            self.add_to_output(ExpressionType.WARNING, string_or_num="encountered inertia on X while optimizing!")

    @BasePlayer.record_to_call_stack
    def xwall(self, x: float, sequence: MothballSequence, /):
        "Attempts to find the speed such that executing `sequence` results in a displacement of `x` on the X axis. A warning is raised if the simulation using the calculated speed doesn't match `x`, meaning that inertia was encountered while simulating."
        vx = self.optimize(x, None, sequence)


        self.simulate(f" x(0) vx({vx}) outvx(label=Vx Needed) {sequence} outx(label=X dist)")
        

        if abs(self.x - x) > 1e-5:
            self.add_to_output(ExpressionType.WARNING, string_or_num="encountered inertia on X while optimizing!")

    @BasePlayer.record_to_call_stack
    def xblocks(self, xb: float, sequence: MothballSequence, /):
        "Attempts to find the speed such that executing `sequence` results in traversing `xb` blocks on the X axis. A warning is raised if the simulation using the calculated speed doesn't match `xb`, meaning that inertia was encountered while simulating."
        vx = self.optimize(xb, None, sequence, PlayerSimulationXZ.block_to_dist)


        self.simulate(f" x(0) vx({vx}) outvx(label=Vx Needed) {sequence} xb(label=X blocks)")
        

        if abs(PlayerSimulationXZ.dist_to_block(self.x) - xb) > 1e-5:
            self.add_to_output(ExpressionType.WARNING, string_or_num="encountered inertia on X while optimizing!")

    def mcsin(self, rad):
        if self.total_angles == -1:
            return sin(rad)
        elif self.total_angles == 65536:
            index = int(rad * f32(10430.378)) & 65535
        else:
            index = int(1 / (2 * PlayerSimulationXZ.pi) * self.total_angles * rad) & (self.total_angles - 1)
        return f32(sin(index * self.pi * 2.0 / self.total_angles))

    def mccos(self, rad):
        if self.total_angles == -1:
            return cos(rad)
        elif self.total_angles == 65536:
            index = int(rad * f32(10430.378) + f32(16384.0)) & 65535
        else:
            index = int(1 / (2 * PlayerSimulationXZ.pi) * self.total_angles * rad + self.total_angles / 4) & (self.total_angles - 1)
        return f32(sin(index * self.pi * 2.0 / self.total_angles))
    
    def macro(self, name: str, formatting: str = 'mpk', /):
        formatting = formatting.lower().strip()
        if formatting == 'mpk':
            lines = ["X,Y,Z,YAW,PITCH,ANGLE_X,ANGLE_Y,W,A,S,D,SPRINT,SNEAK,JUMP,LMB,RMB,VEL_X,VEL_Y,VEL_Z"]
            for i in self.history:
                lines.append(f"0.0,0.0,0.0,0.0,0.0,{i.last_turn:.3f},0.0,{'true' if i.w else 'false'},{'true' if i.a else 'false'},{'true' if i.s else 'false'},{'true' if i.d else 'false'},{'true' if i.sprint else 'false'},{'true' if i.sneak else 'false'},{'true' if i.space else 'false'},false,{'true' if i.right_click else 'false'},0.0,0.0,0.0")
            self.macros[name+'.csv'] = "\n".join(lines)
        elif formatting == 'cyv': # CYV: WASD sprint sneak jump angle
            lines = []
            for i in self.history:
                lines.append(['true' if i.w else 'false','true' if i.a else 'false','true' if i.s else 'false','true' if i.d else 'false','true' if i.sprint else 'false','true' if i.sneak else 'false','true' if i.space else 'false', f'{i.last_turn:.3f}', '0.0'])
            self.macros[name+'.json'] = lines
        else:
            raise ValueError(f"No such formatting {formatting}, options are either 'mpk' or 'cyv'.")


    FUNCTIONS = BasePlayer.FUNCTIONS | {"w":walk,"walk":walk,
            "sprint":sprint, "s": sprint,
            "walkair": walkair, "wa": walkair,
            "sprintair": sprintair, "sa": sprintair,
            "walkjump": walkjump, "wj": walkjump,
            "sprintjump": sprintjump, "sj": sprintjump,
            "sneak": sneak, "sn": sneak,
            "sneakair": sneakair, "sna": sneakair,
            "sneakjump": sneakjump, "snj": sneakjump,
            "sneaksprint": sneaksprint, "sns": sneaksprint,
            "sneaksprintair": sneaksprintair, "snsa": sneaksprintair,
            "sneaksprintjump": sneaksprintjump, "snsj": sneaksprintjump,
            "sprintstrafejump": sprintstrafejump, "strafejump": sprintstrafejump, "stfj": sprintstrafejump,
            "stopground": stop, "stop": stop, "st": stop,
            "stopair": stopair, "sta": stopair,
            "stopjump": stopjump, "stj": stopjump,
            "sneakstop": sneakstop, "snst": sneakstop,
            "sneakstopair": sneakstopair, "snsta": sneakstopair,
            "sneakstopjump": sneakstopjump, "snstj": sneakstopjump,
            "walk45": walk45, "w45": walk45,
            "sprint45": sprint45, "s45": sprint45,
            "walkair45": walkair45, "wa45": walkair45,
            "sprintair45": sprintair45, "sa45": sprintair45,
            "walkjump45": walkjump45, "wj45": walkjump45,
            "sprintjump45": sprintjump45, "sj45": sprintjump45,
            "sneak45": sneak45, "sn45": sneak45,
            "sneakair45": sneakair45, "sna45": sneakair45,
            "sneakjump45": sneakjump45, "snj45": sneakjump45,
            "sprintstrafejump45": sprintstrafejump45, "strafejump45": sprintstrafejump45, "stfj45": sprintstrafejump45,
            "sneaksprint45": sneaksprint45, "sns45": sneaksprint45,
            "sneaksprintair45": sneaksprintair45, "snsa45": sneaksprintair45,
            "sneaksprintjump45": sneaksprintjump45, "snsj45": sneaksprintjump45,
            "outz": outz,
            "zmm": zmm,
            "zb": zb,
            "outvz": outvz,
            "outx": outx,
            "xmm": xmm,
            "xb": xb,
            "outvx": outvx,
            "vec": vec,
            "outangle": outangle, "outa": outangle, "outfacing": outangle, "outf": outangle,
            "outturn": outturn, "outt": outturn,
            "effectsmultiplier": effectsmultiplier, "effects": effectsmultiplier,
            'angleinfo': angleinfo, 'ai': angleinfo,
            "f": face, "face": face, "facing": face,
            "turn": turn,
            "setposz": setposz, "z": setposz,
            "setvz": setvz, "vz": setvz,
            "setposx": setposx, "x": setposx,
            "setvx": setvx, "vx": setvx,
            "setslip": setslip, "slip": setslip,
            "inertia": inertia,
            "sprintairdelay": sprintairdelay, "sdel": sprintairdelay,
            "sneakdelay": sneakdelay, "sndel": sneakdelay,
            "singleaxisinertia": singleaxisinertia, "sai": singleaxisinertia,
            "version": version, "v": version,
            "speed": speed,
            "slowness": slowness, "slow": slowness,
            "anglequeue": anglequeue, "aq": anglequeue,
            "turnqueue": turnqueue, "tq": turnqueue,
            "possibilities": possibilities, "poss": possibilities,
            "xpossibilities": xpossibilities, "xposs": xpossibilities,
            "xzpossibilities": xzpossibilities, "xzposs": xzpossibilities,
            "dimensions": dimensions, "dim": dimensions,
            "taps": taps,
            "bwmm": bwmm,
            "xbwmm": xbwmm,
            "wall": wall, "inv": wall,
            "xwall": xwall, "xinv": xwall,
            "blocks": blocks,
            "xblocks": xblocks,
            "inertialistener": inertialistener, "il": inertialistener, "xzinertialistener": inertialistener, "xzil": inertialistener,
            "xinertialistener": xinertialistener, "xil": xinertialistener,
            "zinertialistener": zinertialistener, "zil": zinertialistener,
            "macro": macro
            }
    ALIASES = BasePlayer.ALIASES
    for alias, func in FUNCTIONS.items():
        if func.__name__ in ALIASES: 
            ALIASES[func.__name__].append(alias)
        else:
            ALIASES[func.__name__] = [alias]


    def show_default_output(self):
        self.add_to_output(ExpressionType.Z_LABEL, "Z", self.z)
        self.add_to_output(ExpressionType.Z_LABEL,"VZ", self.vz)
        self.add_to_output(ExpressionType.X_LABEL,"X", self.x)
        self.add_to_output(ExpressionType.X_LABEL,"VX", self.vx)



if __name__ == "__main__":
    a = PlayerSimulationXZ()
    # s = "print(A pixel is {px} blocks\, and 8 pixels is {8*px} blocks)"
    # s = 'f(-13.875) wa.a(6) x(0) xil(wj.a wa.d(8) wa.sd(2) wa.s) outx x(0) w.s outz z(0) zil( wj.sd wa.d(2) sa.wd(9)) outz s.wd outz xmm vec | aq(-16.255, -38.185, -62.88, -76.93, -84.985, -90) xil(sj sa45(5) zmm outx sa45(7)) outx'
    # s = 'angleinfo(-45.01)'
    s = 'pre(16) r(s[ss] outvz,3) r(st[ss] outvz, 3)'
    a.simulate(s)
    a.show_output()