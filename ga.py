from kesslergame import Scenario, GraphicsType, TrainerEnvironment
import pygad
from test import ScottDickController
import EasyGA
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pandas as pd
import random



def fitness(instance, chromosome, idx):
    # print(chromosome)
    # print(idx)
    my_test_scenario = Scenario(name='Test Scenario',
                                ship_states=[
                                    {'position': (500, 400), 'angle': 90, 'lives': 3, 'team': 1},
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

    # print("Starting")
    for i in range(3):
        try:
            score, perf_data = game.run(scenario=my_test_scenario, controllers=[ScottDickController(chromosome)])
        except:
            return 0
    # print("Ended")
    return score.teams[0].asteroids_hit




def on_generation(ga_instance):
    print(f"Generation = {ga_instance.generations_completed}")
    print(f"Fitness    = {ga_instance.best_solution()[1]}")
    print(f"Best       = {ga_instance.best_solution()}")



num_generations = 2 # Number of generations.
#num_parents_mating = 5 # Number of solutions to be selected as parents in the mating pool.


if __name__ == '__main__':


    ga_instance = pygad.GA(num_generations=num_generations,
                           num_parents_mating=2,
                           fitness_func=fitness,
                           on_generation=on_generation,
                           num_genes=32,
                           sol_per_pop=5,
                           gene_space={'low': 0, 'high': 1, 'step': 0.001},
                           parallel_processing=["process", 5])

    ga_instance.run()


#
# ga = EasyGA.GA()
#
# ga.gene_impl = lambda: random.randint(0, 1000)/1000
# ga.chromosome_length = 32
# ga.population_size = 30
# ga.target_fitness_type = 'max'
# ga.generation_goal = 50
# ga.fitness_function_impl = fitness
#
#
#
# currentGen = 1
# while ga.active():
#     print('Starting Generation: ' + str(currentGen))
#     # Evolve only a certain number of generations
#     ga.evolve(1)
#     # Print the current generation
#     ga.print_generation()
#     # Print the best chromosome from that generations population
#     ga.print_best_chromosome()
#     # To divide the print to make it easier to look at
#     print('-'*50)
#     currentGen = currentGen + 1
#
# ga.print_best_chromosome()