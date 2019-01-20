import csv
import numpy as np
from scipy.stats import truncnorm, skew
import math, functools
from RouteModel.stop import Stop
import matplotlib.pyplot as plt
import pickle

ZERO = 0.000000001

@functools.lru_cache(maxsize=128)
def trunclognorm_cdf(x, a, b, mean, sd):
    try:
        mu = math.log(mean / math.sqrt(1 + (sd * sd) / (mean * mean)))
        sigma = math.sqrt(math.log(1 + (sd * sd) / (mean * mean)))
        return truncnorm.cdf((math.log(x) - mu) / sigma, a, b, loc=0, scale=1)
    except ValueError:
        print(x, a, b, mean, sd)
        raise ValueError


class Model:
    def __init__(self, data, dmin, dmax):
        self.dmin = dmin
        self.dmax = dmax
        self.gamma_w = 0.11
        self.gamma_r = 0.085
        self.gamma_o = 1.969
        self.gamma_od = 1.686
        self.e_crit = -2
        self.l_crit = 5
        self.H = 20
        self.Delta = 2
        self.p0 = None
        self.set_initial_on_time()
        self.stop_list = []
        for r in data:
            self.stop_list.append(
                Stop(float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6]),
                     float(r[7]), self.H, self.dmin, self.dmax, self.Delta, r[8], r[9]))
        self.current_state = [False for i in self.stop_list]
        self.optimal_state = [i for i in self.current_state]

    @classmethod
    def from_db(cls, db, route_id, config_id, dmin, dmax):
        # Connect and query
        """
        Create a model instance from an existing model_config configuration
        :param db: Database file name
        :param route_id: route_id in the model_data table
        :param config_id: config_id in the model_data table
        :param dmin: lower bound for states
        :param dmax: upper bound for states
        :return: an instance of the MultiStateModel class
        """
        import sqlite3
        conn = sqlite3.connect(db)
        c = conn.cursor()

        sql = """
                SELECT mu, sigma, nb, na, theta, gamma_e, gamma_l, tau, stop.stop_id, stop.stop_name FROM model_data
                JOIN stop on stop.stop_id = model_data.stop_id
                WHERE route_id = ?
                AND config_id = ?
                ORDER BY stop_seq"""

        c.execute(sql, (route_id, config_id))
        res = c.fetchall()
        return cls(res, dmin, dmax)

    @staticmethod
    def from_file(filename):
        with open(filename, "rb") as infile:
            return pickle.load(infile)

    def i_to_d(self, i):
        """
        Convert matrix index to delta value
        """
        return i + self.dmin

    def d_to_i(self, d):
        """
        Convert delta value to matrix index
        """
        return d - self.dmin

    def set_initial_on_time(self):
        # Generate correctly sized vector
        p0 = [0 for i in range(self.dmin, self.dmax + 1)]
        # Set on-time probability to one
        p0[self.d_to_i(0)] = 1
        self.p0 = np.array(p0)

    def set_initial_normal(self, mu, sigma):
        self.p0 = [0 for i in range(self.dmin, self.dmax + 1)]
        # Most negative jump possible
        a = self.dmin
        # Most positive jump possible
        b = self.dmax
        for d in range(self.dmin, self.dmax):
            if d == self.dmax:  # Take all the probability above as well
                p = 1 - truncnorm.cdf(d - 0.5, a, b, loc=mu, scale=sigma)
            elif d == self.dmin:  # Take all the probability below as well
                p = truncnorm.cdf(d + 0.5, a, b, loc=mu, scale=sigma)
            else:
                p = truncnorm.cdf(d + 0.5, a, b, loc=mu, scale=sigma) - \
                    truncnorm.cdf(d - 0.5, a, b, loc=mu, scale=sigma)
            self.p0[self.d_to_i(d)] = p

    def set_initial_lognormal(self, mu, sigma):
        self.p0 = [0 for i in range(self.dmin, self.dmax + 1)]
        # Most negative jump possible
        a = self.dmin
        # Most positive jump possible
        b = self.dmax
        for d in range(1, self.dmax):
            p = trunclognorm_cdf(d + 0.5, a, b, mu, sigma) - \
                trunclognorm_cdf(d - 0.5, a, b, mu, sigma)
            self.p0[self.d_to_i(d)] = p

    def make_normal_probabilities(self):
        for stop in self.stop_list:
            mtx = []
            for row in range(self.dmin, self.dmax + 1):
                r = []
                # Most negative jump possible
                a = self.dmin - row - 0.5
                # Most positive jump possible
                b = self.dmax - row + 0.5
                for col in range(self.dmin, self.dmax + 1):
                    if col == self.dmax:  # Take all the probability above as well
                        p = 1 - truncnorm.cdf(stop.mu + self.dmax - row - 0.5, a, b, loc=stop.mu, scale=stop.sigma)
                    elif col == self.dmin:  # Take all the probability below as well
                        p = truncnorm.cdf(stop.mu + self.dmin - row + 0.5, a, b, loc=stop.mu, scale=stop.sigma)
                    else:  # Regular calculation of an interval
                        p = truncnorm.cdf(stop.mu + col - row + 0.5, a, b, loc=stop.mu, scale=stop.sigma) - \
                            truncnorm.cdf(stop.mu + col - row - 0.5, a, b, loc=stop.mu, scale=stop.sigma)
                    r.append(p)
                mtx.append(r)
            stop.set_p_matrix(mtx)
            tMtx = [i[:] for i in mtx]
            for row in tMtx:
                s = 0
                for c in range(self.dmin, stop.tau):
                    s += row[self.d_to_i(c)]
                    row[self.d_to_i(c)] = 0
                row[self.d_to_i(0)] += s
            stop.set_t_matrix(tMtx)

    def make_lognormal_probabilities(self):
        for stop in self.stop_list:
            mtx = []
            for row in range(self.dmin, self.dmax + 1):
                r = []
                # Most negative jump possible
                a = self.dmin - row - 0.5
                # Most positive jump possible
                b = self.dmax - row + 0.5
                for col in range(self.dmin, self.dmax + 1):
                    if col == self.dmax:  # Take all the probability above as well, have to exclude negative values
                        val = stop.mu + self.dmax - row - 0.5
                        if val <= 0.0:
                            val = ZERO
                        p = 1 - trunclognorm_cdf(val, a, b, stop.mu, stop.sigma)
                    elif col == self.dmin:  # Take all the probability below as well
                        # print("From {} to {}".format(row, col))
                        # print(stop.mu + self.dmin - row + 0.5)
                        val = stop.mu + self.dmin - row + 0.5
                        if val <= 0.0:
                            val = ZERO
                        p = trunclognorm_cdf(val, a, b, stop.mu, stop.sigma)
                        # print(p)
                    else:  # Regular calculation of an interval
                        val1 = stop.mu + col - row + 0.5
                        if val1 <= 0.0:
                            val1 = ZERO
                        val2 = stop.mu + col - row - 0.5
                        if val2 <= 0.0:
                            val2 = ZERO
                        p = trunclognorm_cdf(val1, a, b, stop.mu, stop.sigma) - \
                            trunclognorm_cdf(val2, a, b, stop.mu, stop.sigma)
                    # print("From {} to {}: {}".format(row, col, p))
                    r.append(p)
                mtx.append(r)
            stop.set_p_matrix(mtx)
            tMtx = [i[:] for i in mtx]
            for row in tMtx:
                s = 0
                for c in range(self.dmin, stop.tau):
                    s += row[self.d_to_i(c)]
                    row[self.d_to_i(c)] = 0
                row[self.d_to_i(0)] += s  # Set at 0, not tau, to make sure we don't skew downstream.
            stop.set_t_matrix(tMtx)

    def update_stop_matrix_lognormal(self, s_idx):
        stop = self.stop_list[s_idx]
        mtx = []
        for row in range(self.dmin, self.dmax + 1):
            r = []
            # Most negative jump possible
            a = self.dmin - row - 0.5
            # Most positive jump possible
            b = self.dmax - row + 0.5
            for col in range(self.dmin, self.dmax + 1):
                if col == self.dmax:  # Take all the probability above as well, have to exclude negative values
                    val = stop.mu + self.dmax - row - 0.5
                    if val <= 0.0:
                        val = ZERO
                    p = 1 - trunclognorm_cdf(val, a, b, stop.mu, stop.sigma)
                elif col == self.dmin:  # Take all the probability below as well
                    val = stop.mu + self.dmin - row + 0.5
                    if val <= 0.0:
                        val = ZERO
                    p = trunclognorm_cdf(val, a, b, stop.mu, stop.sigma)
                else:  # Regular calculation of an interval
                    val1 = stop.mu + col - row + 0.5
                    if val1 <= 0.0:
                        val1 = ZERO
                    val2 = stop.mu + col - row - 0.5
                    if val2 <= 0.0:
                        val2 = ZERO
                    p = trunclognorm_cdf(val1, a, b, stop.mu, stop.sigma) - \
                        trunclognorm_cdf(val2, a, b, stop.mu, stop.sigma)
                r.append(p)
            mtx.append(r)
        stop.set_p_matrix(mtx)
        tMtx = [i[:] for i in mtx]
        for row in tMtx:
            s = 0
            for c in range(self.dmin, stop.tau):
                s += row[self.d_to_i(c)]
                row[self.d_to_i(c)] = 0
            row[self.d_to_i(0)] += s
        stop.set_t_matrix(tMtx)

    def update_stop_matrix_normal(self, s_idx):
        stop = self.stop_list[s_idx]
        mtx = []
        for row in range(self.dmin, self.dmax + 1):
            r = []
            # Most negative jump possible
            a = self.dmin - row - 0.5
            # Most positive jump possible
            b = self.dmax - row + 0.5
            for col in range(self.dmin, self.dmax + 1):
                if col == self.dmax:  # Take all the probability above as well
                    p = 1 - truncnorm.cdf(stop.mu + self.dmax - row - 0.5, a, b, loc=stop.mu, scale=stop.sigma)
                elif col == self.dmin:  # Take all the probability below as well
                    # print("From {} to {}".format(row, col))
                    # print(stop.mu + self.dmin - row + 0.5)
                    p = truncnorm.cdf(stop.mu + self.dmin - row + 0.5, a, b, loc=stop.mu, scale=stop.sigma)
                    # print(p)
                else:  # Regular calculation of an interval
                    p = truncnorm.cdf(stop.mu + col - row + 0.5, a, b, loc=stop.mu, scale=stop.sigma) - \
                        truncnorm.cdf(stop.mu + col - row - 0.5, a, b, loc=stop.mu, scale=stop.sigma)
                # print("From {} to {}: {}".format(row, col, p))
                r.append(p)
            mtx.append(r)
        stop.set_p_matrix(mtx)
        tMtx = [i[:] for i in mtx]
        for row in tMtx:
            s = 0
            for c in range(self.dmin, stop.tau):
                s += row[self.d_to_i(c)]
                row[self.d_to_i(c)] = 0
            row[self.d_to_i(0)] += s
        stop.set_t_matrix(tMtx)

    def evolve_to_stop(self, s_seq):
        # Evolve the system to a stop given the current configuration state
        if s_seq > len(self.current_state):
            print("TOO LONG A STATE")
            return
        # Initial vector
        mtx = self.p0
        for j in range(s_seq):
            if self.current_state[j]:
                mtx = np.dot(mtx, self.stop_list[j].tMtx)
            else:
                mtx = np.dot(mtx, self.stop_list[j].pMtx)
        return mtx

    def next_vec(self, vec, i):
        if self.current_state[i]:
            nvec = np.dot(vec, self.stop_list[i].tMtx)
        else:
            nvec = np.dot(vec, self.stop_list[i].pMtx)
        return nvec

    def cost_at_stop(self, i, components=False):
        vec = self.evolve_to_stop(i)
        stop = self.stop_list[i]
        return self.cost_by_vec(vec, stop, i, components=components)

    def cost_by_vec(self, vec, stop, i, components=False):
        CP = stop.gamma_e * stop.na * sum(
            [vec[d] for d in range(self.dmin, self.e_crit + 1)]) + stop.gamma_l * stop.na * sum(
            [vec[d] for d in range(self.l_crit, self.dmax + 1)])
        # These costs require checking if there's a time point or not
        if self.current_state[i]:
            CE = 0
            CL = self.gamma_w * sum(
                [d * stop.M(d) * vec[self.d_to_i(d)] for d in range(stop.tau + 1, self.Delta + 1)])
            self.current_state[i] = False
            vec = self.evolve_to_stop(i)
            CT = self.gamma_r * stop.theta * sum([abs(d) * vec[d] for d in range(self.dmin, stop.tau + 1)])
            # CO = self.gamma_o * (stop.mu + sum([(stop.tau - d) * vec[d] for d in range(self.dmin, stop.tau + 1)]))
            CO = self.gamma_o * sum([(stop.tau - d) * vec[d] for d in range(self.dmin, stop.tau + 1)])
            self.current_state[i] = True
        else:
            CE = self.gamma_w * self.H * sum(
                [(stop.M(0) - stop.M(d)) * vec[self.d_to_i(d)] for d in range(-1 * self.H + self.Delta, 0)])
            CL = self.gamma_w * sum(
                [d * stop.M(d) * vec[self.d_to_i(d)] for d in range(1, self.Delta + 1)])
            CT = 0.0
            # CO = self.gamma_o * stop.mu
            CO = 0.0
        if components:
            return CE, CL, CT, CP, CO
        else:
            return CE + CL + CT + CP + CO

    def stats_at_stop(self, i):
        mtx = self.evolve_to_stop(i)
        mean = 0
        sd = 0
        for i in range(len(mtx)):
            mean += mtx[i] * self.i_to_d(i)
        for i in range(len(mtx)):
            sd += mtx[i] * (self.i_to_d(i) - mean) * (self.i_to_d(i) - mean)
        sd = math.sqrt(sd)
        sk = skew(mtx)
        return mean, sd

    def reliability_at_stop(self, i, late_start=3, early_end=-1):
        mtx = self.evolve_to_stop(i)
        p_late = sum([mtx[self.d_to_i(k)] for k in range(late_start, self.dmax + 1)])
        p_early = sum([mtx[self.d_to_i(k)] for k in range(self.dmin, early_end)])
        return p_late, p_early

    def total_cost(self):
        cost = 0
        vec = self.evolve_to_stop(1)
        for i in range(len(self.stop_list)):
            cost += self.cost_by_vec(vec, self.stop_list[i], i)
            vec = self.next_vec(vec, i)
        COD = self.gamma_od * sum([d * vec[self.d_to_i(d)] for d in range(1, self.dmax + 1)])
        cost += COD
        return cost

    def total_cost_components(self):
        vec = self.evolve_to_stop(1)
        TCE = 0
        TCL = 0
        TCT = 0
        TCP = 0
        TCO = 0
        for i in range(len(self.stop_list)):
            CE, CL, CT, CP, CO = self.cost_by_vec(vec, self.stop_list[i], i, components=True)
            TCE += CE
            TCL += CL
            TCT += CT
            TCP += CP
            TCO += CO
            vec = self.next_vec(vec, i)
        COD = self.gamma_od * sum([d * vec[self.d_to_i(d)] for d in range(1, self.dmax + 1)])
        # for v in vec:
        #     print(v)
        return TCE, TCL, TCT, TCP, TCO, COD

    def set_ground_state(self):
        self.current_state = [False for i in self.stop_list]

    def set_state_from_file(self, filename):
        self.set_ground_state()
        with open(filename) as infile:
            reader = csv.reader(infile)
            for row in reader:
                self.current_state[int(row[0])] = True

    def set_state_from_file_taus(self, filename):
        self.set_ground_state()
        with open(filename) as infile:
            reader = csv.reader(infile)
            for row in reader:
                self.current_state[int(row[0])] = True
                self.stop_list[int(row[0])].tau = int(row[1])

    def set_excluded_stops(self, excluded_list):
        # Reset exclusion
        for s in self.stop_list:
            s.excluded = False
        # Set exclusion
        for s in excluded_list:
            self.stop_list[s].excluded = True

    def set_excluded_stops_from_file(self, filename):
        for s in self.stop_list:
            s.excluded = False
        with open(filename) as infile:
            reader = csv.reader(infile)
            for row in reader:
                self.stop_list[int(row[0])].excluded = True

    def account_for_excluded(self, i, reverse=False):
        # Shifts the passed stop index to return appropriate stop sequence
        if reverse:
            return i - sum([int(s.excluded) for s in self.stop_list[:i]])
        else:
            shift = 0
            z = 0
            seq = 0
            while z < i:
                if self.stop_list[seq].excluded:
                    shift += 1
                z = seq - shift
                seq += 1
            return i + shift

    def current_state_int(self):
        return [int(i) for i in self.current_state]

    def plot_state(self, i):
        mtx = self.evolve_to_stop(i)
        x = range(self.dmin, self.dmax + 1)
        plt.plot(x, mtx)
        plt.show()

    def plot_last(self):
        x = range(self.dmin, self.dmax + 1)
        current = self.current_state
        self.set_ground_state()
        mtx1 = self.evolve_to_stop(len(self.current_state))
        self.current_state = [True for i in self.current_state]
        mtx2 = self.evolve_to_stop(len(self.current_state))
        self.current_state = current
        plt.plot(x, mtx1)
        plt.plot(x, mtx2)
        plt.show()

    def psi(self):
        return "".join([str(i) for i in self.current_state_int()])

    def print_time_points(self):
        tp_list = []
        for i in range(len(self.stop_list)):
            if self.current_state[i]:
                tp_list.append((i, self.stop_list[i].tau))
        print(tp_list)

    def get_time_points(self):
        tp_list = []
        for i in range(len(self.stop_list)):
            if self.current_state[i]:
                tp_list.append((i, self.stop_list[i].tau))
        return(tp_list)

    def config_data(self):
        data = []
        for idx, stop in enumerate(self.stop_list):
            data.append([self.current_state[idx], stop.tau, stop.stop_id, stop.stop_name])
        return data

    def write_stats(self, filename):
        with open(filename, "w") as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(["stop_seq", "mean", "sd"])
            for i in range(len(self.stop_list)):
                mean, sd = self.stats_at_stop(i)
                writer.writerow([str(i), str(mean), str(sd)])

    def save_to_file(self, filename):
        with open(filename, "wb") as outfile:
            pickle.dump(self, outfile)

    def get_random_trajectory(self):
        state_list = []
        current_state = 0
        for i in range(len(self.stop_list)):
            state = self.get_jump_at_stop(i, current_state)
            # print(state)
            current_state = self.get_jump_at_stop(i, current_state)
            state_list.append(current_state)
        return state_list

    def get_jump_at_stop(self, i, initial_state):
        # Ensure we are not transitioning outside the bounds of the model.
        if initial_state > self.dmax:
            initial_state = self.dmax
        elif initial_state < self.dmin:
            initial_state = self.dmin
        # Depending on whether the stop is a time point, select probability matrices from
        if self.current_state[i]:
            probabilities = self.stop_list[i].tMtx[self.d_to_i(initial_state)]
        else:
            probabilities = self.stop_list[i].pMtx[self.d_to_i(initial_state)]
        shift_choice = [i for i in range(self.dmin, self.dmax+1)]
        shift = np.random.choice(shift_choice, 1, p=probabilities)
        return shift[0]

    def cumulative_mean_at_stop(self, i):
        cumulative_mean = 0
        for j in range(i+1):
            cumulative_mean += self.stop_list[j].mu
        return cumulative_mean

