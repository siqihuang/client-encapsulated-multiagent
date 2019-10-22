from som3 import *
import random as rnd

X_BOUND = 10

# create experiment, agent
ex = Experiment('sniffy_test')
explorer = ex.create_agent('explorer')

ex.register_sensor('lt')
ex.register_sensor('rt')

ex.register('atT')
ex.register('dist')
ex.register('sig')

def action_RT(state):
    return state['rt'][0]

def action_LT(state):
    return state['lt'][0]

# create bua
lt = explorer.create_bua('lt', ex, 'sig', action_LT, 'qualitative')
rt = explorer.create_bua('rt', ex, 'sig', action_RT, 'qualitative')

# TODO find a way to explicitly get the envelope client by the name of an agnet
exp_envelope = Envelope('explorer_envelope')
ar_envelope = exp_envelope.create_child_envelope('ar_envelope')
ar = explorer.create_unscripted_bua('ar', envelope=ar_envelope, type='qualitative') # not a scripted bua
ar.construct_unscripted_sensor('id_F', 'id_F*')
ar.construct_unscripted_sensor('id_toF', 'id_toF*')
ar.init_unscripted_bua()

id_F = ar_envelope.create_signal_generator('ar_id_F', 'id_F', 'input')
id_toF = ar_envelope.create_signal_generator('ar_id_toF', 'id_toF', 'input')
id_phi_ar = ar_envelope.create_signal_generator('ar_phi', 'ar_phi', 'input')
# TODO check what the state_n=1 really mean, make sure it is the last statement
id_F.create_signal_input('ar_id_F_last_state_lt', generator_type='bua_state', bua_id='lt', state_n=1)
id_F.create_signal_input('ar_id_F_last_state_rt', generator_type='bua_state', bua_id='rt', state_n=1)
id_toF.create_signal_input('ar_id_toF_current_state_lt', generator_type='bua_state', bua_id='lt', state_n=0)
id_toF.create_signal_input('ar_id_toF_current_state_rt', generator_type='bua_state', bua_id='rt', state_n=0)
id_phi_ar.create_signal_input('ar_phi_last_state_lt', generator_type='bua_state', bua_id='lt', state_n=1)
id_phi_ar.create_signal_input('ar_phi_last_state_rt', generator_type='bua_state', bua_id='rt', state_n=1)
id_F.create_operators("&")
id_toF.create_operators("&")
id_phi_ar.create_operators("&")
ar.add_phi_generator('ar_phi')

id_ar_out_lt = ar_envelope.create_signal_generator('id_ar_out_lt', 'lt', 'output')
id_ar_out_rt = ar_envelope.create_signal_generator('id_ar_out_rt', 'rt', 'output')
# lt state override; coin flapping
id_ar_out_lt.create_signal_input('arb_current_state', generator_type='bua_state', bua_id='ar', state_n=0)
id_ar_out_lt.create_signal_input('arb_rnd', generator_type='random_bool')
id_ar_out_lt.create_signal_input('arb_lt_current_state', generator_type='bua_state', bua_id='lt', state_n=0)
id_ar_out_lt.create_signal_input('arb_current_state', generator_type='bua_state', bua_id='ar', state_n=0)
id_ar_out_lt.create_signal_input('arb_rnd', generator_type='random_bool')
id_ar_out_lt.create_signal_input('arb_lt_current_state', generator_type='bua_state', bua_id='lt', state_n=0)
id_ar_out_lt.create_signal_input('arb_current_state', generator_type='bua_state', bua_id='ar', state_n=0)
id_ar_out_lt.create_signal_input('arb_lt_current_state', generator_type='bua_state', bua_id='lt', state_n=0)
id_ar_out_lt.create_operators("(&&)|((!)&(!)&)|((!)&)")
# rt state override; coin flapping

id_ar_out_rt.create_signal_input('arb_current_state', generator_type='bua_state', bua_id='ar', state_n=0)
id_ar_out_rt.create_signal_input('arb_rnd', generator_type='random_bool')
id_ar_out_rt.create_signal_input('arb_rt_current_state', generator_type='bua_state', bua_id='rt', state_n=0)
id_ar_out_rt.create_signal_input('arb_current_state', generator_type='bua_state', bua_id='ar', state_n=0)
id_ar_out_rt.create_signal_input('arb_rnd', generator_type='random_bool')
id_ar_out_rt.create_signal_input('arb_rt_current_state', generator_type='bua_state', bua_id='rt', state_n=0)
id_ar_out_rt.create_signal_input('arb_current_state', generator_type='bua_state', bua_id='ar', state_n=0)
id_ar_out_rt.create_signal_input('arb_rt_current_state', generator_type='bua_state', bua_id='rt', state_n=0)
id_ar_out_rt.create_operators("(&&(!))|(&(!)&)|((!)&)")


def in_bounds(pos):
    return (pos >= 0 and pos <= X_BOUND)

def motion(state):
    triggers = {'rt': 1, 'lt': -1}
    diff = 0
    for t in triggers:
        diff += triggers[t] * int(state[t][0])
    newpos = state['pos'][0] + diff
    if in_bounds(newpos):
        return newpos
    else:
        return state['pos'][0]

ex.register('pos')
TARGET = 5
START = 5

ex.construct_measurable('pos', motion, init_value=deque([START, START], 2))

def xsensor(m):  # along x-axis
    return lambda state: state['pos'][0] < m + 1

for i in range(X_BOUND):
    tmp_name = 'x' + str(i)
    ex.register_sensor(tmp_name)

    ex.construct_sensor(tmp_name, xsensor(i), deque([xsensor(i)(ex._STATE), xsensor(i)(ex._STATE)], 2))
    lt.add_sensor(tmp_name)
    rt.add_sensor(tmp_name)

def dist(p, q):
    return abs(p - q)

def dist_to_target(state):
    print state['pos'][0], dist(state['pos'][0], TARGET)
    return dist(state['pos'][0], TARGET)

ex.construct_measurable('dist', dist_to_target, deque([dist(START, TARGET), dist(START, TARGET)], 2))

def sig(state):
    return 0 if state['dist'][0] == 0 else 1

ex.construct_measurable('sig', sig, deque([dist(START, TARGET), dist(START, TARGET)], 2))

lt.init()
rt.init()
ar.init()
ex.init()

ex.update_state()

for bua in [lt, rt]:
    delay_sigs = [[i == 2 * ind for i in xrange(2 * X_BOUND)] for ind in xrange(X_BOUND)]
    uuids = [['predelay' + str(i), 'c_delay' + str(i)] for i in range(X_BOUND)]
    bua.delay(delay_sigs, uuids)

delay_sigs = [[True, False, False, False], [False, False, True, False]]
uuids = [['predelay' + str(i), 'c_delay' + str(i)] for i in range(2)]
ar.delay(delay_sigs, uuids)


WARM_UP = 100
instruction_lt = [bool(rnd.randint(0, 1)) for i in range(WARM_UP)]
instruction_rt = [not v for v in instruction_lt]
lt.add_instruction(instruction_lt)
rt.add_instruction(instruction_rt)

for i in range(200):
    ex.update_state()

# TODO add a tree evaluator now