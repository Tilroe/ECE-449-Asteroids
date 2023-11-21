# ECE 449 Intelligent Systems Engineering
# Fall 2023
# Dr. Scott Dick

# Demonstration of a fuzzy tree-based controller for Kessler Game.
# Please see the Kessler Game Development Guide by Dr. Scott Dick for a
#   detailed discussion of this source code.

from kesslergame import KesslerController  # In Eclipse, the name of the library is kesslergame, not src.kesslergame
from typing import Dict, Tuple
from cmath import sqrt
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import math
import numpy as np
import matplotlib as plt


def norm(a, b) -> int:
    return sqrt(a ** 2 + b ** 2).real


def dot(a, b) -> int:
    return a[0] * b[0] + a[1] * b[1]


# Check up to time_limit to see if ship and asteroid will collide
def collision_prediction(ship, asteroid, time_limit):
    buffer = 5

    ship_pos_x = ship["position"][0]
    ship_pos_y = ship["position"][1]
    ship_vel_x = ship["velocity"][0]
    ship_vel_y = ship["velocity"][1]

    astr_pos_x = asteroid["position"][0]
    astr_pos_y = asteroid["position"][1]
    astr_vel_x = asteroid["velocity"][0]
    astr_vel_y = asteroid["velocity"][1]

    # check every 0.1 seconds
    time_step = 0.1
    for t in np.arange(0, time_limit, time_step):
        ship_pos_x += time_step * ship_vel_x
        ship_vel_y += time_step * ship_vel_y
        astr_pos_x += time_step * astr_vel_x
        astr_pos_y += time_step * astr_vel_y

        dx = ship_pos_x - astr_pos_x
        dy = ship_pos_y - astr_pos_y

        # Check for collision
        if norm(dx, dy) < ship["radius"] + asteroid["radius"] + buffer:
            # Collision has happened
            collision_angle = math.radians(ship["heading"]) - math.atan2(astr_vel_y, astr_vel_x)
            collision_angle = (collision_angle + math.pi) % (
                        2 * math.pi) - math.pi  # angle of collision, wrapped to [-pi, pi]

            collision_angle_degr = math.degrees(collision_angle)
            if collision_angle_degr < -170:
                collision_angle = math.pi # To prevent collision angle switching between like -179 and 179

            return t, collision_angle

    # Collision has not happened
    return time_limit, None


class ScottDickController(KesslerController):
    def __init__(self):
        self.eval_frames = 0  # What is this?
        self.max_collision_time = 10  # Look up to this many seconds in advance for a collision

        # self.ship_control is the targeting rulebase, which is static in this controller.
        # Declare variables
        ship_speed = ctrl.Antecedent(np.arange(-240, 240, 1), "ship_speed")  # Max speed is 240 from source files
        collision_time = ctrl.Antecedent(np.arange(0, self.max_collision_time, 0.02),
                                         'collision_time')  # time until closest collision
        collision_theta = ctrl.Antecedent(np.arange(-math.pi, math.pi, 0.1),
                                          'collision_theta')  # angle between ship heading and asteroid theta
        bullet_time = ctrl.Antecedent(np.arange(0, 1.0, 0.002), 'bullet_time')
        theta_delta = ctrl.Antecedent(np.arange(-1 * math.pi, math.pi, 0.1), 'theta_delta')  # Radians due to Python

        ship_thrust = ctrl.Consequent(np.arange(-480, 480, 1), 'ship_thrust')  # Max thrust is 480 from source files
        ship_turn = ctrl.Consequent(np.arange(-180, 180, 1), 'ship_turn')  # Degrees due to Kessler
        ship_fire = ctrl.Consequent(np.arange(-1, 1, 0.1), 'ship_fire')
        # ship_bomb = ctrl.Consequent(np.arange(-1, 1, 0.1), 'ship_bomb')

        # Declare fuzzy sets for collision_time (how long until asteroid collides with ship)
        collision_time['S'] = fuzz.trimf(collision_time.universe, [0, 0, self.max_collision_time / 2])
        collision_time['M'] = fuzz.trimf(collision_time.universe,
                                         [0, self.max_collision_time / 2, self.max_collision_time])
        collision_time['L'] = fuzz.trimf(collision_time.universe,
                                         [self.max_collision_time / 2, self.max_collision_time / 2,
                                          self.max_collision_time])

        # Declare fuzzy sets for ship_speed
        ship_speed['N'] = fuzz.trimf(ship_speed.universe, [-240, -240, 0])
        ship_speed['Z'] = fuzz.trimf(ship_speed.universe, [-10, 0, 10])
        ship_speed['P'] = fuzz.trimf(ship_speed.universe, [0, 240, 240])

        # Declare fuzzy sets for collision theta
        collision_theta['NL'] = fuzz.trimf(collision_theta.universe, [-math.pi, -math.pi, -math.pi / 2])
        collision_theta['NM'] = fuzz.trimf(collision_theta.universe,
                                           [-math.pi * 3 / 4, - math.pi / 2, - math.pi * 1 / 4])
        collision_theta['NS'] = fuzz.trimf(collision_theta.universe, [-math.pi / 2, -math.pi * 1 / 4, 0])
        collision_theta['Z'] = fuzz.trimf(collision_theta.universe, [-math.pi * 1 / 4, 0, math.pi * 1 / 4])
        collision_theta['PS'] = fuzz.trimf(collision_theta.universe, [0, math.pi * 1 / 4, math.pi / 2])
        collision_theta['PM'] = fuzz.trimf(collision_theta.universe, [math.pi * 1 / 4, math.pi / 2, math.pi * 3 / 4])
        collision_theta['PL'] = fuzz.trimf(collision_theta.universe, [math.pi / 2, math.pi, math.pi])

        # Declare sets for ship thrust on a range of nl to pl
        ship_thrust['NL'] = fuzz.zmf(ship_thrust.universe, -480, -120)
        ship_thrust['NS'] = fuzz.trimf(ship_thrust.universe, [-240, -120, 0])
        ship_thrust['Z'] = fuzz.trimf(ship_thrust.universe, [-60, 0, 60])
        ship_thrust['PS'] = fuzz.trimf(ship_thrust.universe, [0, 120, 240])
        ship_thrust['PL'] = fuzz.smf(ship_thrust.universe, 120, 480)

        # Declare fuzzy sets for bullet_time (how long it takes for the bullet to reach the intercept point)
        bullet_time['S'] = fuzz.trimf(bullet_time.universe, [0, 0, 0.05])
        bullet_time['M'] = fuzz.trimf(bullet_time.universe, [0, 0.05, 0.1])
        bullet_time['L'] = fuzz.smf(bullet_time.universe, 0.0, 0.1)

        # Declare fuzzy sets for theta_delta (degrees of turn needed to reach the calculated firing angle)
        theta_delta['NL'] = fuzz.zmf(theta_delta.universe, -1 * math.pi / 3, -1 * math.pi / 6)
        theta_delta['NS'] = fuzz.trimf(theta_delta.universe, [-1 * math.pi / 3, -1 * math.pi / 6, 0])
        theta_delta['Z'] = fuzz.trimf(theta_delta.universe, [-1 * math.pi / 6, 0, math.pi / 6])
        theta_delta['PS'] = fuzz.trimf(theta_delta.universe, [0, math.pi / 6, math.pi / 3])
        theta_delta['PL'] = fuzz.smf(theta_delta.universe, math.pi / 6, math.pi / 3)
        # theta_delta.view()

        # Declare fuzzy sets for the ship_turn consequent; this will be returned as turn_rate.
        ship_turn['NL'] = fuzz.trimf(ship_turn.universe, [-180, -180, -30])
        ship_turn['NS'] = fuzz.trimf(ship_turn.universe, [-90, -30, 0])
        ship_turn['Z'] = fuzz.trimf(ship_turn.universe, [-30, 0, 30])
        ship_turn['PS'] = fuzz.trimf(ship_turn.universe, [0, 30, 90])
        ship_turn['PL'] = fuzz.trimf(ship_turn.universe, [30, 180, 180])

        # Declare singleton fuzzy sets for the ship_fire consequent; -1 -> don't fire, +1 -> fire; this will be
        # thresholded and returned as the boolean 'fire'
        ship_fire['N'] = fuzz.trimf(ship_fire.universe, [-1, -1, 0.0])
        ship_fire['Y'] = fuzz.trimf(ship_fire.universe, [0.0, 1, 1])

        # Declare sets for ship bomb as a yes or no
        # ship_bomb['N'] = fuzz.trimf(ship_bomb.universe, [-1, -1, 0.0])
        # ship_bomb['Y'] = fuzz.trimf(ship_bomb.universe, [0.0, 1, 1])

        # Declare each fuzzy rule

        # --- Shooting rules ---
        rule1 = ctrl.Rule(ship_speed['Z'] & bullet_time['L'] & theta_delta['NL'], (ship_turn['NL'], ship_fire['N'], ship_thrust['Z']))
        # if there is a long bullet time and a large negative theta_delta, then turn left and don't fire
        rule2 = ctrl.Rule(ship_speed['Z'] & bullet_time['L'] & theta_delta['NS'], (ship_turn['NS'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a long bullet time and a small negative theta_delta, then turn left and fire
        rule3 = ctrl.Rule(ship_speed['Z'] & bullet_time['L'] & theta_delta['Z'], (ship_turn['Z'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a long bullet time and a zero theta_delta, then turn left and fire
        rule4 = ctrl.Rule(ship_speed['Z'] & bullet_time['L'] & theta_delta['PS'], (ship_turn['PS'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a long bullet time and a small positive theta_delta, then turn left and fire
        rule5 = ctrl.Rule(ship_speed['Z'] & bullet_time['L'] & theta_delta['PL'], (ship_turn['PL'], ship_fire['N'], ship_thrust['Z']))
        # if there is a long bullet time and a large positive theta_delta, then turn left and don't fire

        rule6 = ctrl.Rule(ship_speed['Z'] & bullet_time['M'] & theta_delta['NL'], (ship_turn['NL'], ship_fire['N'], ship_thrust['Z']))
        # if there is a medium bullet time and a large negative theta_delta, then turn left and don't fire
        rule7 = ctrl.Rule(ship_speed['Z'] & bullet_time['M'] & theta_delta['NS'], (ship_turn['NS'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a medium bullet time and a small negative theta_delta, then turn left and fire
        rule8 = ctrl.Rule(ship_speed['Z'] & bullet_time['M'] & theta_delta['Z'], (ship_turn['Z'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a medium bullet time and a zero theta_delta, then turn left and fire
        rule9 = ctrl.Rule(ship_speed['Z'] & bullet_time['M'] & theta_delta['PS'], (ship_turn['PS'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a medium bullet time and a small positive theta_delta, then turn left and fire
        rule10 = ctrl.Rule(ship_speed['Z'] & bullet_time['M'] & theta_delta['PL'], (ship_turn['PL'], ship_fire['N'], ship_thrust['Z']))
        # if there is a medium bullet time and a large positive theta_delta, then turn left and don't fire

        rule11 = ctrl.Rule(ship_speed['Z'] & bullet_time['S'] & theta_delta['NL'], (ship_turn['NL'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a short bullet time and a large negative theta_delta, then turn left and fire
        rule12 = ctrl.Rule(ship_speed['Z'] & bullet_time['S'] & theta_delta['NS'], (ship_turn['NS'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a short bullet time and a small negative theta_delta, then turn left and fire
        rule13 = ctrl.Rule(ship_speed['Z'] & bullet_time['S'] & theta_delta['Z'], (ship_turn['Z'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a short bullet time and a zero theta_delta, then turn left and fire
        rule14 = ctrl.Rule(ship_speed['Z'] & bullet_time['S'] & theta_delta['PS'], (ship_turn['PS'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a short bullet time and a small positive theta_delta, then turn left and fire
        rule15 = ctrl.Rule(ship_speed['Z'] & bullet_time['S'] & theta_delta['PL'], (ship_turn['PL'], ship_fire['Y'], ship_thrust['Z']))
        # if there is a short bullet time and a large positive theta_delta, then turn left and fire

        # --- Movement rules ---
        # low collision risk rules, slow down to stationary
        rule16 = ctrl.Rule(collision_time['L'] & ship_speed['P'], ship_thrust['NS'])
        rule17 = ctrl.Rule(collision_time['L'] & ship_speed['N'], ship_thrust['PS'])
        rule18 = ctrl.Rule(collision_time['L'] & ship_speed['Z'], ship_thrust['Z'])

        # medium collision risk rules
        rule19 = ctrl.Rule(collision_time['M'] & collision_theta['NL'], (ship_turn['PS'], ship_thrust['Z'], ship_fire['N']))
        rule20 = ctrl.Rule(collision_time['M'] & collision_theta['NM'], (ship_turn['Z'], ship_thrust['PS'], ship_fire['N']))
        rule21 = ctrl.Rule(collision_time['M'] & collision_theta['NS'], (ship_turn['NS'], ship_thrust['Z'], ship_fire['N']))
        rule22 = ctrl.Rule(collision_time['M'] & collision_theta['Z'],
                           (ship_turn['NS'], ship_thrust['Z'], ship_fire['N']))  # default turn right when asteroid coming head on
        rule23 = ctrl.Rule(collision_time['M'] & collision_theta['PS'], (ship_turn['PS'], ship_thrust['Z'], ship_fire['N']))
        rule24 = ctrl.Rule(collision_time['M'] & collision_theta['PM'], (ship_turn['Z'], ship_thrust['Z'], ship_fire['N']))
        rule25 = ctrl.Rule(collision_time['M'] & collision_theta['PL'], (ship_turn['NS'], ship_thrust['Z'], ship_fire['N']))

        # high collision risk rules
        rule26 = ctrl.Rule(collision_time['S'] & collision_theta['NL'], (ship_turn['PS'], ship_thrust['Z'], ship_fire['N']))
        rule27 = ctrl.Rule(collision_time['S'] & collision_theta['NM'], (ship_turn['Z'], ship_thrust['PL'], ship_fire['N']))
        rule28 = ctrl.Rule(collision_time['S'] & collision_theta['NS'], (ship_turn['NS'], ship_thrust['Z'], ship_fire['N']))
        rule29 = ctrl.Rule(collision_time['S'] & collision_theta['Z'],
                           (ship_turn['NS'], ship_thrust['PS'], ship_fire['N']))  # default turn right when asteroid coming head on
        rule30 = ctrl.Rule(collision_time['S'] & collision_theta['PS'], (ship_turn['PS'], ship_thrust['Z'], ship_fire['N']))
        rule31 = ctrl.Rule(collision_time['S'] & collision_theta['PM'], (ship_turn['Z'], ship_thrust['PL'], ship_fire['N']))
        rule32 = ctrl.Rule(collision_time['S'] & collision_theta['PL'], (ship_turn['NS'], ship_thrust['Z'], ship_fire['N']))

        # DEBUG
        # bullet_time.view()
        # theta_delta.view()
        # ship_speed.view()
        # collision_time.view()
        # collision_theta.view()
        #
        # ship_turn.view()
        # ship_fire.view()
        # ship_thrust.view()

        # Declare the fuzzy controller, add the rules
        # This is an instance variable, and thus available for other methods in the same object. See notes.
        # self.ship_control = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13, rule14, rule15])

        self.ship_control = ctrl.ControlSystem()

        self.ship_control.addrule(rule1)
        self.ship_control.addrule(rule2)
        self.ship_control.addrule(rule3)
        self.ship_control.addrule(rule4)
        self.ship_control.addrule(rule5)
        self.ship_control.addrule(rule6)
        self.ship_control.addrule(rule7)
        self.ship_control.addrule(rule8)
        self.ship_control.addrule(rule9)
        self.ship_control.addrule(rule10)
        self.ship_control.addrule(rule11)
        self.ship_control.addrule(rule12)
        self.ship_control.addrule(rule13)
        self.ship_control.addrule(rule14)
        self.ship_control.addrule(rule15)
        self.ship_control.addrule(rule16)
        self.ship_control.addrule(rule17)
        self.ship_control.addrule(rule18)
        self.ship_control.addrule(rule19)
        self.ship_control.addrule(rule20)
        self.ship_control.addrule(rule21)
        self.ship_control.addrule(rule22)
        self.ship_control.addrule(rule23)
        self.ship_control.addrule(rule24)
        self.ship_control.addrule(rule25)
        self.ship_control.addrule(rule26)
        self.ship_control.addrule(rule27)
        self.ship_control.addrule(rule28)
        self.ship_control.addrule(rule29)
        self.ship_control.addrule(rule30)
        self.ship_control.addrule(rule31)
        self.ship_control.addrule(rule32)

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool]:
        """
        Method processed each time step by this controller.
        """
        # These were the constant actions in the basic demo, just spinning and shooting.
        # thrust = 0 <- How do the values scale with asteroid velocity vector?
        # turn_rate = 90 <- How do the values scale with asteroid velocity vector?

        # Answers: Asteroid position and velocity are split into their x,y components in a 2-element ?array each.
        # So are the ship position and velocity, and bullet position and velocity.
        # Units appear to be meters relative to origin (where?), m/sec, m/sec^2 for thrust.
        # Everything happens in a time increment: delta_time, which appears to be 1/30 sec; this is hardcoded in many places.
        # So, position is updated by multiplying velocity by delta_time, and adding that to position.
        # Ship velocity is updated by multiplying thrust by delta time.
        # Ship position for this time increment is updated after the the thrust was applied.

        # My demonstration controller does not move the ship, only rotates it to shoot the nearest asteroid.
        # Goal: demonstrate processing of game state, fuzzy controller, intercept computation
        # Intercept-point calculation derived from the Law of Cosines, see notes for details and citation.

        # ---------------------- BULLET INTERCEPT CALCULATION ----------------------

        # Find the closest asteroid (disregards asteroid velocity)
        ship_pos_x = ship_state["position"][0]  # See src/kesslergame/ship.py in the KesslerGame Github
        ship_pos_y = ship_state["position"][1]
        closest_asteroid = None

        for a in game_state["asteroids"]:
            # Loop through all asteroids, find minimum Eudlidean distance
            curr_dist = math.sqrt((ship_pos_x - a["position"][0]) ** 2 + (ship_pos_y - a["position"][1]) ** 2)
            if closest_asteroid is None:
                # Does not yet exist, so initialize first asteroid as the minimum. Ugh, how to do?
                closest_asteroid = dict(aster=a, dist=curr_dist)

            else:
                # closest_asteroid exists, and is thus initialized.
                if closest_asteroid["dist"] > curr_dist:
                    # New minimum found
                    closest_asteroid["aster"] = a
                    closest_asteroid["dist"] = curr_dist

        # closest_asteroid is now the nearest asteroid object.
        # Calculate intercept time given ship & asteroid position, asteroid velocity vector, bullet speed (not direction).
        # Based on Law of Cosines calculation, see notes.

        # Side D of the triangle is given by closest_asteroid.dist. Need to get the asteroid-ship direction
        #    and the angle of the asteroid's current movement.
        # REMEMBER TRIG FUNCTIONS ARE ALL IN RADAINS!!!

        asteroid_ship_x = ship_pos_x - closest_asteroid["aster"]["position"][0]
        asteroid_ship_y = ship_pos_y - closest_asteroid["aster"]["position"][1]

        asteroid_ship_theta = math.atan2(asteroid_ship_y, asteroid_ship_x)

        asteroid_direction = math.atan2(closest_asteroid["aster"]["velocity"][1], closest_asteroid["aster"]["velocity"][
            0])  # Velocity is a 2-element array [vx,vy].
        my_theta2 = asteroid_ship_theta - asteroid_direction
        cos_my_theta2 = math.cos(my_theta2)
        # Need the speeds of the asteroid and bullet. speed * time is distance to the intercept point
        asteroid_vel = math.sqrt(
            closest_asteroid["aster"]["velocity"][0] ** 2 + closest_asteroid["aster"]["velocity"][1] ** 2)
        bullet_speed = 800  # Hard-coded bullet speed from bullet.py

        # Determinant of the quadratic formula b^2-4ac
        targ_det = (-2 * closest_asteroid["dist"] * asteroid_vel * cos_my_theta2) ** 2 - (
                4 * (asteroid_vel ** 2 - bullet_speed ** 2) * closest_asteroid["dist"])

        # Combine the Law of Cosines with the quadratic formula for solve for intercept time. Remember, there are two values produced.
        intrcpt1 = ((2 * closest_asteroid["dist"] * asteroid_vel * cos_my_theta2) + math.sqrt(targ_det)) / (
                2 * (asteroid_vel ** 2 - bullet_speed ** 2))
        intrcpt2 = ((2 * closest_asteroid["dist"] * asteroid_vel * cos_my_theta2) - math.sqrt(targ_det)) / (
                2 * (asteroid_vel ** 2 - bullet_speed ** 2))

        # Take the smaller intercept time, as long as it is positive; if not, take the larger one.
        if intrcpt1 > intrcpt2:
            if intrcpt2 >= 0:
                bullet_t = intrcpt2
            else:
                bullet_t = intrcpt1
        else:
            if intrcpt1 >= 0:
                bullet_t = intrcpt1
            else:
                bullet_t = intrcpt2

        # Calculate the intercept point. The work backwards to find the ship's firing angle my_theta1.
        intrcpt_x = closest_asteroid["aster"]["position"][0] + closest_asteroid["aster"]["velocity"][0] * bullet_t
        intrcpt_y = closest_asteroid["aster"]["position"][1] + closest_asteroid["aster"]["velocity"][1] * bullet_t

        my_theta1 = math.atan2((intrcpt_y - ship_pos_y), (intrcpt_x - ship_pos_x))

        # Lastly, find the difference between firing angle and the ship's current orientation. BUT THE SHIP HEADING IS IN DEGREES.
        shooting_theta = my_theta1 - ((math.pi / 180) * ship_state["heading"])

        # Wrap all angles to (-pi, pi)
        shooting_theta = (shooting_theta + math.pi) % (2 * math.pi) - math.pi

        # ---------------------- ASTEROID-SHIP COLLISION CALCULATION ----------------------
        closest_collision = self.max_collision_time
        collision_angle = 0

        for asteroid in game_state["asteroids"]:
            collision_time, angle = collision_prediction(ship_state, asteroid, self.max_collision_time)
            if collision_time < closest_collision:
                closest_collision = collision_time
                collision_angle = angle

        if closest_collision < self.max_collision_time:
            degr = collision_angle * 180 / math.pi
            print(f"Predicted collision: t = {closest_collision:.1f}, theta = {degr:.1f}")

        # ---------------------- FUZZY SYSTEM ----------------------
        # Pass the inputs to the rulebase and fire it
        control = ctrl.ControlSystemSimulation(self.ship_control, flush_after_run=1)

        control.input['bullet_time'] = bullet_t
        control.input['theta_delta'] = shooting_theta
        control.input["collision_time"] = closest_collision
        control.input["collision_theta"] = collision_angle
        control.input["ship_speed"] = ship_state["speed"]

        control.compute()

        # Get the defuzzified outputs
        turn_rate = control.output['ship_turn']
        thrust = control.output['ship_thrust']
        fire = True if control.output['ship_fire'] >= 0 else False

        self.eval_frames += 1

        # DEBUG
        # print(thrust, bullet_t, shooting_theta, turn_rate, fire)
        # speed = ship_state["speed"]
        # print(f"next collision: {closest_collision:.2f}, thrust: {thrust:.1f}, speed: {speed:.1f}")

        return thrust, turn_rate, fire, 0

    @property
    def name(self) -> str:
        return "Controller"
