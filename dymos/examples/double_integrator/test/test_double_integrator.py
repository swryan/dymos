import os
import unittest

import openmdao.api as om
from openmdao.utils.assert_utils import assert_near_equal
from openmdao.utils.testing_utils import use_tempdirs, require_pyoptsparse

import dymos as dm
from dymos.examples.double_integrator.double_integrator_ode import DoubleIntegratorODE


@require_pyoptsparse(optimizer='IPOPT')
def double_integrator(transcription='gauss-lobatto', compressed=True, grid_type='lgl', optimizer='IPOPT'):

    p = om.Problem(model=om.Group())
    p.driver = om.pyOptSparseDriver(optimizer=optimizer)
    p.driver.declare_coloring()

    if optimizer == 'IPOPT':
        p.driver.opt_settings['max_iter'] = 500
        p.driver.opt_settings['alpha_for_y'] = 'safer-min-dual-infeas'
        p.driver.opt_settings['print_level'] = 0
        p.driver.opt_settings['nlp_scaling_method'] = 'gradient-based'
        p.driver.opt_settings['tol'] = 1.0E-7

    if transcription == 'gauss-lobatto':
        t = dm.GaussLobatto(num_segments=30, order=3, compressed=compressed)
    elif transcription == "radau-ps":
        t = dm.Radau(num_segments=30, order=3, compressed=compressed)
    elif transcription == 'birkhoff':
        t = dm.Birkhoff(num_nodes=100, grid_type=grid_type)
    else:
        raise ValueError('invalid transcription')

    traj = p.model.add_subsystem('traj', dm.Trajectory())

    phase = traj.add_phase('phase0', dm.Phase(ode_class=DoubleIntegratorODE, transcription=t))

    phase.set_time_options(fix_initial=True, fix_duration=True, units='s')

    phase.add_state('v', fix_initial=True, fix_final=True, rate_source='u', units='m/s')
    phase.add_state('x', fix_initial=True, rate_source='v', units='m', shape=(1, ))

    phase.add_control('u', units='m/s**2', scaler=1.0, continuity=False, rate_continuity=False,
                      rate2_continuity=False, shape=(1, ), lower=-1.0, upper=1.0)

    # Maximize distance travelled in one second.
    phase.add_objective('x', loc='final', scaler=-1)

    p.model.linear_solver = om.DirectSolver()

    p.setup(check=True)

    phase.set_time_val(initial=0.0, duration=1.0)
    phase.set_state_val('x', [0, 0.25])
    phase.set_state_val('v', [0, 0])
    phase.set_control_val('u', [1, -1])

    simulate_kwargs = {'times_per_seg': 100 if transcription == 'birkhoff' else 10}
    dm.run_problem(p, simulate=False, make_plots=True, simulate_kwargs=simulate_kwargs)

    return p


@use_tempdirs
class TestDoubleIntegratorExample(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        for filename in ['total_coloring.pkl', 'SLSQP.out', 'SNOPT_print.out']:
            if os.path.exists(filename):
                os.remove(filename)

    def _assert_results(self, p, traj=True, tol=1.0E-4):
        if traj:
            x = p.get_val('traj.phase0.timeseries.x')
            v = p.get_val('traj.phase0.timeseries.v')
        else:
            x = p.get_val('phase0.timeseries.x')
            v = p.get_val('phase0.timeseries.v')

        assert_near_equal(x[0], 0.0, tolerance=tol)
        assert_near_equal(x[-1], 0.25, tolerance=tol)

        assert_near_equal(v[0], 0.0, tolerance=tol)
        assert_near_equal(v[-1], 0.0, tolerance=tol)

    def test_ex_double_integrator_gl_compressed(self):
        p = double_integrator('gauss-lobatto',
                              compressed=True)

        self._assert_results(p)

    def test_ex_double_integrator_gl_uncompressed(self):
        p = double_integrator('gauss-lobatto',
                              compressed=False)

        self._assert_results(p)

    def test_ex_double_integrator_radau_compressed(self):
        p = double_integrator('radau-ps',
                              compressed=True)

        self._assert_results(p)

    def test_ex_double_integrator_radau_uncompressed(self):
        p = double_integrator('radau-ps',
                              compressed=False)

        self._assert_results(p)

    def test_ex_double_integrator_birkhoff_lgl(self):
        p = double_integrator('birkhoff',
                              grid_type='lgl')

        self._assert_results(p)

    def test_ex_double_integrator_birkhoff_cgl(self):
        p = double_integrator('birkhoff',
                              grid_type='cgl')

        self._assert_results(p)

    @require_pyoptsparse(optimizer='SLSQP')
    def test_ex_double_integrator_input_times_uncompressed(self):
        """
        Tests that externally connected t_initial and t_duration function as expected.
        """
        compressed = False
        p = om.Problem(model=om.Group())
        p.driver = om.pyOptSparseDriver(print_results=False)
        p.driver.declare_coloring()

        times_ivc = p.model.add_subsystem('times_ivc', om.IndepVarComp(),
                                          promotes_outputs=['t0', 'tp'])
        times_ivc.add_output(name='t0', val=0.0, units='s')
        times_ivc.add_output(name='tp', val=1.0, units='s')

        transcription = dm.Radau(num_segments=20, order=3, compressed=compressed)
        phase = dm.Phase(ode_class=DoubleIntegratorODE, transcription=transcription)
        p.model.add_subsystem('phase0', phase)

        p.model.connect('t0', 'phase0.t_initial')
        p.model.connect('tp', 'phase0.t_duration')

        phase.set_time_options(input_initial=True, input_duration=True, units='s')

        phase.add_state('v', fix_initial=True, fix_final=True, rate_source='u', units='m/s')
        phase.add_state('x', fix_initial=True, rate_source='v', units='m')

        phase.add_control('u', units='m/s**2', scaler=0.01, continuity=False, rate_continuity=False,
                          rate2_continuity=False, shape=(1,), lower=-1.0, upper=1.0)

        # Maximize distance travelled in one second.
        phase.add_objective('x', loc='final', scaler=-1)

        p.model.linear_solver = om.DirectSolver()

        p.setup(check=True)

        phase.set_time_val(0, 1)
        phase.set_state_val('x', [0, 0.25])
        phase.set_state_val('v', [0, 0])
        phase.set_control_val('u', [1, -1])

        p.run_driver()

        self._assert_results(p, traj=False)
        exp_out = phase.simulate()
        self._assert_results(exp_out, traj=False, tol=1.0E-2)

    @require_pyoptsparse(optimizer='SLSQP')
    def test_ex_double_integrator_input_times_compressed(self):
        """
        Tests that externally connected t_initial and t_duration function as expected.
        """
        compressed = True
        p = om.Problem(model=om.Group())
        p.driver = om.pyOptSparseDriver()
        p.driver.declare_coloring()

        times_ivc = p.model.add_subsystem('times_ivc', om.IndepVarComp(),
                                          promotes_outputs=['t0', 'tp'])
        times_ivc.add_output(name='t0', val=0.0, units='s')
        times_ivc.add_output(name='tp', val=1.0, units='s')

        transcription = dm.Radau(num_segments=20, order=3, compressed=compressed)
        phase = dm.Phase(ode_class=DoubleIntegratorODE, transcription=transcription)
        p.model.add_subsystem('phase0', phase)

        p.model.connect('t0', 'phase0.t_initial')
        p.model.connect('tp', 'phase0.t_duration')

        phase.set_time_options(input_initial=True, input_duration=True, units='s')

        phase.add_state('v', fix_initial=True, fix_final=True, rate_source='u', units='m/s')
        phase.add_state('x', fix_initial=True, rate_source='v', units='m')

        phase.add_control('u', units='m/s**2', scaler=0.01, continuity=False, rate_continuity=False,
                          rate2_continuity=False, shape=(1, ), lower=-1.0, upper=1.0)

        # Maximize distance travelled in one second.
        phase.add_objective('x', loc='final', scaler=-1)

        p.model.linear_solver = om.DirectSolver()

        p.setup(check=True)

        p['t0'] = 0.0
        p['tp'] = 1.0

        phase.set_state_val('x', [0, 0.25])
        phase.set_state_val('v', [0, 0])
        phase.set_control_val('u', [1, -1])

        p.run_driver()

        assert_near_equal(p.get_val('phase0.timeseries.x')[-1, ...],
                          [0.25],
                          tolerance=1.0E-8)


if __name__ == "__main__":

    unittest.main()
