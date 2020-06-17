
from __future__ import annotations

from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from core.pprint import print_model_solution, print_model
from src.core.result import Result

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Optional

    from core.server import Server
    from core.task import Task


def optimal_algorithm(tasks: List[Task], servers: List[Server], time_limit: int) -> Optional[Result]:
    assert 0 < time_limit, f'Time limit: {time_limit}'

    model = CpoModel('Optimal')

    # The resource speed variables and the allocation variables
    loading_speeds: Dict[Task, CpoVariable] = {}
    compute_speeds: Dict[Task, CpoVariable] = {}
    sending_speeds: Dict[Task, CpoVariable] = {}
    server_task_allocation: Dict[Tuple[Task, Server], CpoVariable] = {}

    # The maximum bandwidth and the computation that the speed can be
    max_bandwidth, max_computation = max(server.bandwidth_capacity for server in servers) - 1, \
        max(server.computation_capacity for server in servers)

    # Loop over each task to allocate the variables and add the deadline constraints
    for task in tasks:
        loading_speeds[task] = model.integer_var(min=1, max=max_bandwidth, name=f'{task.name} loading speed')
        compute_speeds[task] = model.integer_var(min=1, max=max_computation, name=f'{task.name} compute speed')
        sending_speeds[task] = model.integer_var(min=1, max=max_bandwidth, name=f'{task.name} sending speed')

        model.add((task.required_storage / loading_speeds[task]) +
                  (task.required_computation / compute_speeds[task]) +
                  (task.required_results_data / sending_speeds[task]) <= task.deadline)

        # The task allocation variables and add the allocation constraint
        for server in servers:
            server_task_allocation[(task, server)] = model.binary_var(name=f'Job {task.name} Server {server.name}')
        model.add(sum(server_task_allocation[(task, server)] for server in servers) <= 1)

    # For each server, add the resource constraint
    for server in servers:
        model.add(sum(task.required_storage * server_task_allocation[(task, server)]
                      for task in tasks) <= server.storage_capacity)
        model.add(sum(compute_speeds[task] * server_task_allocation[(task, server)]
                      for task in tasks) <= server.computation_capacity)
        model.add(sum((loading_speeds[task] + sending_speeds[task]) * server_task_allocation[(task, server)]
                      for task in tasks) <= server.bandwidth_capacity)

    # The optimisation statement
    model.maximize(sum(task.value * server_task_allocation[(task, server)] for task in tasks for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, TimeLimit=time_limit)

    # Check that it is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print(f'Optimal algorithm failed - status: {model_solution.get_solve_status()}')
        print_model_solution(model_solution)
        print_model(tasks, servers)
        return None

    # Generate the allocation of the tasks and servers
    try:
        for task in tasks:
            for server in servers:
                if model_solution.get_value(server_task_allocation[(task, server)]):
                    task.allocate(model_solution.get_value(loading_speeds[task]),
                                  model_solution.get_value(compute_speeds[task]),
                                  model_solution.get_value(sending_speeds[task]), server)
                    server.allocate_task(task)
    except (AssertionError, KeyError) as e:
        print('Error: ', e)
        print_model_solution(model_solution)
        return None

    return Result('Optimal', tasks, servers, round(model_solution.get_solve_time(), 2),
                  **{'solve status': model_solution.get_solve_status()})
