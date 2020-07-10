"""
Evaluating the effectiveness of the different greedy algorithms using different models, number of tasks and servers
"""

from __future__ import annotations

import json
import pprint

from src.core.core import reset_model
from src.core.fixed_task import FixedTask, FixedSumSpeeds
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.value_density import policies as value_densities
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal
from src.optimal.relaxed_flexible import relaxed_flexible


# noinspection DuplicatedCode
def greedy_evaluation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 50,
                      optimal_time_limit: int = 30, fixed_optimal_time_limit: int = 30, relaxed_time_limit: int = 30):
    """
    Evaluation of different greedy algorithms

    :param model_dist: The model distribution
    :param repeat_num: The repeat
    :param repeats: Number of model runs
    :param optimal_time_limit: The compute time for the optimal algorithm
    :param fixed_optimal_time_limit: The compute time for the fixed optimal algorithm
    :param relaxed_time_limit: The compute time for the relaxed algorithm
    """
    print(f'Evaluates the greedy algorithms (plus optimal, fixed and relaxed) for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('greedy', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate()
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        algorithm_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(algorithm_results)

        # Find the optimal solution
        optimal_result = flexible_optimal(tasks, servers, optimal_time_limit)
        algorithm_results[optimal_result.algorithm] = optimal_result.store()
        optimal_result.pretty_print()
        reset_model(tasks, servers)

        # Find the fixed solution
        fixed_optimal_result = fixed_optimal(fixed_tasks, servers, fixed_optimal_time_limit)
        algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
        fixed_optimal_result.pretty_print()
        reset_model(fixed_tasks, servers)

        # Find the relaxed solution
        relaxed_result = relaxed_flexible(tasks, servers, relaxed_time_limit)
        algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
        relaxed_result.pretty_print()
        reset_model(tasks, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm] = greedy_result.store()
                    greedy_result.pretty_print()
                    reset_model(tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()
    greedy_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
