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


# Max speed is 165 (calculated from Asteroid constructor)
# Max distance is the diagonal of the map = norm(game_state["map_size"][0], game_state["map_size"][1])
# Can't get game_state from init, so for now I'm just going to assume it's the default 1000 x 800 -> diag = ~1280 TODO
max_collision_time = 1280 / 165  # ~7.5


class ScottDickController(KesslerController):

    def __init__(self):
        self.eval_frames = 0  # What is this?

        # self.targeting_control is the targeting rulebase, which is static in this controller.
        # Declare variables
        collision_time = ctrl.Antecedent(np.arange(0, max_collision_time, 0.02), 'collision_time')
        collision_theta_delta = ctrl.Antecedent(np.arange(-1 * math.pi, math.pi, 0.1), 'collision_theta_delta')
        ship_thrust = ctrl.Consequent(np.arange(-1, 1, 0.1), 'ship_thrust')

        bullet_time = ctrl.Antecedent(np.arange(0, 1.0, 0.002), 'bullet_time')
        theta_delta = ctrl.Antecedent(np.arange(-1 * math.pi, math.pi, 0.1), 'theta_delta')  # Radians due to Python
        ship_turn = ctrl.Consequent(np.arange(-180, 180, 1), 'ship_turn')  # Degrees due to Kessler
        ship_fire = ctrl.Consequent(np.arange(-1, 1, 0.1), 'ship_fire')
        # ship_bomb = ctrl.Consequent(np.arange(-1, 1, 0.1), 'ship_bomb')

        # Declare fuzzy sets for collision_time (how long until asteroid collides with ship)
        collision_time['S'] = fuzz.trimf(collision_time.universe, [0, 0, max_collision_time / 2])
        collision_time['M'] = fuzz.trimf(collision_time.universe, [0, max_collision_time / 2, max_collision_time])
        collision_time['L'] = fuzz.smf(collision_time.universe, 0.0, max_collision_time)

        # Declare fuzzy sets for collision_theta_delta (angle between ships heading

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

        # Declare singleton fuzzy sets for the ship_fire consequent; -1 -> don't fire, +1 -> fire; this will be  thresholded
        #   and returned as the boolean 'fire'
        ship_fire['N'] = fuzz.trimf(ship_fire.universe, [-1, -1, 0.0])
        ship_fire['Y'] = fuzz.trimf(ship_fire.universe, [0.0, 1, 1])

        # Declare sets for ship bomb as a yes or no
        # ship_bomb['N'] = fuzz.trimf(ship_bomb.universe, [-1, -1, 0.0])
        # ship_bomb['Y'] = fuzz.trimf(ship_bomb.universe, [0.0, 1, 1])

        # Declare sets for ship thrust on a range of nl to pl
        ship_thrust['NL'] = fuzz.zmf(ship_thrust.universe, -1, -0.5)
        ship_thrust['NS'] = fuzz.trimf(ship_thrust.universe, [-0.75, -0.5, 0])
        ship_thrust['Z'] = fuzz.trimf(ship_thrust.universe, [-0.5, 0, 0.5])
        ship_thrust['PS'] = fuzz.trimf(ship_thrust.universe, [0, 0.5, 0.75])
        ship_thrust['PL'] = fuzz.smf(ship_thrust.universe, 0.5, 1)

        # Declare each fuzzy rule

        rule1 = ctrl.Rule(bullet_time['L'] & theta_delta['NL'], (ship_turn['NL'], ship_fire['N']))
        # if there is a long bullet time and a large negative theta_delta, then turn left and don't fire
        rule2 = ctrl.Rule(bullet_time['L'] & theta_delta['NS'], (ship_turn['NS'], ship_fire['Y']))
        # if there is a long bullet time and a small negative theta_delta, then turn left and fire
        rule3 = ctrl.Rule(bullet_time['L'] & theta_delta['Z'], (ship_turn['Z'], ship_fire['Y']))
        # if there is a long bullet time and a zero theta_delta, then turn left and fire
        rule4 = ctrl.Rule(bullet_time['L'] & theta_delta['PS'], (ship_turn['PS'], ship_fire['Y']))
        # if there is a long bullet time and a small positive theta_delta, then turn left and fire
        rule5 = ctrl.Rule(bullet_time['L'] & theta_delta['PL'], (ship_turn['PL'], ship_fire['N']))
        # if there is a long bullet time and a large positive theta_delta, then turn left and don't fire

        rule6 = ctrl.Rule(bullet_time['M'] & theta_delta['NL'], (ship_turn['NL'], ship_fire['N']))
        # if there is a medium bullet time and a large negative theta_delta, then turn left and don't fire
        rule7 = ctrl.Rule(bullet_time['M'] & theta_delta['NS'], (ship_turn['NS'], ship_fire['Y']))
        # if there is a medium bullet time and a small negative theta_delta, then turn left and fire
        rule8 = ctrl.Rule(bullet_time['M'] & theta_delta['Z'], (ship_turn['Z'], ship_fire['Y']))
        # if there is a medium bullet time and a zero theta_delta, then turn left and fire
        rule9 = ctrl.Rule(bullet_time['M'] & theta_delta['PS'], (ship_turn['PS'], ship_fire['Y']))
        # if there is a medium bullet time and a small positive theta_delta, then turn left and fire
        rule10 = ctrl.Rule(bullet_time['M'] & theta_delta['PL'], (ship_turn['PL'], ship_fire['N']))
        # if there is a medium bullet time and a large positive theta_delta, then turn left and don't fire

        rule11 = ctrl.Rule(bullet_time['S'] & theta_delta['NL'], (ship_turn['NL'], ship_fire['Y']))
        # if there is a short bullet time and a large negative theta_delta, then turn left and fire
        rule12 = ctrl.Rule(bullet_time['S'] & theta_delta['NS'], (ship_turn['NS'], ship_fire['Y']))
        # if there is a short bullet time and a small negative theta_delta, then turn left and fire
        rule13 = ctrl.Rule(bullet_time['S'] & theta_delta['Z'], (ship_turn['Z'], ship_fire['Y']))
        # if there is a short bullet time and a zero theta_delta, then turn left and fire
        rule14 = ctrl.Rule(bullet_time['S'] & theta_delta['PS'], (ship_turn['PS'], ship_fire['Y']))
        # if there is a short bullet time and a small positive theta_delta, then turn left and fire
        rule15 = ctrl.Rule(bullet_time['S'] & theta_delta['PL'], (ship_turn['PL'], ship_fire['Y']))
        # if there is a short bullet time and a large positive theta_delta, then turn left and fire

        # Movement rules
        rule16 = ctrl.Rule(collision_time["S"], ship_thrust["PL"])
        rule17 = ctrl.Rule(collision_time["M"], ship_thrust["PS"])
        rule18 = ctrl.Rule(collision_time["L"], ship_thrust["Z"])

        # DEBUG
        # bullet_time.view()
        # theta_delta.view()
        # ship_turn.view()
        # ship_fire.view()
        # ship_thrust.view()

        # Declare the fuzzy controller, add the rules
        # This is an instance variable, and thus available for other methods in the same object. See notes.
        # self.targeting_control = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13, rule14, rule15])

        self.targeting_control = ctrl.ControlSystem()
        self.movement_control = ctrl.ControlSystem()

        self.targeting_control.addrule(rule1)
        self.targeting_control.addrule(rule2)
        self.targeting_control.addrule(rule3)
        self.targeting_control.addrule(rule4)
        self.targeting_control.addrule(rule5)
        self.targeting_control.addrule(rule6)
        self.targeting_control.addrule(rule7)
        self.targeting_control.addrule(rule8)
        self.targeting_control.addrule(rule9)
        self.targeting_control.addrule(rule10)
        self.targeting_control.addrule(rule11)
        self.targeting_control.addrule(rule12)
        self.targeting_control.addrule(rule13)
        self.targeting_control.addrule(rule14)
        self.targeting_control.addrule(rule15)

        self.movement_control.addrule(rule16)
        self.movement_control.addrule(rule17)
        self.movement_control.addrule(rule18)

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
        closest_collision = None

        for asteroid in game_state["asteroids"]:
            # y = mx + b
            # 0 = mx - y + b   <--->   0 = ax + by + c
            # https://brilliant.org/wiki/dot-product-distance-between-point-and-a-line/#:~:text=The%20distance%20between%20a%20point,and%20passes%20through%20the%20point.

            # Calculating how close the ship is to the linear line that is the asteroids trajectory
            m = asteroid["velocity"][1] / asteroid["velocity"][0]  # m = dy/dx = dy/dt / dx/dt
            b = asteroid["position"][1] - m * asteroid["position"][0]  # b = y - mx
            d = abs(m * ship_pos_x + -1 * ship_pos_y + b) / norm(m, -1)

            # Checking if a collision will occur
            will_collide = d <= ship_state["radius"] + asteroid["radius"]

            # If a collision will occur
            if will_collide:

                # Calculating when the collision will occur
                # point 1 = asteroid location, point 2 = ship location - d*norm(line normal)
                dx = asteroid["position"][0] - (ship_state["position"][0] - d * m / norm(m, -1))
                dy = asteroid["position"][1] - (ship_state["position"][1] - d * -1 / norm(m, -1))
                time_to_collide = norm(dx, dy) / norm(asteroid["velocity"][0], asteroid["velocity"][1])

                if closest_collision is None:
                    closest_collision = time_to_collide
                else:
                    if time_to_collide < closest_collision:
                        closest_collision = time_to_collide

        # ---------------------- FUZZY SYSTEM ----------------------
        # Pass the inputs to the rulebase and fire it
        shooting = ctrl.ControlSystemSimulation(self.targeting_control, flush_after_run=1)
        movement = ctrl.ControlSystemSimulation(self.movement_control, flush_after_run=1)

        shooting.input['bullet_time'] = bullet_t
        shooting.input['theta_delta'] = shooting_theta
        shooting.compute()

        movement.input["collision_time"] = closest_collision if closest_collision is not None else max_collision_time
        movement.compute()

        # Get the defuzzified outputs
        turn_rate = shooting.output['ship_turn']
        thrust = movement.output['ship_thrust'] * 480

        if shooting.output['ship_fire'] >= 0:
            fire = True
        else:
            fire = False

        self.eval_frames += 1

        # DEBUG
        # print(thrust, bullet_t, shooting_theta, turn_rate, fire)
        print(closest_collision, thrust)

        return thrust, turn_rate, fire, 0

    @property
    def name(self) -> str:
        return "Controller"
