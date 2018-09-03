"""
Copyright (c) 2017, Sandia National Labs and SunSpec Alliance
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Sandia National Labs and SunSpec Alliance nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Questions can be directed to support@sunspec.org
"""

import sys
import os
import traceback
# needed if running script stand alone
lib_path = os.path.join(os.path.dirname(__file__), '..', 'Lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)
print sys.path
from svpelab import gridsim
from svpelab import pvsim
from svpelab import das
from svpelab import der
from svpelab import hil
import sunspec.core.client as client
import script
import openpyxl
import numpy as np

# DAS soft channels
das_points = {'sc': ('P_target_pct', 'P_min_pct', 'P_max_pct', 'eval_flag', 'freq_set')}

def p_target(f_step, f_nom, hz_start, hz_stop):
    f_step_pct = 100.*(f_step/f_nom)
    hz_start_pct = 100.*(hz_start/f_nom)
    hz_stop_pct = 100.*(hz_stop/f_nom)
    if f_step_pct < hz_start_pct:
        p_targ = 100.
    elif f_step_pct > hz_stop_pct:
        p_targ = 0.
    else:
        p_targ = 100. - 100.*((f_step_pct-hz_start_pct)/(hz_stop_pct-hz_start_pct))
    return p_targ

def test_run():

    result = script.RESULT_FAIL
    daq = None
    data = None
    trigger = None
    grid = None
    pv = None
    eut = None
    chil = None
    rs = None

    try:
        # initialize hardware-in-the-loop environment (if applicable)
        ts.log('Configuring HIL system...')
        chil = hil.hil_init(ts)
        if chil is not None:
            chil.config()

        # initialize grid simulator
        grid = gridsim.gridsim_init(ts)

        # initialize pv simulator
        pv = pvsim.pvsim_init(ts)
        p_rated = ts.param_value('fw.p_rated')
        pv.power_set(p_rated)
        pv.power_on()  # power on at p_rated

        # initialize data acquisition system
        daq = das.das_init(ts, sc_points=das_points['sc'])
        daq.sc['P_target_pct'] = 100
        daq.sc['P_min_pct'] = 100
        daq.sc['P_max_pct'] = 100
        daq.sc['eval_flag'] = 0

        # Configure the EUT communications
        eut = der.der_init(ts)
        eut.config()
        ts.log_debug(eut.measurements())
        ts.log_debug('Set L/HFRT and trip parameters to the widest range of adjustability possible.')

        fw_mode = ts.param_value('fw.fw_mode')
        f_nom = ts.param_value('fw.f_nom')
        f_min = ts.param_value('fw.f_min')
        f_max = ts.param_value('fw.f_max')
        MSAHz = ts.param_value('fw.MSAHz')
        MSAP = ts.param_value('fw.MSAP')
        t_settling = ts.param_value('fw.ts')
        fstart_min = ts.param_value('fw.fstart_min')
        fstart_max = ts.param_value('fw.fstart_max')
        k_pf_min = ts.param_value('fw.k_pf_min')
        k_pf_max = ts.param_value('fw.k_pf_max')
        k_pf = ts.param_value('fw.kpf')  # %Prated/Hz

        n_points = ts.param_value('test.n_points')
        irr = ts.param_value('test.irr')
        n_iterations = ts.param_value('test.n_iter')
        curves = ts.param_value('test.curves')

        if curves == 'Both':
            fw_curves = [1, 2]
        elif curves == 'Charactistic Curve 1':
            fw_curves = [1]
        else:  # Charactistic Curve 2
            fw_curves = [2]

        if irr == 'All':
            pv_powers = [1., 0.66, 0.33]
        elif irr == '100%':
            pv_powers = [1.]
        elif irr == '66%':
            pv_powers = [0.66]
        else:   #Charactistic Curve 2
            pv_powers = [0.33]

        # open result summary file
        result_summary_filename = 'result_summary.csv'
        result_summary = open(ts.result_file_path(result_summary_filename), 'a+')
        ts.result_file(result_summary_filename)
        result_summary.write('Result, Test Name, Power Level, Iteration, direction, '
                             'Freq, Power, P_min, P_max,  Dataset File\n')

        for fw_curve in fw_curves:
            if fw_curve == 1:  # characteristic curve 1
                hz_stop = fstart_max + 100./k_pf_max
                hz_start = fstart_min
            else:  # characteristic curve 2
                hz_stop = fstart_min + 100./k_pf_min
                hz_start = fstart_max

            if fw_mode == 'Parameters':
                eut.freq_watt_param(params={'HysEna': False, 'HzStr': hz_start,
                                            'HzStop': hz_stop, 'WGra': k_pf_min})
            else:  # pointwise
                eut.freq_watt(params={'ActCrv': 1})
                parameters = {'hz': [fstart_min, fstart_min, hz_stop, hz_stop], 'w': [100, 100, 0, 0]}
                ts.log_debug(parameters)
                eut.freq_watt_curve(id=1, params=parameters)
                eut.freq_watt(params={'Ena': True})
                ts.log_debug(eut.freq_watt())

            # start and stop frequencies for the grid simulator steps
            f_start = fstart_min
            f_end = f_max - MSAHz

            for power in pv_powers:
                pv.power_set(p_rated*power)
                for n_iter in range(n_iterations):
                    # SA14.3.2(d) and (e)
                    daq.data_capture(True)
                    f_steps = list(np.linspace(f_start, f_end, n_points)) + \
                              list(np.linspace(f_end, f_start, n_points)) + [49.0]

                    filename = 'FW_curve_%s_power=%0.2f_iter=%s.csv' % (fw_curve, power, n_iter+1)
                    step_count = 0
                    for f_step in f_steps:
                        step_count += 1
                        grid.freq(f_step)
                        daq.sc['freq_set'] = f_step
                        ts.log('        Recording power at frequency %0.3f Hz for 2*t_settling = %0.1f sec.' %
                               (f_step, 2*t_settling))
                        p_targ = p_target(f_step, f_nom, hz_start, hz_stop)
                        daq.sc['P_target_pct'] = p_targ
                        daq.sc['P_min_pct'] = p_targ - (MSAP/p_rated)*100.
                        daq.sc['P_max_pct'] = p_targ + (MSAP/p_rated)*100.
                        ts.sleep(t_settling)
                        daq.sc['eval_flag'] = 1  # flag the time in which the power will be analyzed, see Figure SA14.3
                        daq.data_capture()
                        ts.sleep(t_settling*1.5)  # This time period will be analyzed for pass/fail criteria
                        data = daq.data_capture_read()
                        ts.log_debug('Powers targ, min, max: %s, %s, %s' %
                                     (p_targ, daq.sc['P_min_pct'], daq.sc['P_max_pct'] ))
                        ts.log_debug('Powers are: %s, %s, %s' %
                                     (data.get('AC_P_1'), data.get('AC_P_2'), data.get('AC_P_3')))
                        AC_W = data.get('AC_P_1') + data.get('AC_P_2') + data.get('AC_P_3')
                        AC_W_pct = (AC_W/p_rated)*100.
                        if daq.sc['P_min_pct'] <= AC_W_pct <= daq.sc['P_max_pct']:
                            passfail = 'Pass'
                        else:
                            passfail = 'Fail'
                        if step_count <= n_points:
                            direction = 'up'
                        else:
                            direction = 'down'
                        result_summary.write('%s, %s, %s, %s, %s, %s, %s, %s, %s, %s \n' %
                                             (passfail, ts.config_name(), power*100., n_iter+1, direction,
                                              f_step, AC_W_pct, daq.sc['P_min_pct'], daq.sc['P_max_pct'],
                                              filename))
                        daq.sc['eval_flag'] = 0
                        daq.data_capture()

                    daq.data_capture(False)
                    ds = daq.data_capture_dataset()
                    ts.log('Saving file: %s' % filename)
                    ds.to_csv(ts.result_file_path(filename))
                    ts.result_file(filename)

        result = script.RESULT_COMPLETE

    except script.ScriptFail, e:
        reason = str(e)
        if reason:
            ts.log_error(reason)
    finally:
        if daq is not None:
            daq.close()
        if pv is not None:
            pv.close()
        if grid is not None:
            grid.close()
        if rs is not None:
            rs.close()
        if chil is not None:
            chil.close()

    return result

def run(test_script):

    try:
        global ts
        ts = test_script
        rc = 0
        result = script.RESULT_COMPLETE

        ts.log_debug('')
        ts.log_debug('**************  Starting %s  **************' % (ts.config_name()))
        ts.log_debug('Script: %s %s' % (ts.name, ts.info.version))
        ts.log_active_params()

        result = test_run()

        ts.result(result)
        if result == script.RESULT_FAIL:
            rc = 1

    except Exception, e:
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        rc = 1

    sys.exit(rc)

info = script.ScriptInfo(name=os.path.basename(__file__), run=run, version='1.0.0')

der.params(info)
# EUT FW parameters
info.param_group('fw', label='FW Configuration')
info.param('fw.fw_mode', label='Freq-Watt Mode', default='Parameters',
           values=['Parameters', 'Pointwise'],
           desc='Parameterized FW curve or pointwise linear FW curve?')
info.param('fw.p_rated', label='Output Power Rating (W)', default=34500.)
info.param('fw.f_nom', label='Nominal AC frequency (Hz)', default=50.)
info.param('fw.f_min', label='Min AC frequency (Hz)', default=49.)
info.param('fw.f_max', label='Max AC frequency (Hz)', default=52.)
info.param('fw.MSAHz', label='Manufacturer\'s stated AC frequency accuracy (Hz)', default=0.1)
info.param('fw.MSAP', label='Manufacturer\'s stated power accuracy (W)', default=10.)
info.param('fw.ts', label='Settling time (s)', default=1.)
info.param('fw.fstart_min', label='Min start of frequency droop (Hz)', default=50.1)
info.param('fw.fstart_max', label='Max start of frequency droop (Hz)', default=51.)
info.param('fw.k_pf_min', label='Min slope of frequency droop (%Prated/Hz)', default=0.1)
info.param('fw.k_pf_max', label='Max slope of frequency droop (%Prated/Hz)', default=1.0)
info.param('fw.k_pf', label='Slope of frequency droop (%Prated/Hz)', default=0.4)

info.param_group('test', label='Test Parameters')
info.param('test.curves', label='Curves to Evaluate', default='Both',
           values=['Charactistic Curve 1', 'Charactistic Curve 2', 'Both'])
info.param('test.irr', label='Power Levels', default='All',
           values=['100%', '66%', '33%', 'All'])
info.param('test.n_iter', label='Number of iteration for each test', default=3)
info.param('test.n_points', label='Number of points tested above f_start', default=3)

gridsim.params(info)
pvsim.params(info)
das.params(info)
hil.params(info)

# info.logo('sunspec.gif')

def script_info():
    
    return info


if __name__ == "__main__":

    # stand alone invocation
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    params = None

    test_script = script.Script(info=script_info(), config_file=config_file, params=params)
    test_script.log('log it')

    run(test_script)


