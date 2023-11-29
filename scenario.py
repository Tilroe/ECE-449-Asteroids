# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import time

from kesslergame import Scenario, KesslerGame, GraphicsType, TrainerEnvironment
from test import ScottDickController
from graphics_both import GraphicsBoth
import EasyGA


# Define game scenario
my_test_scenario = Scenario(name='Test Scenario',
                            ship_states=[
                                {'position': (500, 400), 'angle': 90, 'lives': 3, 'team': 1, "mines_remaining": 3},
                            ],
                            # asteroid_states=[
                            #     {'position': (500, 0), 'angle': 270, 'size': 3},
                            #     {'position': (0, 400), 'angle': 0, 'size': 3}
                            # ],
                            num_asteroids=10,
                            map_size=(1000, 800),
                            time_limit=60,
                            ammo_limit_multiplier=0,
                            stop_if_no_ammo=False)

# Define Game Settings
game_settings = {'perf_tracker': True,
                 'graphics_type': GraphicsType.Tkinter,
                 'realtime_multiplier': 0,
                 'graphics_obj': None,
                 'frequency': 30}

game = KesslerGame(settings=game_settings)  # Use this to visualize the game scenario
# game = TrainerEnvironment(settings=game_settings)  # Use this for max-speed, no-graphics simulation

# Evaluate the game
pre = time.perf_counter()

ga = EasyGA.GA()

best_chromosome = "[0.758][0.508][0.946][0.358][0.732][0.606][0.039][0.95][0.698][0.945][0.941][0.241][0.126][0.775][0.979][0.277][0.478][0.113][0.958][0.144][0.041][0.214][0.038][0.001][0.565][0.285][0.865][0.486][0.664][0.359][0.263][0.766]"
# chromosome = ga.make_chromosome([float(i) for i in best_chromosome[1:-1].split("][")])
chromosome = [float(i) for i in best_chromosome[1:-1].split("][")]

print("Starting")
score, perf_data = game.run(scenario=my_test_scenario, controllers=[ScottDickController(chromosome)])
print("Ended")

# Print out some general info about the result
print('Scenario eval time: ' + str(time.perf_counter() - pre))
print(score.stop_reason)
print('Asteroids hit: ' + str([team.asteroids_hit for team in score.teams]))
print('Deaths: ' + str([team.deaths for team in score.teams]))
print('Accuracy: ' + str([team.accuracy for team in score.teams]))
print('Mean eval time: ' + str([team.mean_eval_time for team in score.teams]))
