import requests
import logging
import sys
import os
import json

class UMARestService:
    def __init__(self, host='localhost', port='8000'):
        #self.logger = logging.getLogger("RestService")
        #self.logger.setLevel(logging.DEBUG)
        self._headers = {'Content-type': 'application/json', 'Accpet': 'text/plain'}
        self._base_url = "http://%s:%s" % (host, port)
        #self._log = open('./client.txt', 'w')

    def post(self, uri, data):
        uri = self._base_url + uri
        try:
            r = requests.post(uri, data=json.dumps(data), headers=self._headers)
        except Exception, e:
            print str(e)
            #self._log.write("Errors while doing post request " + uri + ': ' + str(e) + '\n')
            return None
        if r.status_code >= 400 and r.status_code < 500:
            print str(r.json()['message'])
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

    def get(self, uri, query):
        uri = self._base_url + uri
        retry = 0
        while retry < 5:
            try:
                r = requests.get(uri, params=query, headers=self._headers)
                break
            except:
                #self._log.write("Errors while doing get request " + uri + '\n')
                retry += 1
                if retry == 5:
                    return None

        if r.status_code >= 400 and r.status_code < 500:
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

    def put(self, uri, data, query):
        uri = self._base_url + uri
        try:
            r = requests.put(uri, data=json.dumps(data), params=query, headers=self._headers)
        except Exception, e:
            #self._log.write("Errors while doing put request " + uri + '\n')
            print str(e)
            return None
        if r.status_code >= 400 and r.status_code < 500:
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

    def delete(self, uri, data):
        uri = self._base_url + uri
        try:
            r = requests.delete(uri, data=json.dumps(data), headers=self._headers)
        except:
            #self._log.write("Errors while doing put request " + uri + '\n')
            return None
        if r.status_code >= 400 and r.status_code < 500:
            #self._log.write("Client Error(" + str(r.status_code) + "): " + str(r.json()['message'] + '\n'))
            return None
        if r.status_code >= 500:
            #self._log.write("Server Error(" + str(r.status_code) + ") please check server log" + '\n')
            return None
        #self._log.write("(" + str(r.status_code) + ") " + str(r.json()['message']) + '\n')
        return r.json()

class UMAClientObject:
    def __init__(self, service):
        self._service = service

    def get_service(self):
        return self._service

# Client class for World
class UMAClientWorld(UMAClientObject):
    def __init__(self, service):
        # self.logger = logging.getLogger("ClientWorld")
        self._service = service
        pass

    # add an UMA Experiment object
    # if creation succeed, it will return a client experiment object
    def add_experiment(self, experiment_id):
        data = {'experiment_id': experiment_id}
        result = self._service.post('/UMA/object/experiment', data)
        if not result:
            print "create experiment=%s failed!" % experiment_id
            return None
        else:
            return UMAClientExperiment(experiment_id, self.get_service())

    # delete an UMA Experiment object
    def delete_experiment(self, experiment_id):
        data = {'experiment_id': experiment_id}
        result = self._service.delete('/UMA/object/experiment', data)
        if not result:
            print "delete experiment=%s failed!" % experiment_id
            return None

    # get the available experiment name in the current world
    def get_world(self):
        result = self._service.get('/UMA/world', data={})
        if not result:
            print "get world info failed!"
            return None
        else:
            return result['data']

    # reset the UMA World, which will remove the current world and recreate a new one
    def reset(self):
        result = self._service.post('/UMA/world/reset', data={})
        if not result:
            print "World reset failed"
            return False
        return True

# Client class for Experiment
class UMAClientExperiment(UMAClientObject):
    def __init__(self, experiment_id, service):
        #self.logger = logging.getLogger("ClientExperiment")
        self._service = service
        self._experiment_id = experiment_id

    # return the experiment id
    def get_experiment_id(self):
        return self._experiment_id

    # get the experiment info
    def get_experiment_info(self):
        data = {'experiment_id': self._experiment_id}
        result = self._service.get('/UMA/object/experiment', data)
        if not result:
            return None
        else:
            return result['data']

    # add an UMA Agent object
    # if succeed, will return a client Agent object
    def add_agent(self, agent_id, **kwargs):
        data = {'experiment_id': self._experiment_id, 'agent_id': agent_id}
        data.update(kwargs)
        result = self._service.post('/UMA/object/agent', data)
        if not result:
            print "create agent=%s failed!" % agent_id
            return None
        else:
            return UMAClientAgent(self._experiment_id, agent_id, self.get_service())

    # make a decision
    def make_decision(self, signals, state):
        data = {'experiment_id': self._experiment_id, 'signals': signals, 'state': state}
        result = self._service.post('/UMA/simulation/decision', data)
        if not result:
            return None
        result = result['data']
        return result

    def register_sensors(self, sensors):
        data = {'experiment_id': self._experiment_id, 'mids': sensors}
        result = self._service.post(uri='/UMA/object/experiment/register', data=data)
        if not result:
            print "error register sensors to UMACore!"
            exit()


# Client class for Agent
class UMAClientAgent(UMAClientObject):
    def __init__(self, experiment_id, agent_id, service):
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id

    # get experiment id
    def get_experiment_id(self):
        return self._experiment_id

    # get the agent id
    def get_agent_id(self):
        return self._agent_id

    # get agent info, which contains all bua information
    def get_agent_info(self):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id}
        result = self._service.get('/UMA/object/agent', data)
        if not result:
            return None
        else:
            return result['data']

    # add an UMA bua object
    # if succeed, will return an UMA client object
    def add_bua(self, bua_id, type, **kwargs):
        data = {'agent_id': self._agent_id, 'bua_id': bua_id, 'type': type}
        data.update(kwargs)
        result = self._service.post('/UMA/object/bua', data)
        if not result:
            print "create bua=%s failed!" % bua_id
            return None
        else:
            return UMAClientBua(self._experiment_id, self._agent_id, bua_id, self.get_service())

    # save agent
    # NOT TESTED
    def save_agent(self, filename):
        data = {'experiment_id': self._experiment_id, 'bua_id': self._bua_id, 'filename': filename}
        result = self._service.post('/UMA/object/bua/save', data)
        if not result:
            print "Saving Bua=%s failed!" % self._bua_id
        else:
            print "Bua=%s is successfully saved!" % self._bua_id

    # experiment_id is the experiment the loaded bua will go into, filename is the filename to read
    # bua id is id of new bua, it can be different from the old one from file
    # NOT TESTED
    def load_bua(self, filename):
        data = {'experiment_id': self._experiment_id,' bua_id': self._bua_id, 'filename': filename}
        result = self._service.post('/UMA/object/bua/load', data)

        if not result:
            print "Loading Bua=%s failed!" % self._bua_id
        else:
            print "Bua=%s is successfully loaded!" % self._bua_id

# Client class for Bua
class UMAClientBua(UMAClientObject):
    def __init__(self, experiment_id, agent_id, bua_id, service):
        #self.logger = logging.getLogger("ClientAgent")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._bua_id = bua_id

    # get experiment id
    def get_experiment_id(self):
        return self._experiment_id

    # get agent id
    def get_agent_id(self):
        return self._agent_id

    # get bua id
    def get_bua_id(self):
        return self._bua_id

    # get bua info
    def get_bua_info(self):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id, 'bua_id': self._bua_id}
        result = self._service.get('/UMA/object/bua', data)
        if not result:
            return None
        else:
            return result['data']

    # add an UMA snapshot object
    # if succeed, will return an UMA client object
    def add_snapshot(self, snapshot_id):
        data = {'snapshot_id': snapshot_id, 'bua_id': self._bua_id}
        result = self._service.post('/UMA/object/snapshot', data)
        if not result:
            print "create snapshot=%s failed!" % snapshot_id
            return None
        else:
            return UMAClientSnapshot(self._experiment_id, self._agent_id, self._bua_id, snapshot_id, self.get_service())

    def add_instruction(self, instructions):
        query = {'bua_id': self._bua_id}
        data = {'instructions': instructions}
        result = self._service.put('/UMA/object/bua', query=query, data=data)
        if not result:
            print "add instruction to %s failed!" % self._bua_id

    def add_phi_generator(self, phi_generator_id):
        query = {'bua_id': self._bua_id}
        data = {'phi_generator_id': phi_generator_id}
        result = self._service.put('/UMA/object/bua', query=query, data=data)
        if not result:
            print "add phi generator to %s failed!" % self._bua_id

    # copy an UMA bua
    # NOT TESTED
    def copy_bua(self, to_experiment_id, new_agent_id):
        data = {'experiment_id1': self._experiment_id, 'agent_id1': self._agent_id,
                'experiment_id2': to_experiment_id, 'agent_id2': new_agent_id}
        result = self._service.post('/UMA/object/agent/copy', data=data)

        if not result:
            print "agent copy from %s:%s to %s failed!" % (self._experiment_id, self._agent_id, to_experiment_id)

        # get the schema for the newly created agent
        res = {}
        query = {'experiment_id': to_experiment_id, 'agent_id': new_agent_id}
        agent_info = self._service.get('/UMA/object/agent', query=query)['data']
        res['agent_id'] = new_agent_id
        res['type'] = agent_info['type']

        for snapshot_id, snapshot_type in agent_info['snapshot_ids']:
            query = {'experiment_id': to_experiment_id, 'agent_id': new_agent_id, 'snapshot_id': snapshot_id}
            snapshot_info = self._service.get('/UMA/object/snapshot', query=query)
            res[snapshot_id] = snapshot_info['data']

        return res

# CLient class for Snapshot
class UMAClientSnapshot(UMAClientObject):
    def __init__(self, experiment_id, agent_id, bua_id, snapshot_id, service):
        #self.logger = logging.getLogger("ClientSnapshot")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._bua_id = bua_id
        self._snapshot_id = snapshot_id

    # get experiment id
    def get_experiment_id(self):
        return self._experiment_id

    # get agent id
    def get_agent_id(self):
        return self._agent_id

    # get bua id
    def get_bua_id(self):
        return self._bua_id

    # get snapshot id
    def get_snapshot_id(self):
        return self._snapshot_id

    # get snapshot info
    def get_snapshot_info(self):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id,
                'bua_id': self._bua_id, 'snapshot_id': self._snapshot_id}
        result = self._service.get('/UMA/object/snapshot', data)
        if not result:
            return None
        else:
            return result['data']

    # add UMA Sensor object
    # if succeed, will return UMA client object
    def add_sensor(self, sensor_id, c_sensor_id):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id,
                'bua_id': self._bua_id, 'snapshot_id': self._snapshot_id,
                'sensor_id': sensor_id, 'c_sid': c_sensor_id, 'w': [], 'd': [], 'diag': []}
        result =  self._service.post('/UMA/object/sensor', data)
        if not result:
            print "add sensor=%s failed!" % sensor_id
            return None
        else:
            return UMAClientSensor(self._experiment_id, self._agent_id, self._bua_id, self._snapshot_id, sensor_id, self.get_service())

    # init the snapshot
    def init(self):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id,
                'bua_id': self._bua_id, 'snapshot_id': self._snapshot_id}
        result = self._service.post('/UMA/object/snapshot/init', data)
        if not result:
            print "snapshot=%s init fail!" % self._snapshot_id
            return None
        return result

    # set auto target flag
    def set_auto_target(self, auto_target):
        return self._service.put('/UMA/object/snapshot', {'auto_target': auto_target}, {'experiment_id': self._experiment_id,
                        'bua_id': self._bua_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    # set propagate mask flag
    def set_propagate_mask(self, propagate_mask):
        return self._service.put('/UMA/object/snapshot', {'propagate_mask': propagate_mask}, {'experimentId': self._experiment_id,
                        'agent_id': self._agent_id, 'bua_id': self._bua_id, 'snapshot_id': self._snapshot_id})

    # set initial size
    def set_initial_size(self, initial_size):
        return self._service.put('/UMA/object/snapshot', {'initial_size': initial_size}, {'experiment_id': self._experiment_id,
                        'bua_id': self._bua_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    # set q
    def set_q(self, q):
        return self._service.put('/UMA/object/snapshot', {'q': q}, {'experiment_id': self._experiment_id,
                       'bua_id': self._bua_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    # set threshold
    def set_threshold(self, threshold):
        return self._service.put('/UMA/object/snapshot', {'threshold': threshold}, {'experiment_id': self._experiment_id,
                       'bua_id': self._bua_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    # delay operation
    def delay(self, delay_list, uuid_list):
        data = {'experiment_id': self._experiment_id, 'agent_id': self._agent_id,
                'bua_id': self._bua_id, 'snapshot_id': self._snapshot_id,
                'delay_lists': delay_list, 'uuid_lists': uuid_list}
        result = self._service.post('/UMA/object/snapshot/delay', data)
        if not result:
            return False
        return True

    # pruning operation
    def pruning(self, signal):
        data = {'experiment_id': self._experiment_id, 'bua_id': self._bua_id, 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                'signals': signal}
        result = self._service.post('/UMA/object/snapshot/pruning', data)
        if not result:
            return False
        return True

# client class for Data
class UMAClientData:
    def __init__(self, experiment_id, agent_id, bua_id, snapshot_id, service):
        #self.logger = logging.getLogger("ClientData")
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._bua_id = bua_id
        self._snapshot_id = snapshot_id

    def get_experiment_id(self):
        return self._experiment_id

    def get_agent_id(self):
        return self._agent_id

    def get_bua_id(self):
        return self._bua_id

    def get_snapshot_id(self):
        return self._snapshot_id

    # get current signal
    def getCurrent(self):
        return self._service.get('/UMA/data/current', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                                    'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    # get prediction signal
    def getPrediction(self):
        return self._service.get('/UMA/data/prediction', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                                    'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

    # get target signal
    def getTarget(self):
        return self._service.get('/UMA/data/target', {'experiment_id': self._experiment_id ,'bua_id': self._bua_id,
                                    'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['target']

    # get negligible signal
    def getNegligible(self):
        return self._service.get('/UMA/data/negligible', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['negligible']

    # get npdir matrix
    def get_npdirs(self):
        return self._service.get('/UMA/data/npdirs', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['npdirs']

    # get dir matrix
    def get_dirs(self):
        return self._service.get('/UMA/data/dirs', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['dirs']

    # get weight matrix
    def get_weights(self):
        return self._service.get('/UMA/data/weights', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['weights']

    # get propagate mask signal
    def get_propagate_masks(self):
        return self._service.get('/UMA/data/propagateMasks', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['propagate_masks']

    # get all signal
    def get_all(self):
        return self._service.get('/UMA/data/all', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']

    # get mask amper matrix
    def get_mask_amper(self):
        return self._service.get('/UMA/data/maskAmper', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})['data']['mask_amper']

    # set target
    def setTarget(self, target):
        return self._service.put('/UMA/data/target',{'target': target}, {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                        'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id})

# client object for Sensor
class UMAClientSensor:
    def __init__(self, experiment_id, agent_id, bua_id, snapshot_id, sensor_id, service):
        self._service = service
        self._experiment_id = experiment_id
        self._agent_id = agent_id
        self._bua_id = bua_id
        self._snapshot_id = snapshot_id
        self._sensor_id = sensor_id

    def get_experiment_id(self):
        return self._experiment_id

    def get_agent_id(self):
        return self._agent_id

    def get_snapshot_id(self):
        return self._snapshot_id

    def get_sensor_id(self):
        return self._sensor_id

    # get the amper list of the sensor
    def getAmperList(self):
        result = self._service.get('/UMA/object/sensor', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                            'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id, 'sensor_id': self._sensor_id})
        if not result:
            return None
        result = result['data']['amper_list']
        return result

    # get amper list by id
    def getAmperListID(self):
        result = self._service.get('/UMA/object/sensor', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                            'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id, 'sensor_id': self._sensor_id})
        if not result:
            return None
        result = result['data']['amper_list_id']
        return result

    # set the amper list
    def setAmperList(self, amper_list):
        result = self._service.post('/UMA/object/sensor', {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                            'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id, 'sensor_id': self._sensor_id,
                            'amper_list': amper_list})
        if not result:
            return None
        return result

class UMAClientAttrSensor:
    def __init__(self):
        #self.logger = logging.getLogger("ClientAttrSensor")
        pass

# Client class for Envelope
class UMAClientEnvelope:
    def __init__(self, service, envelope_id, **kwargs):
        self._service = service
        self._envelope_id = envelope_id

    def add_envelope(self, **kwargs):
        data = {'envelope_id': self._envelope_id}
        data.update(kwargs)
        self._service.post('/UMA/object/envelope', data=data)

# Client class for SignalGenerator
class UMAClientSignalGenerator:
    def __init__(self, service, sg_id):
        self._sg_id = sg_id
        self._service = service

    def add_signal_generator(self, envelope_id, sg_name, processor_type):
        data = {'signal_generator_id': self._sg_id, 'signal_generator_name': sg_name,
                'envelope_id': envelope_id, 'processor_type': processor_type}
        self._service.post('/UMA/object/signalGenerator', data = data)

    def add_operator(self, operators):
        query = {'signal_generator_id': self._sg_id}
        data = {'operators': operators}
        self._service.put('/UMA/object/signalGenerator', data=data, query=query)

# Client class for SignalInput
class UMAClientSignalInput:
    def __init__(self, service, si_id):
        self._si_id = si_id
        self._service = service

    def add_signal_input(self, sg_id, generator_type, **kwargs):
        data = {'signal_input_id': self._si_id, 'signal_generator_id': sg_id, 'generator_type': generator_type}
        data.update(kwargs)

        self._service.post('/UMA/object/signalInput', data = data)

# client object for UMA Simulation
# NOT UPDATED FOR NOW
class UMAClientSimulation:
    def __init__(self, experiment_id, service):
        #self.logger = logging.getLogger("ClientSimulation")
        self._service = service
        self._experiment_id = experiment_id

    def get_experiment_id(self):
        return self._experiment_id

    def make_up(self, signal):
        data =  {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'signal': signal}
        result = self._service.post('/UMA/simulation/up', data)
        if not result:
            return None
        return list(result['data']['signal'])

    def make_abduction(self, signals):
        data =  {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'signals': signals}
        result = self._service.post('/UMA/simulation/abduction', data)
        if not result:
            return None
        return list(result['data']['abduction_even']), list(result['data']['abduction_odd'])

    def make_propagate_masks(self):
        data =  {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id}
        result = self._service.post('/UMA/simulation/propagateMasks', data)
        if not result:
            return None
        return list(result['data']['propagate_mask'])

    def make_ups(self, signals):
        data =  {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                 'agent_id': self._agent_id,
                 'snapshot_id': self._snapshot_id, 'signals': signals}
        result = self._service.post('/UMA/simulation/ups', data)
        if not result:
            return None
        return list(result['data']['signals'])

    def make_downs(self, signals):
        data =  {'experiment_id': self._experiment_id,'bua_id': self._bua_id,
                 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'signals': signals}
        result = self._service.post('/UMA/simulation/downs', data)
        if not result:
            return None
        return list(result['data']['signals'])

    def make_propagation(self, signals, load):
        data =  {'experimentId': self._experiment_id, 'bua_id': self._bua_id,
                 'agentId': self._agent_id, 'snapshotId': self._snapshot_id,
                 'signals': signals, 'load': load}
        result = self._service.post('/UMA/simulation/propagation', data)
        if not result:
            return None
        return list(result['data']['signals'])

    def make_blocks(self, dists, delta):
        data =  {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                 'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id,
                 'dists': dists, 'delta': delta}
        result = self._service.post('/UMA/simulation/blocks', data)
        if not result:
            return None
        return list(result['data']['blocks'])

    def make_npdirs(self):
        data = {'experiment_id': self._experiment_id, 'bua_id': self._bua_id,
                'agent_id': self._agent_id, 'snapshot_id': self._snapshot_id}
        result = self._service.post('/UMA/simulation/npdirs', data)
        if not result:
            return None
        return list(result['data']['npdirs'])