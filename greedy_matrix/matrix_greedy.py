"""Greedy algorithm using a matrix of job and server resource allocation values"""

from __future__ import annotations
from typing import List

from core.job import Job
from core.server import Server
from core.result import Result

from greedy_matrix.allocation_value_policy import AllocationValuePolicy


def allocate_resources(job: Job, server: Server, value: AllocationValuePolicy):
    return max(((value.evaluate(job, server, s, w, r), s, w, r)
                for s in range(1, server.available_bandwidth + 1)
                for w in range(1, server.available_computation + 1)
                for r in range(1, server.available_bandwidth - s + 1)
                if job.required_storage * w * r + s * job.required_computation * r +
                s * w * job.required_results_data <= job.deadline * s * w * r), key=lambda x: x[0])


def matrix_greedy(jobs: List[Job], servers: List[Server], matrix_policy: AllocationValuePolicy):
    unallocated_jobs = jobs.copy()
    while unallocated_jobs:
        value_matrix = []
        for job in unallocated_jobs:
            for server in servers:
                if server.can_run(job):
                    value, s, w, r = allocate_resources(job, server, matrix_policy)
                    value_matrix.append((value, job, server, s, w, r))
                    
        if value_matrix:
            value, job, server, s, w, r = max(value_matrix, key=lambda x: x[0])
            job.allocate(s, w, r, server)
            server.allocate_job(job)
            unallocated_jobs.remove(job)
        else:
            break

    return Result("Matrix Greedy", jobs, servers)
