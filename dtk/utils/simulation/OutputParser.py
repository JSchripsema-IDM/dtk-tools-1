import os           # mkdir, chdir, path, etc.
import json         # to read JSON output files
import numpy as np  # for reading spatial output data by node and timestep
import struct       # for binary file unpacking
import threading    # for multi-threaded job submission and monitoring

import logging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s')

# A class to parse output files
class DTKOutputParser(threading.Thread):

    def __init__(self, sim_dir, sim_id, sim_data, analyzers, semaphore=None):
        threading.Thread.__init__(self)
        self.sim_dir = sim_dir
        self.sim_id = sim_id
        self.sim_data = sim_data
        self.analyzers = analyzers
        self.raw_data = {}
        self.selected_data = {}
        self.semaphore = semaphore

    def run(self):
        try:
            # list of output files needed by any analysis
            filenames = set()
            for a in self.analyzers:
                filenames.update(a.filenames)
            filenames = list(filenames)

            # parse output files for analysis
            for filename in filenames:
                file_extension = os.path.splitext(filename)[1][1:]
                if file_extension == 'json':
                    #print(filename + ' is a JSON file.  Loading JSON output data...\n')
                    logging.debug('reading JSON')
                    self.load_json_file(filename)
                elif file_extension == 'bin' and 'SpatialReport' in filename:
                    #print(filename + ' is a binary spatial output file.  Loading BIN output data...\n')
                    self.load_bin_file(filename)
                else:
                    print(filename + ' is of an unknown type.  Skipping...')
                    continue

            # do sim-specific part of analysis on parsed output data
            for analyzer in self.analyzers:
                self.selected_data[id(analyzer)]=analyzer.apply(self)

            del self.raw_data #?
        finally:
            if self.semaphore:
                self.semaphore.release()

    def load_json_file(self, filename):
        with open(os.path.join(self.get_sim_dir(), 'output', filename)) as json_file:
            self.raw_data[filename] = json.loads(json_file.read())

    def load_bin_file(self, filename):
        with open(os.path.join(self.get_sim_dir(), 'output', filename), 'rb') as bin_file:
            data = bin_file.read(8)
            n_nodes, = struct.unpack( 'i', data[0:4] )
            n_tstep, = struct.unpack( 'i', data[4:8] )
            #print( "There are %d nodes and %d time steps" % (n_nodes, n_tstep) )

            nodeids_dtype = np.dtype( [ ( 'ids', '<i4', (1, n_nodes ) ) ] )
            nodeids = np.fromfile( bin_file, dtype=nodeids_dtype, count=1 )
            nodeids = nodeids['ids'][:,:,:].ravel()
            #print( "node IDs: " + str(nodeids) )

            channel_dtype = np.dtype( [ ( 'data', '<f4', (1, n_nodes ) ) ] )
            channel_data = np.fromfile( bin_file, dtype=channel_dtype )
            channel_data = channel_data['data'].reshape(n_tstep, n_nodes)

        self.raw_data[filename] = {'n_nodes': n_nodes,
                                   'n_tstep': n_tstep,
                                   'nodeids': nodeids,
                                   'data': channel_data}

    def get_sim_dir(self):
        return os.path.join(self.sim_dir, self.sim_id)

class CompsDTKOutputParser(DTKOutputParser):

    sim_dir_map={}

    @classmethod
    def createSimDirectoryMap(cls,exp_id):
        from COMPS.Data import Experiment, QueryCriteria

        e = Experiment.GetById(exp_id)
        sims = e.GetSimulations(QueryCriteria().Select('Id').SelectChildren('HPCJobs')).toArray()
        sim_map = { sim.getId().toString() : sim.getHPCJobs().toArray()[-1].getWorkingDirectory() for sim in sims }
        print('Populated map of %d simulation IDs to output directories' % len(sim_map))
        cls.sim_dir_map=sim_map
        return sim_map

    def get_sim_dir(self):
        return self.sim_dir_map[self.sim_id]
