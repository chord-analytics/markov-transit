from scipy.stats import johnsonsb
import numpy as np

class Stop:
    def __init__(self, mu, sigma, on, off, thru, g_e, g_l, tau, H, dmin, dmax, Delta, stop_id, stop_name ):
        # Transition matrices
        self.pMtx = None  # Matrix for non-time-point stop
        self.tMtx = None  # Matrix for time point stop

        # Data
        self.mu = float(mu)  # Mean travel time
        self.sigma = float(sigma)  # Standard deviation of travel time
        self.nb = float(on)  # Mean boarding counts
        self.theta = float(thru)  # Mean through passenger counts
        self.na = float(off)  # Mean alighting counts

        # Model stop parameters
        self.tau = int(tau)  # Slack time
        self.gamma_e = float(g_e)  # Early penalty cost
        self.gamma_l = float(g_l)  # Late penalty cost
        self.cost = None  # Total cost placeholder

        # Passenger arrival parameters
        self.jsb_a = -1.0  # Passenger Johnson SB arrival distribution parameter 'a'
        self.jsb_b = 1.0  # Passenger Johnson SB arrival distribution parameter 'a'
        self.jsb_q = 0.8  # Passenger Johnson SB arrival distribution parameter 'q'
        self.alpha = 0.15  # Arrival distribution ratio of uninformed passengers
        self.H = H  # Route headway inherited from parent model
        self.Delta = Delta  # Shift in arrival parameters for Johnson SB

        # Other model parameters
        self.dmin = dmin  # Minimum deviation
        self.dmax = dmax  # Maximum deviation
        self.excluded = False  # Stop ineligible as time point
        self.stop_id = stop_id
        self.stop_name = stop_name




    def m(self, delta):
        # return self.uniform_m(delta)
        return self.uniform_and_johnsonsb_m(delta)

    def M(self, delta):
        return sum([self.m(d) for d in range(-1 * self.H + self.Delta, delta + 1)])

    def l(self, delta):
        return self.zero_l(delta)

    def set_p_matrix(self, mtx):
        self.pMtx = mtx

    def set_t_matrix(self, mtx):
        self.tMtx = mtx

    def set_cost(self, cost):
        self.cost = cost

    def linear_m(self, delta):
        return (self.nb/self.mu)*delta + self.nb

    def linear_l(self, delta):
        return (self.nb/self.mu)*delta

    def uniform_m(self, delta):
        if abs(delta) > self.H:
            return 0
        else:
            return self.nb/self.H

    def uniform_and_johnsonsb_m(self, delta):
        if delta < -1 * self.H + self.jsb_q:
            return 0
            # return self.nb * (self.alpha / self.H + (1 - self.alpha) * 0.1 * johnsonsb.pdf((delta + self.H - self.jsb_q) / self.H + 1.5, self.jsb_a, self.jsb_b))
        elif delta < 0:
            return self.nb * (self.alpha / self.H + (1 - self.alpha) * 0.1 * johnsonsb.pdf((delta + 0.5 - self.jsb_q) / self.H + 1, self.jsb_a, self.jsb_b))
        else:
            return self.nb * (self.alpha / self.H + (1 - self.alpha) * 0.1 * johnsonsb.pdf((delta + 0.5 - self.H - self.jsb_q) / self.H + 1, self.jsb_a, self.jsb_b))

    def uniform_l(self, delta):
        if abs(delta) > self.H:
            return 0
        else:
            return self.nb/self.H

    def johnson_sb_m(self, delta):
        pass

    def johnson_sb_l(self, delta):
        pass

    def zero_m(self, delta):
        return 0

    def zero_l(self, delta):
        return 0

    def get_random_alighting(self, dist="poisson"):
        if dist == "poisson":
            return np.random.poisson(self.na, 1)[0]

    def get_random_through(self, dist="poisson"):
        if dist == "poisson":
            return np.random.poisson(self.theta, 1)[0]

    def get_random_boarding(self, d, dist="poisson"):
        lam = self.M(d)
        print(lam)
        if dist == "poisson":
            return np.random.poisson(lam, 1)[0]
        if dist == "normal":
            return np.random.normal(lam, lam/2, 1)

    def get_random_boarding_profile(self, start=None, end=None, dist="poisson"):
        if not start:
            start = self.dmin
        if not end:
            end = self.dmax
        profile = []
        for i in range(start, end+1):
            avg = self.M(i+1)-self.M(i)
            if dist == "normal":
                randnum = np.random.normal(avg, avg/2, 1)[0]
                if randnum < 0:
                    randnum = 0
                profile.append(randnum)
            else:
                profile.append(np.random.poisson(avg, 1)[0])

        return profile
