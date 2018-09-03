<scriptConfig name="LVRT_LV1" script="SA9_volt_ride_through">
  <params>
    <param name="vrt.n_r" type="int">1</param>
    <param name="eut.t_msa" type="float">1.0</param>
    <param name="gridsim.frea.phases" type="int">1</param>
    <param name="eut.v_msa" type="float">2.0</param>
    <param name="eut.vrt_t_dwell" type="int">5</param>
    <param name="vrt.t_hold" type="float">20.0</param>
    <param name="vrt.v_test" type="float">70.0</param>
    <param name="vrt.v_grid_max" type="float">100.0</param>
    <param name="vrt.v_grid_min" type="float">100.0</param>
    <param name="eut.v_nom" type="float">190.0</param>
    <param name="das_das_rms.wt3000e.sample_interval" type="int">1000</param>
    <param name="gridsim.frea.ip_port" type="int">2001</param>
    <param name="eut.p_rated" type="int">40000</param>
    <param name="das_das_rms.wt3000e.chan_1_label" type="string">1</param>
    <param name="das_das_rms.wt3000e.ip_addr" type="string">127.0.0.1</param>
    <param name="gridsim.frea.ip_addr" type="string">127.0.0.1</param>
    <param name="das_das_rms.wt3000e.chan_2_label" type="string">2</param>
    <param name="aist.script_version" type="string">2.0.0</param>
    <param name="aist.library_version" type="string">2.1.0</param>
    <param name="das_das_rms.wt3000e.chan_3_label" type="string">3</param>
    <param name="das_das_rms.wt3000e.chan_2" type="string">AC</param>
    <param name="das_das_rms.wt3000e.chan_3" type="string">AC</param>
    <param name="das_das_rms.wt3000e.chan_1" type="string">AC</param>
    <param name="das_das_rms.wt3000e.chan_4" type="string">DC</param>
    <param name="hil.mode" type="string">Disabled</param>
    <param name="loadsim.mode" type="string">Disabled</param>
    <param name="der.mode" type="string">Disabled</param>
    <param name="gridsim.auto_config" type="string">Enabled</param>
    <param name="vrt.p_20" type="string">Enabled</param>
    <param name="vrt.p_100" type="string">Enabled</param>
    <param name="gridsim.mode" type="string">FREA_Simulator</param>
    <param name="das_das_wf.mode" type="string">Manual</param>
    <param name="das_das_rms.mode" type="string">Manual</param>
    <param name="das_das_rms.wt3000e.comm" type="string">Network</param>
    <param name="das_das_rms.wt3000e.chan_4_label" type="string">None</param>
    <param name="eut.phases" type="string">Single Phase</param>
    <param name="gridsim.frea.comm" type="string">TCP/IP</param>
    <param name="vrt.test_label" type="string">lvrt_lv1</param>
  </params>
</scriptConfig>
