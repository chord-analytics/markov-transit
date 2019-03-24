import argparse 
import json 
import sys
import time
import multiprocessing
import logging
import numpy as np
sys.path.append("/usr/src/")
from RouteModel.route import Model

logging.basicConfig(filename='hub_transfer_model.log',level=logging.DEBUG)

def get_probability_of_transfer(early_time_boundary:int, late_time_boundary:int, schedule_offset:int, route_A_distribution:np.array, route_B_distribution:np.array) -> float:
    """
    Description:
    Returns the chance of making a transfer at a hub between Routes A and B.

    Inputs:
    early_time_boundary: Max amount of early minutes/states you can be. 
    late_time_boundary: Max amount of late minutes/states you can be.
    schedule_offset: Number of time states that the routes are offset from each other for scheduled arrival.
    route_A_distribution: The distribution of Route A arriving at this hub at each early/lateness state.
    route_B_distribution: The distribution of Route B arriving at this hub at each early/lateness state.

    """
    transfer_probability_matrix = np.outer(route_A_distribution, route_B_distribution)
    reshift_and_bound = lambda time_state: max(min(transfer_probability_matrix.shape[0], time_state+early_time_boundary), 0)
    total_probability = 0.0
    for time_state_A in range(-early_time_boundary, late_time_boundary):
        for time_state_B in range(time_state_A-schedule_offset, late_time_boundary):
            adjusted_time_state_A = reshift_and_bound(time_state_A)
            adjusted_time_state_B = reshift_and_bound(time_state_B)
            total_probability += transfer_probability_matrix[adjusted_time_state_A, adjusted_time_state_B]
    return total_probability


parser = argparse.ArgumentParser()
parser.add_argument("--db_file", type=str, help="Path to sqlite database.")
parser.add_argument("--transfer_json", type=str, help="Path to transfers json file.")
parser.add_argument("--output_json", type=str, help="Path to the output json file.")
parser.add_argument("--early_time_boundary", type=int, help="Earlyness cut off.")
parser.add_argument("--late_time_boundary", type=int, help="Lateness cut off.")
parser.add_argument("--config_id", type=int, help="Configuration ID.")
def main():
    args = parser.parse_args()
    transfer_data = json.load(open(args.transfer_json))
    for hub in transfer_data['hubs']:
        route_distributions = {}
        for route in hub['routes']:
            try:
                model = Model.from_db(args.db_file, route['route_id'], args.config_id, -args.early_time_boundary, args.late_time_boundary)
                model.set_state_from_db(args.db_file)
                model.make_lognormal_probabilities()
                route_distributions[route['route_id']] = model.evolve_to_stop(route['stop_seq'])
            except Exception as e:
                logging.debug(e)
        n = len(route_distributions)
        transfer_time = hub['transfer_time']
        route_to_route_transfer_matrix = np.ones((n,n))
        for i, route_id_A in enumerate(route_distributions.keys()):
            for j, route_id_B in enumerate(route_distributions.keys()):
                if route_id_A != route_id_B:
                    p = get_probability_of_transfer(args.early_time_boundary, args.late_time_boundary, transfer_time, route_distributions[route_id_A], route_distributions[route_id_B])
                    route_to_route_transfer_matrix[i,j] = p
        t2 = time.time()
        hub['transfer_probability_matrix'] = route_to_route_transfer_matrix.tolist()
        hub['transfer_probability_matrix_index'] = {key:i for i,key in enumerate(route_distributions.keys())}

    with open(args.output_json, 'w') as out_json:
        json.dump(transfer_data, out_json, indent=4)
    return

if __name__ == "__main__":
    main()