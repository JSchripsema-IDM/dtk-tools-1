# Execute directly: 'python example_optimization.py'
# or via the calibtool.py script: 'calibtool run example_optimization.py'
import copy
import math
import random

from scipy.special import gammaln

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from calibtool.resamplers.CramerRaoResampler import CramerRaoResampler
from calibtool.resamplers.RandomPerturbationResampler import RandomPerturbationResampler

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

try:
    from malaria.study_sites.DielmoCalibSite import DielmoCalibSite
    from malaria.study_sites.NdiopCalibSite import NdiopCalibSite
except ImportError as e:
    message = "The malaria package needs to be installed before running this example...\n" \
                "Please run `dtk get_package malaria -v HEAD` to install"
    raise ImportError(message)

# Which simtools.ini block to use for this calibration
SetupParser.default_block = 'HPC'

# Start from a base MALARIA_SIM config builder
# This config builder will be modify by the different sites defined below
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

# List of sites we want to calibrate on
sites = [DielmoCalibSite()]

# The default plotters used in an Optimization with OptimTool
plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPlotter()  # OTP must be last because it calls gc.collect()
]

# Antigen_Switch_Rate (1e-10 to 1e-8, log)
# Falciparum_PfEMP1_Variants (900 to 1700, linear int)
# Falciparum_MSP_Variants (5 to 50, linear int)

# The following params can be changed by stopping 'calibool', making a modification, and then resuming.
# Things you can do:
# * Change the min and max, but changing the guess of an existing parameter has no effect
# * Make a dynamic parameter static and vise versa
# * Add and remove (needs testing) parameters
params = [
    {
        'Name': 'Clinical Fever Threshold High',
        'Dynamic': True,
        #'MapTo': 'Clinical_Fever_Threshold_High', # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 1.75,
        'Min': 0.5,
        'Max': 2.5
    },
    {
        'Name': 'MSP1 Merozoite Kill Fraction',
        'Dynamic': False,   # <-- NOTE: this parameter is frozen at Guess
        'MapTo': 'MSP1_Merozoite_Kill_Fraction',
        'Guess': 0.65,
        'Min': 0.4,
        'Max': 0.7
    },
    {
        'Name': 'Falciparum PfEMP1 Variants',
        'Dynamic': True,
        'MapTo': 'Falciparum_PfEMP1_Variants',
        'Guess': 1500,
        'Min': 1, # 900 [0]
        'Max': 5000 # 1700 [1e5]
    },
    {
        'Name': 'Min Days Between Clinical Incidents',
        'Dynamic': False, # <-- NOTE: this parameter is frozen at Guess
        'MapTo': 'Min_Days_Between_Clinical_Incidents',
        'Guess': 25,
        'Min': 1,
        'Max': 50
    },
]


def constrain_sample( sample ):
    """
    This function is called on every samples and allow the user to edit them before they are passed
    to the map_sample_to_model_input function.
    It is useful to round some parameters as demonstrated below.

    Can do much more here, e.g. for
    # Clinical Fever Threshold High <  MSP1 Merozoite Kill Fraction
    if 'Clinical Fever Threshold High' and 'MSP1 Merozoite Kill Fraction' in sample:
        sample['Clinical Fever Threshold High'] = \
            min( sample['Clinical Fever Threshold High'], sample['MSP1 Merozoite Kill Fraction'] )

    You can omit this function by not specifying it in the OptimTool constructor.
    :param sample: The sample coming from the next point algorithm
    :return: The sample with constrained values
    """
    # Convert Falciparum MSP Variants to nearest integer
    if 'Min Days Between Clinical Incidents' in sample:
        sample['Min Days Between Clinical Incidents'] = int( round(sample['Min Days Between Clinical Incidents']) )

    return sample


def map_sample_to_model_input(cb, sample):
    """
    This method needs to map the samples generated by the next point algorithm to the model inputs (represented here by the cb).

    It is important to note that the sample may be shared by several isntances of this function.
    Therefore it is important to deepcopy the sample at the beginning if we intend to modify it (by calling .pop() for example).
       sample = copy.deepcopy(sample)

    :param cb: The config builder representing the model inputs for this particular simulation
    :param sample: The sample containing a values for all the params. e.g. {'Clinical Fever Threshold High':1, ... }
    :return: A dictionary containing the tags that will be attached to the simulation
    """
    tags = {}
    # Make a copy of samples so we can alter it safely
    sample = copy.deepcopy(sample)

    # Can perform custom mapping, e.g. a trivial example
    if 'Clinical Fever Threshold High' in sample:
        value = sample.pop('Clinical Fever Threshold High')
        tags.update(cb.set_param('Clinical_Fever_Threshold_High', value))

    for p in params:
        if 'MapTo' in p:
            if p['Name'] not in sample:
                print('Warning: %s not in sample, perhaps resuming previous iteration' % p['Name'])
                continue
            value = sample.pop( p['Name'] )
            tags.update(cb.set_param(p['Name'], value))

    for name,value in sample.items():
        print('UNUSED PARAMETER:'+name)
    assert( len(sample) == 0 ) # All params used

    # For testing only, the duration should be handled by the site !! Please remove before running in prod!
    tags.update(cb.set_param("Simulation_Duration", 3650 + 1))
    tags.update(cb.set_param('Run_Number', random.randint(0, 1e6)))

    return tags

# Just for fun, let the numerical derivative baseline scale with the number of dimensions
volume_fraction = 0.05   # desired fraction of N-sphere area to unit cube area for numerical derivative (automatic radius scaling with N)
num_params = len([p for p in params if p['Dynamic']])
r = OptimTool.get_r(num_params, volume_fraction)

optimtool = OptimTool(params,
    constrain_sample,   # <-- WILL NOT BE SAVED IN ITERATION STATE
    mu_r = r,           # <-- radius for numerical derivatve.  CAREFUL not to go too small with integer parameters
    sigma_r = r/10.,    # <-- stdev of radius
    center_repeats = 1, # <-- Number of times to replicate the center (current guess).  Nice to compare intrinsic to extrinsic noise
    samples_per_iteration = 10  # 32 # <-- Samples per iteration, includes center repeats.  Actual number of sims run is this number times number of sites.
)

calib_manager = CalibManager(name='ExampleOptimization_cramer_test2',    # <-- Please customize this name
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool,
                             sim_runs_per_param_set=1,  # <-- Replicates
                             max_iterations=3,          # <-- Iterations
                             plotters=plotters)

# *******************************************************************
# Resampling specific code
# *******************************************************************

# Define the resamplers to run (one or more) in list order.
resample_steps = [
    # can pass kwargs directly to the underlying resampling routines if needed
    # We need to allocate per-realization (M) and cross-realization (N).
    # Note that M>p^2, where p is the number of parameters (size of θ).
    # The number of cross-realization (N) should be set depending on the uncertainty
    # of the model at the given final point (θ*).
    # To choose N, you can use Chebyshev's inequality.
    RandomPerturbationResampler(M=10,N=20),
    # We need to determine the number of sample point (num_of_pts).
    # The algorithm gives num_of_pts samples from a multi-variant gaussian with mean=θ*
    # and covariance matrix=Σ along with their corresponding log-likelihood values.
    CramerRaoResampler(num_of_pts=20)
]

# REQUIRED variable name: run_calib_args . Required key: 'resamplers'
run_calib_args = {
    'resamplers': resample_steps,
    'calib_manager': calib_manager
}


if __name__ == "__main__":
    from calibtool.ResampleManager import ResampleManager

    # initialization
    SetupParser.init()

    # Run the calibration
    calib_manager.run_calibration()

    # Run the resampling
    resample_manager = ResampleManager(steps=run_calib_args['resamplers'], calibration_manager=calib_manager)
    resample_manager.resample_and_run()
