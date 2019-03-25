from peak_detection import indexes
import csv

from RouteModel.route import Model

def get_cost_components():
    CE = []
    CL = []
    CT = []
    CP = []
    CO = []
    CLE = []
    for i in range(len(m.stop_list)):
        if not m.stop_list[i].excluded:
            row = m.cost_at_stop(i, components=True)
            CE.append(row[0])
            CL.append(row[1])
            CT.append(row[2])
            CP.append(row[3])
            CO.append(row[4])
            CLE.append(row[0] + row[1])
    return CE, CL, CT, CP, CO, CLE


def get_high_values(CLE, thres=0.5):
    thres_value = thres*max(CLE)
    idx_list = []
    for idx, val in enumerate(CLE):
        if val > thres_value:
            idx_list.append(idx)
    return idx_list

db = "../thesis_data.db"
# conn = sqlite3.connect(db)
thres = 0.5
models = [(210, 15, thres, 9)]
# models = [(0, 1, thres, 13), (210, 6, thres, 9), (173, 1, thres, 13), (115, 1, thres, 22), (242, 1, thres, 22)]
all_taus = []
all_slack_list = []
all_costs = []
len_tp = []
tau_range = range(0, 7)

for route_id, config_id, peak_thres, H in models:
    print("==========================")
    print("      ROUTE ID {}".format(route_id))
    print("Config: {} | Headway: {}".format(config_id, H))
    print("==========================")

    # Set Data
    cost_list = []
    state_list = []
    slack_list = []
    blacklist = []
    costdelta = 100.0
    iteration = 1

    # Intialize the model
    m = Model.from_db(db, route_id, config_id, -15, 30, route_id)
    m.H = H
    print("Data fetched. Making probabilities")
    m.make_lognormal_probabilities()
    excluded_stops = [len(m.stop_list)-1,]
    m.set_excluded_stops(excluded_stops)
    outdata = []

    cur_stop = None

    print("THRESHOLD VALUE: {}".format(peak_thres))
    m.set_ground_state()
    cur_cost = m.total_cost()
    print("Initial route cost: {}".format(cur_cost))
    cost_list.append(cur_cost)
    length = len(m.stop_list)
    while iteration <= 50:
        print("Iteration {}".format(iteration))
        CE, CL, CT, CP, CO, CLE = get_cost_components()
        print("Component List Length: {}".format(len(CE)))
        # CLE_idx = indexes(CLE, thres=peak_thres)
        CLE_idx = get_high_values(CLE, thres=peak_thres)
        print("Peak Indices:", CLE_idx)
        shift_CLE = [m.account_for_excluded(i) for i in CLE_idx]
        print("Actual Peaks:", shift_CLE)
        CLE_idx = [i for i in CLE_idx if i not in blacklist]
        if len(CLE_idx) == 0:
            print("No more non-blacklisted peaks! Exiting routine")
            print(blacklist)
            break
        print("Found {} peaks".format(len(CLE_idx)))
        if iteration == 1:
            cur_stop = 0
        else:
            cur_stop = m.account_for_excluded(CLE_idx[0])
        start_cost = cur_cost
        best_tau = None
        tau_cost = start_cost
        print("Starting iteration at cost: {}".format(start_cost))

        # Set the state as a time point
        m.current_state[cur_stop] = True
        print("Placed time point at actual stop {}".format(cur_stop))

        # Check a set of slack times for the best one
        tau_list = []
        for tau in tau_range:
            # Set the tau and update the matrices for cost calculations
            m.stop_list[cur_stop].tau = tau
            m.update_stop_matrix_lognormal(cur_stop)
            new_cost = m.total_cost()
            # print("{},{}".format(tau, new_cost))
            tau_list.append(new_cost)
            if new_cost < tau_cost:
                tau_cost = new_cost
                best_tau = tau
        print("Went with tau = {} at cost {}".format(best_tau, tau_cost))
        slack_list.append(tau_list)
        all_slack_list.append(tau_list)
        if best_tau is not None:
            all_taus.append(best_tau)
            m.stop_list[cur_stop].tau = best_tau
            m.update_stop_matrix_lognormal(cur_stop)
            cur_cost = tau_cost
        else:
            print("Time point didn't improve things! Blacklisting actual stop {} with index {}".format(cur_stop, m.account_for_excluded(cur_stop, reverse=True)))
            m.current_state[m.account_for_excluded(cur_stop, reverse=True)] = False
            m.stop_list[m.account_for_excluded(cur_stop, reverse=True)].tau = 0
            blacklist.append(m.account_for_excluded(cur_stop, reverse=True))
            cur_cost = start_cost
        m.print_time_points()
        state_list.append(m.get_time_points())
        cost_list.append(cur_cost)
        costdelta = start_cost - cur_cost
        print("Cost delta: {}".format(costdelta))
        iteration += 1
    all_costs.append(cost_list)
    if len(state_list) > 0:
        tps = len(state_list[-1])
    else:
        tps = 0
    len_tp.append([length, tps])
    print("Writing files...")

    with open("peak_{}_cost_list__normal.csv".format(route_id), "w") as f:
        writer = csv.writer(f, lineterminator='\n')
        writedata = [[str(j)] for j in cost_list]
        writer.writerows(writedata)

    with open("peak_{}_state_list__normal.csv".format(route_id), "w") as f:
        writer = csv.writer(f, lineterminator='\n')
        writedata = [[str(j) for j in i] for i in state_list]
        writer.writerows(writedata)

    with open("peak_{}_slack_list__normal.csv".format(route_id), "w") as f:
        writer = csv.writer(f, lineterminator='\n')
        writedata = [[str(j) for j in i] for i in slack_list]
        writer.writerows(writedata)

with open("peak/all_taus_tau_normal.csv", "w") as f:
    writer = csv.writer(f, lineterminator='\n')
    writedata = [str(i) for i in all_taus]
    writer.writerows(writedata)

with open("peak/all_states.csv", "w") as f:
    writer = csv.writer(f, lineterminator='\n')
    writedata = [[str(j) for j in i] for i in all_slack_list]
    writer.writerows(writedata)

with open("peak/all_costs.csv", "w") as f:
    writer = csv.writer(f, lineterminator='\n')
    writedata = [[str(j) for j in i] for i in all_costs]
    writer.writerows(writedata)

with open("peak/len_tps.csv", "w") as f:
    writer = csv.writer(f, lineterminator='\n')
    writedata = [[str(j) for j in i] for i in len_tp]
    writer.writerows(writedata)