# version 3 for UMA Multi-agent use case
import os
import time
import uuid
import numpy as np
from client.UMARest import *
from collections import deque

service = UMARestService()


def func_amper(experiment, mid_list):
    def f(state):
        return all([experiment._DEFS[mid](state) for mid in mid_list])

    return f


def func_not(func):
    def f(state):
        return not (func(state))

    return f


def func_delay(midlist):
    def f(state):
        return all([state[mid][1] for mid in midlist])

    return f


###
### Shortcuts to numpy Boolean Logic functions
###

def negate(x):
    return np.logical_not(x)


def conjunction(x, y):
    return np.logical_and(x, y)


def disjunction(x, y):
    return np.logical_or(x, y)


def symmetric(x, y):
    return np.logical_xor(x, y)


def alltrue(n):
    return np.array([True for x in xrange(n)])


def allfalse(n):
    return np.array([False for x in xrange(n)])

def name_comp(name):
    ### return the name of the complementary sensor
    return name + '*' if name[-1:] != '*' else name[:-1]

def name_invert(names):
    ### return the set of complemented names in the list/set names
    return set(name_comp(name) for name in names)


def name_delay(name):
    ### delay
    return '#' + str(name)


def name_ampersand(name_list):
    ### conjunction
    L = len(name_list)
    if L == 0:
        raise Exception('\nEmpty conjunction not allowed.\n')
    elif L == 1:
        return name_list[0]
    else:
        return '{' + ';'.join(name_list) + '}'


###
### DATA STRUCTURES
###

class Signal(object):
    def __init__(self, value):
        if len(value) % 2 == 0:
            self._VAL = np.array(value, dtype=bool)
        else:
            raise Exception('Objects of class Signal must have even length -- Aborting!\n')

    def __repr__(self):
        return str(self._VAL)

    def len(self):
        return len(self._VAL)

    def weight(self):
        return self._VAL.sum()

    # set the signal
    def set(self, ind, value):
        self._VAL[ind] = value

    # inspect the signal
    def out(self, ind=None):
        if ind is None:
            return self._VAL.tolist()
        else:
            return self._VAL[ind]

    # report the signal
    def value(self):
        return self._VAL

    # extend the signal
    def extend(self, value):
        self._VAL = np.concatenate((self._VAL, value))

    ### negating a partial signal
    def star(self):
        return Signal([(self._VAL[i + 1] if i % 2 == 0 else self._VAL[i - 1]) for i in xrange(len(self._VAL))])

    ### full complement of a signal
    def negate(self):
        return Signal(negate(self._VAL))

    ### subtracting Signal "other" from Signal "self"
    def subtract(self, other):
        return Signal(conjunction(self._VAL, negate(other._VAL)))

    def add(self, other):
        return Signal(disjunction(self._VAL, other._VAL))

    def intersect(self, other):
        return Signal(conjunction(self._VAL, other._VAL))

    def contained_in(self, other):
        return self.subtract(other).weight() == 0

# the experiment class
class Experiment(object):
    def __init__(self, experiment_id,):
        self._experiment_id = experiment_id
        self._service = UMAClientWorld(service).add_experiment(experiment_id)

        self._agents = {}
        self._ID = set()
        self._SENSORS = []
        self._MID = []
        self._STATE = {}
        self._DEFS = {}
        self._COUNT = 0

    def init(self):
        service.post(uri='/UMA/object/experiment/register',
                     data={'experiment_id': self._experiment_id, 'mids': self._SENSORS})

        for agent_id in self._agents:
            envelope = self._agents[agent_id]._envelope
            for signal in envelope._signals:
                sg = envelope.create_signal_generator("%s-%s" % (agent_id, signal), signal, 'input')
                sg.create_signal_input("%s-%s" % (agent_id, signal), "experiment_sensor",
                                       **{'experiment_id': self._experiment_id, 'sensor_id': signal})
                # init the operator to be null
                sg.create_operators("")

    def create_agent(self, agent_id):
        if agent_id in self._agents:
            raise Exception("agent_id=%s already exist" % agent_id)

        agent_service = self._service.add_agent(agent_id)
        self._agents[agent_id] = Agent(agent_id, agent_service)

        return self._agents[agent_id]

    def registed(self, s):
        return s in self._ID

    def register_sensor(self, id_string=None):
        """
            :param id: the id to be registered as sensor
            :return: the id and cid of the sensor
            """
        # generate the mid first
        mid = self.register(id_string)
        if id_string is None:
            # if the id_string is None, the midc will generate from the #new_id
            midc = self.register(name_comp(mid))
        else:
            # else the midc will generate from id_string*
            midc = self.register(name_comp(id_string))
        return mid, midc

    def register(self, id_string=None):
        """
            :param id: the id to be registered, if it is None, will generate an uuid
            :return: the id
        """
        if id_string is None:  # means the sensor is a new one, uuid will be generated
            new_id = str(uuid.uuid4())
            self._ID.add(new_id)
            return new_id
        elif id_string in self._ID:
            raise Exception('ID $' + str(id_string) + '$ already registered -- Aborting.')
        else:  # need to add the id. if same name provided, just override
            self._ID.add(id_string)
            return id_string

    def update_state(self):
        new_state = self.decide()

        # update the state info based on UMACore update
        for agent_id in new_state:
            agent_info = new_state[agent_id]
            for bua_id in agent_info:
                bua_state = agent_info[bua_id]
                self.set_state(bua_id, bua_state)
        for mid in self._MID:
            self.set_state(mid, self._DEFS[mid](self._STATE))

        self._COUNT += 1

    ## Set new state value
    def set_state(self, mid, value):
        self._STATE[mid].appendleft(value)
        return None

    def construct_measurable(self, mid, definition=None, init_value=None, depth=1):
        """
            :param mid:  the input id, if it is none, id will be generated
            :param definition: the definition function of the measurable
            :param init_value: the init value for the measurable
            :param depth: the depth of the measurable
            :return: nothing
            """
        # check mid first
        #        construction requires prior registration
        if mid not in self._ID:
            raise Exception("the mid " + mid + " is not registered!")

        # add the mid into the MID list, ID_TO_DEP, and DEFS
        self._MID.append(mid)
        self._DEFS[mid] = definition
        if init_value is None:  # will try to generate the init_value based on the definition
            self._STATE[mid] = deque([], depth + 1)
            # -------------------- Remove the old try/except block, because: -----------------------
            # 1 if definition is None, getting this by throwing an exception will reduce performance, an if else check will be faster
            # 2 if definition is not None, and there is an error generating values, then the exception will not be caught because those error are unexpected
            if definition is not None:  # if definition exist, calculate the init value, any error will throw to outer scope
                self.set_state(mid, definition(self._STATE))
        else:
            self._STATE[mid] = deque(init_value, depth + 1)
        return None

    # construct the agent using id
    def construct_sensor(self, mid, definition=None, init_value=None, depth=1):
        """
            :param mid:  the input id, if it is none, id will be generated
            :param definition: the definition function of the measurable
            :param init_value: the init value for the measurable
            :param depth: the depth of the measurable
            :return: nothing
        """
        midc = name_comp(mid)
        # check mid/midc first
        if mid not in self._ID or midc not in self._ID:
            raise Exception("the mid $" + mid + "$ is not registered!")

        # compute initial value of sensor
        if definition is None:  # this is an action sensor, init value WILL be defaulted to False...
            self.construct_measurable(mid, None, [False for ind in xrange(depth + 1)], depth)
            self.construct_measurable(midc, None, [True for ind in xrange(depth + 1)], depth)
        else:
            self.construct_measurable(mid, definition, init_value, depth)
            self.construct_measurable(midc,
                                      func_not(definition),
                                      negate(init_value) if init_value is not None else None,
                                      depth)

        self._SENSORS.extend([mid, midc])
        return None

    def this_state(self, mid, delta=0):
        try:
            return self._STATE[mid][delta]
        except:
            pass

    # decide call launched from experiment
    def decide(self):
        signals = Signal([self.this_state(sensor) for sensor in self._SENSORS])._VAL.tolist()

        state = {}
        for agent_id in self._agents:
            agent = self._agents[agent_id]
            tmp = {}
            for bua_id in agent._buas:
                bua = agent._buas[bua_id]
                if not bua._is_scripted:
                    continue
                phi = self.this_state(bua._id_motivation)
                name = bua_id if bua._active else '*' + bua_id
                tmp[name] = phi
            state[agent_id] = tmp
        #print state
        new_state = self._service.make_decision(signals, state)['state']
        #print new_state
        return new_state

class Agent(object):
    def __init__(self, agent_id, service):
        self._agent_id = agent_id
        self._service = service
        # TODO this name convention has c++ code dependency, we need a better way to handle it
        self._envelope = Envelope("%s_envelope" % agent_id)
        self._buas = {}

    def create_bua(self, bua_id, ex, id_motivation, definition, type):
        bua_idc = name_comp(bua_id)
        if not ex.registed(bua_id) or not ex.registed(bua_idc):
            raise Exception("bua_id=%s or its compi is not registered" %bua_id)

        ex.construct_sensor(bua_id, definition, init_value=[False, False])

        bua_service = self._service.add_bua(bua_id, type)
        self._buas[bua_id] = Bua(bua_id, id_motivation, bua_service, self._envelope)

        return self._buas[bua_id]

    def create_unscripted_bua(self, bua_id, envelope, type):
        bua_service = self._service.add_bua(bua_id, type, envelope_id=envelope._envelope_id)
        self._buas[bua_id] = Bua(bua_id, None, bua_service, envelope, is_scripted=False)

        return self._buas[bua_id]

class Bua(object):
    def __init__(self, bua_id, id_motivation, service, envelope, is_scripted=True):
        self._bua_id = bua_id
        self._service = service
        self._id_motivation = id_motivation
        self._snapshots = {}
        self._active = False
        self._envelope = envelope
        self._is_scripted = is_scripted

        self._snapshots['plus'] = self.create_snapshot('plus')
        self._snapshots['minus'] = self.create_snapshot('minus')

    def create_snapshot(self, snapshot_id):
        snapshot_service = self._service.add_snapshot(snapshot_id)
        self._snapshots[snapshot_id] = Snapshot(snapshot_id, snapshot_service)
        return self._snapshots[snapshot_id]

    def add_sensor(self, sid):
        for snapshot_id in self._snapshots:
            self._snapshots[snapshot_id].add_sensor(sid)

        self._envelope.add_signal(sid)

    def add_instruction(self, instruction):
        self._service.add_instruction(instruction)

    def add_phi_generator(self, phi_generator_id):
        self._service.add_phi_generator(phi_generator_id)

    def init(self):
        for snapshot_id in self._snapshots:
            self._snapshots[snapshot_id].init()

    def construct_unscripted_sensor(self, sid, c_sid):
        for snapshot_id in self._snapshots:
            self._snapshots[snapshot_id].create_unscripted_sensor(sid, c_sid)

    def init_unscripted_bua(self):
        for snapshot_id in self._snapshots:
            self._snapshots[snapshot_id].init_unscripted_snapshot()

    def delay(self, delay_list, uuid_list):
        for snapshot_id in self._snapshots:
            snapshot = self._snapshots[snapshot_id]
            snapshot.delay(delay_list, uuid_list)

class Snapshot(object):
    def __init__(self, snapshot_id, service):
        self._snapshot_id = snapshot_id
        self._service = service
        self._sensor_size = 0
        self._sensors = []

    def add_sensor(self, sid):
        c_sid = name_comp(sid)
        if sid not in self._sensors and c_sid not in self._sensors:
            self._sensors.extend([sid, c_sid])
            self._sensor_size += 2

    def init(self, auto_target=True):
        self._service.set_auto_target(auto_target)

        for i in xrange(self._sensor_size / 2):
            self._service.add_sensor(self._sensors[2 * i], self._sensors[2 * i + 1])
        self._service.init()

    def create_unscripted_sensor(self, sid, c_sid):
        self._service.add_sensor(sid, c_sid)

    def init_unscripted_snapshot(self):
        self._service.init()

    def delay(self, delay_list, uuid_list):
        self._service.delay(delay_list, uuid_list)

class Sensor(object):
    def __init__(self):
        pass

class Envelope(object):
    def __init__(self, envelope_id):
        self._envelope_id = envelope_id
        self._service = UMAClientEnvelope(service, self._envelope_id)
        self._envelopes = {}
        self._processors = {'input': {}, 'output': {}}
        self._signals = set()

    def add_signal(self, signal):
        if signal in self._signals:
            return
        self._signals.add(signal)

    # add an envelope inside the current one
    def create_envelope(self, **kwargs):
        self._service.add_envelope(**kwargs)

    def create_child_envelope(self, envelope_id):
        envelope = Envelope(envelope_id)
        envelope.create_envelope(parent_envelope_ids=[self._envelope_id])
        self._envelopes[envelope_id] = envelope
        return envelope

    def create_signal_generator(self, sg_id, sg_name, processor_type):
        sg = SignalGenerator(sg_id)
        sg.create_signal_generator(self._envelope_id, sg_name, processor_type)

        self._processors[processor_type][sg_id] = sg

        return sg

class SignalGenerator(object):
    def __init__(self, sg_id):
        self._sg_id = sg_id
        self._service = UMAClientSignalGenerator(service, sg_id)
        self._signal_inputs = []

    def create_signal_generator(self, envelope_id, sg_name, processor_type):
        self._service.add_signal_generator(envelope_id, sg_name, processor_type)

    def create_signal_input(self, si_id, generator_type, **kwargs):
        si = SignalInput(si_id)
        si.create_signal_input(self._sg_id, generator_type, **kwargs)
        self._signal_inputs.append(si)

        return si

    # TODO maybe this should not be a separate call?
    def create_operators(self, operators):
        self._service.add_operator(operators)

class SignalInput(object):
    def __init__(self, si_id):
        self._si_id = si_id
        self._service = UMAClientSignalInput(service, si_id)

    def create_signal_input(self, sg_id, generator_type, **kwargs):
        self._service.add_signal_input(sg_id, generator_type, **kwargs)