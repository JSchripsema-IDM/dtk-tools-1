import logging
from sys import exit# as exit
import os

import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal
from scipy.spatial.distance import seuclidean
from scipy.stats import uniform, norm

import statsmodels.api as sm
import matplotlib.pyplot as plt

from calibtool.NextPointAlgorithm import NextPointAlgorithm

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimTool(NextPointAlgorithm):
    '''
    OptimTool

    The basic idea of OptimTool is
    '''

    def __init__(self, params,
                 x0 = [],
                 mu_r = 0.1,
                 sigma_r = 0.02,
                 center_repeats = 2,
                 initial_samples = 1e2, # Should be a collection of samples for OptimTool, not a number of samples to draw from the prior
                 samples_per_iteration = 1e2,
                 current_state = {}
             ):

        self.x0 = x0 # Center of each iteration - resume?
        self.mu_r = mu_r
        self.sigma_r = sigma_r
        self.center_repeats = center_repeats

        self.params = params
        prior_fn = None # OptimTool does not use a prior_fn

        super(OptimTool, self).__init__(prior_fn, initial_samples, samples_per_iteration, current_state)
        '''
        self.prior_fn = prior_fn
        self.samples_per_iteration = int(samples_per_iteration)
        self.set_current_state(current_state)
        if self.samples.size == 0:
            self.set_initial_samples(initial_samples)

        self.iteration = 0
        self.max_resampling_attempts = 100  # IMIS
        self.n_dimensions = self.samples[0].size

        logger.info('%s instance with %d initial %d-dimensional samples and %d per iteration',
                    self.__class__.__name__, self.samples.shape[0], 
                    self.n_dimensions, self.samples_per_iteration)
        '''


    def set_current_state(self, state):
        print "set_current_state"
        '''
        Initialize the current state,
        either to initially empty defaults or the de-serialized state
        passed according to the 'state' argument.
        '''

        super(OptimTool, self).set_current_state(state)
        '''
        self.samples = state.get('samples', np.array([]))
        self.latest_samples = state.get('latest_samples', np.array([]))

        if (self.samples.size > 0) ^ (self.latest_samples.size > 0):
            raise Exception('Both samples (size=%d) and latest_samples (size=%d) '
                            'should be empty or already initialized.',
                            self.samples.size, self.latest_samples.size)

        self.results = state.get('results', [])
        self.priors = state.get('priors', [])
        '''

        x0f = np.array([float(x) for x in self.x0])
        self.D = state.get('D', len(self.x0))
        self.x0 = state.get('x0', x0f)
        self.X_center = state.get('X_center', [x0f]) # np.ndarray((1,self.D), buffer=np.array(x0f))

        # These could vary by iteration ...
        self.mu_r = state.get('mu_r', self.mu_r)
        self.sigma_r = state.get('sigma_r', self.sigma_r)
        self.center_repeats = state.get('center_repeats', self.center_repeats)

        #self.fitted_values_df = state.get('fitted_values_df', pd.DataFrame(columns=[['Iteration', 'Fitted'] + self.get_param_names()]) )

        tmp = state.get('fitted_values_df', None)
        if tmp is None:
            self.fitted_values_df = pd.DataFrame(columns=[['Iteration', 'Fitted'] + self.get_param_names()])
            self.fitted_values_df['Iteration'] = self.fitted_values_df['Iteration'].astype(int)
        else:
            self.fitted_values_df = pd.DataFrame.from_dict(tmp, orient='list')

        self.rsquared = state.get('rsquared', [])


    def set_initial_samples(self, initial_samples):
        print "set_initial_samples"
        #super(OptimTool, self).set_initial_samples(initial_samples)
        '''
        if isinstance(initial_samples, (int, float)):  # allow float like 1e3
            self.samples = self.sample_from_function(self.prior_fn, int(initial_samples))
        elif isinstance(initial_samples, (list, np.ndarray)):
            self.samples = np.array(initial_samples)
        else:
            raise Exception("The 'initial_samples' parameter must be a number or an array.")

        logger.debug('Initial samples:\n%s' % self.samples)
        self.latest_samples = self.samples[:]
        '''


        if isinstance(initial_samples, (int, float)):  # allow float like 1e3
            #self.samples = self.sample_from_function(self.prior_fn, int(initial_samples))
            self.samples = self.choose_hypersphere_points(initial_samples)
        elif isinstance(initial_samples, (list, np.ndarray)):
            self.samples = np.array(initial_samples)
        else:
            raise Exception("The 'initial_samples' parameter must be a number or an array.")

        logger.debug('Initial samples:\n%s' % self.samples)
        self.latest_samples = self.samples[:]


    def update_iteration(self, iteration):
        print "update_iteration"
        #super(OptimTool, self).update_iteration(iteration)
        '''
        self.iteration = iteration
        logger.info('Updating %s at iteration %d:', self.__class__.__name__, iteration)

        self.priors.extend(self.prior_fn.pdf(self.latest_samples))
        logger.debug('Priors:\n%s', self.priors)
        '''

        self.iteration = iteration
        logger.info('Updating %s at iteration %d:', self.__class__.__name__, iteration)

        print "TODO: bounds check here?"

        print 'RESULTS:', self.results
        self.latest_results = self.results[-1]

        print 'ITERATION:', self.iteration
        print 'LATEST SAMPLES:', self.latest_samples
        print 'LATEST RESULTS:', self.latest_results

        mod = sm.OLS(self.latest_results, sm.add_constant(self.latest_samples) )
        mod_fit = mod.fit()
        print mod_fit.summary()

        samples_df = pd.DataFrame(self.latest_samples, columns=self.get_param_names())
        fitted_df = pd.DataFrame(mod_fit.fittedvalues, columns=['Fitted'])
        fitted_values_this_iter = pd.concat([samples_df, fitted_df], axis=1)
        fitted_values_this_iter['Iteration'] = iteration
        self.fitted_values_df = pd.concat([self.fitted_values_df, fitted_values_this_iter])

        self.rsquared.append(mod_fit.rsquared)

        # Choose next X_center
        if mod_fit.rsquared > 0.5:  # TODO: make parameter
            m = mod_fit.params[1:] # Drop constant
            print 'Good R^2 (%f), using params: '%mod_fit.rsquared, mod_fit.params
            ascent_dir = m / np.linalg.norm( m )
            # Scale by param range
            new_center = self.X_center[-1] + [self.mu_r*(v['Max']-v['Min'])*dx for dx,v in zip(ascent_dir, self.params.values())]
            print "TODO: MAKE SURE NEW X_CENTER IS WITHIN CONSTRAINTS"
            self.X_center.append( new_center )
        else:
            max_idx = np.argmax(self.latest_results)
            self.X_center.append( self.latest_samples[max_idx] )

        if False:
            plt.plot( self.latest_results, mod_fit.fittedvalues, 'o')
            plt.plot( [min(self.latest_results), max(self.latest_results)], [min(self.latest_results), max(self.latest_results)], 'r-')
            plt.title( mod_fit.rsquared )
            plt.savefig( 'Regression_%d.png'%self.iteration )
            plt.close()

    def update_results(self, results):
        '''
        For an iteration manager to pass back the results of analyses
        on simulations by sample point to the next-point algorithm,
        for example the log-likelihoods of a calibration suite.
        '''

        self.results.append(results)
        logger.debug('Results:\n%s', self.results)


    def update_samples(self):
        print "update_samples"
        '''
        Perform linear regression.
        Compute goodness of fit.
        '''

        #super(OptimTool, self).update_samples()
        '''
        next_samples = self.sample_from_function(
            self.next_point_fn(), self.samples_per_iteration)

        self.latest_samples = self.verify_valid_samples(next_samples)
        logger.debug('Next samples:\n%s', self.latest_samples)

        self.samples = np.concatenate((self.samples, self.latest_samples))
        logger.debug('All samples:\n%s', self.samples)
        '''

        self.latest_samples = self.choose_hypersphere_points(self.samples_per_iteration)

        # Validate?
        logger.debug('Next samples:\n%s', self.latest_samples)

        self.samples = np.concatenate((self.samples, self.latest_samples))
        logger.debug('All samples:\n%s', self.samples)

        print 'UPDATED SAMPLES:\n',self.latest_samples


    def choose_hypersphere_points(self, N):
        # Pick points on hypersphere
        sn = norm(loc=0, scale=1)

        assert(N > self.center_repeats)

        deviation = []
        for i in range(N - self.center_repeats):
            rvs = sn.rvs(size = self.D)
            nrm = np.linalg.norm(rvs)

            deviation.append( [r/nrm for r in rvs] )

        rad = norm(loc = self.mu_r, scale = self.sigma_r)

        samples = np.empty([N, self.D])
        samples[:self.center_repeats] = self.X_center[-1]
        for i, dev in enumerate(deviation):
            r = rad.rvs()
            # Scale by param range
            samples[self.center_repeats + i] = [x + r * p * (v['Max']-v['Min']) for x,p,v in zip(self.X_center[-1], dev, self.params.values())]

        return samples

    def end_condition(self):
        print "end_condition"
        # Stopping Criterion:
        # Return True to stop, False to continue
        logger.info('Continuing iterations ...')
        return False

    def get_final_samples(self):
        print "get_final_samples"
        '''
        Resample Stage:
        '''
        return dict(samples=self.X_center[-1])


    def get_current_state(self) :
        print "get_current_state"
        state = super(OptimTool, self).get_current_state()

        optimtool_state = dict(
            x0 = self.x0,
            X_center = self.X_center,
            D = self.D,
            center_repeats = self.center_repeats,
            fitted_values_df = self.fitted_values_df.to_dict(orient='list'),
            rsquared = self.rsquared,
        )
        state.update(optimtool_state)
        return state

    def get_param_names(self):
        return self.params.keys()
