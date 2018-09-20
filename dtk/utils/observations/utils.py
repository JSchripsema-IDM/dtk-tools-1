import openpyxl
import numbers
import os
import re
import tempfile
import dtk.utils.io.excel as excel

from dtk.utils.observations.AgeBin import AgeBin
from dtk.utils.observations.PopulationObs import PopulationObs


class UnsupportedFileFormat(Exception): pass
class MissingRequiredWorksheet(Exception): pass
class IncompleteParameterSpecification(Exception): pass
class IncompleteAnalyzerSpecification(Exception): pass
class IncompleteDataSpecification(Exception): pass
class ParameterOutOfRange(Exception): pass
class InvalidAnalyzerWeight(Exception): pass
class AnalyzerSheetException(Exception): pass

EMPTY = [None, '', '--select--']  # not sure if this could be something else
OBS_SHEET_REGEX = re.compile('^Obs-.+$')

CUSTOM_AGE_BINS = 'Custom'
ALL_MATCHING_AGE_BINS = 'All matching'

PROVINCIAL = 'Provincial'
NON_PROVINCIAL = 'Non-provincial'


def get_sheet_from_workbook(wb, sheet_name, wb_path):
    try:
        ws = wb[sheet_name]
    except KeyError:
        raise MissingRequiredWorksheet('Required worksheet: %s not in workbook: %s' % (sheet_name, wb_path))
    return ws


def parse_ingest_data_from_xlsm(filename):
    _, file_type = os.path.splitext(filename)
    file_type = file_type.replace('.', '')
    if file_type != 'xlsm':
        raise UnsupportedFileFormat('Provided ingest file not a .xlsm file.')
    wb = openpyxl.load_workbook(filename)

    # parse params info into a list of dicts
    params = _parse_parameters(wb, wb_path=filename)

    # parse analyzer info
    analyzers = _parse_analyzers(wb, wb_path=filename)

    # parse obs data into a temporary directory of files and then load it
    reference = _parse_reference_data(wb, wb_path=filename)

    return params, reference, analyzers


def _parse_parameters(wb, wb_path):
    defined_names = excel.DefinedName.load_from_workbook(wb)
    params = list()
    params_sheetname = 'Model Parameters'
    ws = get_sheet_from_workbook(wb, sheet_name=params_sheetname, wb_path=wb_path)

    names = excel.read_list(ws=ws, range=defined_names[params_sheetname]['name'])
    dynamic = excel.read_list(ws=ws, range=defined_names[params_sheetname]['dynamic'])
    initial_value = excel.read_list(ws=ws, range=defined_names[params_sheetname]['initial_value'])
    minimum = excel.read_list(ws=ws, range=defined_names[params_sheetname]['min'])
    maximum = excel.read_list(ws=ws, range=defined_names[params_sheetname]['max'])
    map_to = excel.read_list(ws=ws, range=defined_names[params_sheetname]['map_to'])

    param_name_strings = ['Name', 'Dynamic', 'Guess', 'Min', 'Max']
    for i in range(len(names)):
        param_tuple = [names[i], dynamic[i], initial_value[i], minimum[i], maximum[i]]
        n_empty = len([item for item in param_tuple if item in EMPTY])
        # only keep param rows with no empty values, error on rows that are partially empty (incomplete)
        if n_empty == 0:
            # valid parameter specification
            param = dict(zip(param_name_strings, param_tuple))
            if map_to[i] not in EMPTY:
                param['MapTo'] = map_to[i]

            # verify that min <= initial_value <= max
            try:
                if initial_value[i] < minimum[i] or initial_value[i] > maximum[i]:
                    raise TypeError('')
            except TypeError:
                # capturing type errors from < > comparison AND true numeric comparison failures
                raise ParameterOutOfRange('Parameter initial value: %s out of specified range: [%s,%s] : %s' %
                                          (initial_value[i], minimum[i], maximum[i], names[i]))

            params.append(param)
        elif n_empty < len(param_tuple):
            # incomplete parameter specification
            raise IncompleteParameterSpecification('Incomplete parameter specification on row %d '
                                                   'of sheet: %s, workbook: %s' % (i, params_sheetname, wb_path))
        else:
            # valid, no parameter specified on this row
            pass
    return params


def _parse_analyzers(wb, wb_path):
    defined_names = excel.DefinedName.load_from_workbook(wb)

    analyzer_sheetname = 'Analyzers'
    ws = get_sheet_from_workbook(wb, sheet_name=analyzer_sheetname, wb_path=wb_path)

    channels = excel.read_list(ws=ws, range=defined_names[analyzer_sheetname]['channels'])
    distributions = excel.read_list(ws=ws, range=defined_names[analyzer_sheetname]['distributions'])
    provincialities = excel.read_list(ws=ws, range=defined_names[analyzer_sheetname]['provincialities'])
    age_bins = excel.read_list(ws=ws, range=defined_names[analyzer_sheetname]['age_bins'])
    weights = excel.read_list(ws=ws, range=defined_names[analyzer_sheetname]['weights'])
    custom_age_bins = excel.read_list(ws=ws, range=defined_names[analyzer_sheetname]['custom_age_bins'])

    # sheet sanity check
    for data_list in [channels, distributions, provincialities, age_bins, weights, custom_age_bins]:
        if len(data_list) != len(channels):
            raise AnalyzerSheetException('Named range inconsistency on sheet: %s workbook: %s' % (analyzer_sheetname, wb_path))

    analyzer_dicts = list()
    for i in range(len(channels)):
        # items to be used as kwargs for instantiating analyzer objects
        analyzer_dict = {
            'channel': channels[i],
            'distribution': distributions[i],
            'provinciality': provincialities[i],
            'weight': weights[i]
        }
        if age_bins[i] == CUSTOM_AGE_BINS:
            analyzer_dict['age_bins'] = custom_age_bins[i]
        elif age_bins[i] == ALL_MATCHING_AGE_BINS:
            analyzer_dict['age_bins'] = AgeBin.ALL
        else:
            analyzer_dict['age_bins'] = None # missing

        n_empty = len([item for item in analyzer_dict.values() if item in EMPTY])
        if n_empty == 0:
            # probably a valid analyzer specification
            # now verify that the weight is a number
            if not isinstance(analyzer_dict['weight'], numbers.Number):
                raise InvalidAnalyzerWeight('Analyzer weight is not a number, analyzer: %s' % analyzer_dict)
            analyzer_dicts.append(analyzer_dict)
        elif n_empty < len(analyzer_dict.values()):
            print(analyzer_dict.values())
            raise IncompleteAnalyzerSpecification('Incomplete analyzer specification on row %d '
                                                  'of sheet: %s, workbook: %s' % (i, analyzer_sheetname, wb_path))
        else:
            # valid, no analyzer specified on this row
            pass
    return analyzer_dicts


def _parse_reference_data(wb, wb_path):
    defined_names = excel.DefinedName.load_from_workbook(wb)

    # temp_dir = 'temp_dir'
    stratifiers = set()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(temp_dir, exist_ok=True)

        obs_sheets = [sn for sn in wb.sheetnames if OBS_SHEET_REGEX.match(sn)]
        for sheet_name in obs_sheets:
            ws = get_sheet_from_workbook(wb, sheet_name=sheet_name, wb_path=wb_path)

            # detect stratifiers for this channel
            sheet_stratifiers = excel.read_list(ws=ws, range=defined_names[sheet_name]['stratifiers'])
            sheet_stratifiers = [s for s in sheet_stratifiers if s not in EMPTY]
            stratifiers.update(sheet_stratifiers) # union of all stratifiers of all sheets

            # read sheet data
            csv_data = excel.read_block(ws=ws, range=defined_names[sheet_name]['csv'])

            # only keep data rows with no empty values, error on rows that are partially empty (incomplete)
            data_rows = list()
            # for row in csv_data:
            for i in range(len(csv_data)):
                row = csv_data[i]
                n_empty = len([item for item in row if item in EMPTY])
                if n_empty == 0:
                    # valid data specification
                    data_rows.append(row)
                elif n_empty < len(row):
                    # incomplete data item specification
                    raise IncompleteDataSpecification('Incomplete data specification on row %d '
                                                      'of sheet: %s, workbook: %s' % (i, sheet_name, wb_path))
                else:
                    # valid, no data on this row
                    pass

            # convert to csv string
            csv_data_string = '\n'.join([','.join([str(d) for d in row_data]) for row_data in data_rows]) + '\n'

            # write reference csv files
            obs_filename = sheet_name.replace(' ', '_') + '.csv'
            obs_path = os.path.join(temp_dir, obs_filename)
            with open(obs_path, 'w') as f:
                f.write(csv_data_string)
        reference = PopulationObs.from_directory(directory=temp_dir, stratifiers=list(stratifiers))
    return reference