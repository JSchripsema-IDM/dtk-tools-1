import logging
import os
import numpy as np
from calibtool.analyzers.Helpers import season_channel_age_density_csv_to_pandas

from calibtool.study_sites.DensityCalibSite import DensityCalibSite

logger = logging.getLogger(__name__)


class MatsariAgeSeasonCalibSite(DensityCalibSite):
    metadata = {
        'parasitemia_bins': [0, 50, 200, 500, np.inf],  # (, 0] (0, 50] ... (50000, ]
        'age_bins': [0, 5, 15, np.inf],  # (, 5] (5, 15] (15, ],
        'seasons': ['DC2', 'DH2', 'W2'],
        'seasons_by_month': {
            'May': 'DH2',
            'September': 'W2',
            'January': 'DC2'
        },
        'village': 'Matsari'
    }

    reference_csv = os.path.join(os.path.dirname(os.getcwd()), 'calibtool', 'study_sites', 'GarkiDB.csv')

    def get_reference_data(self, reference_type):
        super(MatsariAgeSeasonCalibSite, self).get_reference_data(reference_type)

        reference_data = season_channel_age_density_csv_to_pandas(self.reference_csv, self.metadata)

        return reference_data

    def __init__(self):
        super(MatsariAgeSeasonCalibSite, self).__init__('Matsari')
