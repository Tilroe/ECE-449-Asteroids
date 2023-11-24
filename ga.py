from kesslergame import Scenario, GraphicsType, TrainerEnvironment
from test import ScottDickController
import EasyGA
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pandas as pd
import random



def fitness(chromosome):
    my_test_scenario = Scenario(name='Test Scenario',
                                ship_states=[
                                    {'position': (500, 400), 'angle': 90, 'lives': 3, 'team': 1, "mines_remaining": 0},
                                ],
                                num_asteroids=10,
                                map_size=(1000, 800),
                                time_limit=60,
                                ammo_limit_multiplier=0,
                                stop_if_no_ammo=False)

    # Define Game Settings
    game_settings = {'perf_tracker': True,
                     'graphics_type': GraphicsType.Tkinter,
                     'realtime_multiplier': 20,
                     'graphics_obj': None,
                     'frequency': 30}
    game = TrainerEnvironment(settings=game_settings)  # Use this for max-speed, no-graphics simulation

    print("Starting")
    score, perf_data = game.run(scenario=my_test_scenario, controllers=[ScottDickController(chromosome)])
    print("Ended")
    return score.teams[0].asteroids_hit




ga = EasyGA.GA()

ga.gene_impl = lambda: random.randint(0, 1000)/1000
ga.chromosome_length = 32
ga.population_size = 30
ga.target_fitness_type = 'max'
ga.generation_goal = 50
ga.fitness_function_impl = fitness



currentGen = 1
while ga.active():
    print('Starting Generation: ' + str(currentGen))
    # Evolve only a certain number of generations
    ga.evolve(1)
    # Print the current generation
    ga.print_generation()
    # Print the best chromosome from that generations population
    ga.print_best_chromosome()
    # To divide the print to make it easier to look at
    print('-'*50)
    currentGen = currentGen + 1

ga.print_best_chromosome()