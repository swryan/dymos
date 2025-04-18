import unittest
import openmdao.api as om
import dymos as dm
from openmdao.utils.testing_utils import set_env_vars


class TestCheckPartials(unittest.TestCase):

    def brach_explicit_partials(self):
        from dymos.examples.brachistochrone import BrachistochroneODE
        prob = om.Problem()

        prob.driver = om.ScipyOptimizeDriver()

        tx = dm.ExplicitShooting(grid=dm.GaussLobattoGrid(num_segments=3, nodes_per_seg=6, compressed=False))

        phase = dm.Phase(ode_class=BrachistochroneODE, transcription=tx)

        phase.set_time_options(units='s', fix_initial=True,
                               duration_bounds=(1.0, 10.0))

        # automatically discover states
        phase.set_state_options('x', fix_initial=True)
        phase.set_state_options('y', fix_initial=True)
        phase.set_state_options('v', fix_initial=True)

        phase.add_parameter('g', val=1.0, units='m/s**2', opt=True, lower=1,
                            upper=9.80665)
        phase.add_control('theta', val=45.0, units='deg', opt=True, lower=1.0E-6,
                          upper=179.9,
                          ref=90., rate2_continuity=True)

        phase.add_boundary_constraint('x', loc='final', equals=10.0)
        phase.add_boundary_constraint('y', loc='final', equals=5.0)

        prob.model.add_subsystem('phase0', phase)

        phase.add_objective('time', loc='final')

        prob.setup(force_alloc_complex=True)

        prob.set_val('phase0.t_initial', 0.0)
        prob.set_val('phase0.t_duration', 2)
        prob.set_val('phase0.initial_states:x', 0.0)
        prob.set_val('phase0.initial_states:y', 10.0)
        prob.set_val('phase0.initial_states:v', 1.0E-6)
        prob.set_val('phase0.parameters:g', 1.0, units='m/s**2')
        prob.set_val('phase0.controls:theta', phase.interp('theta', ys=[0.01, 90]),
                     units='deg')

        prob.run_model()

        cpd = prob.check_partials(compact_print=True, method='fd', out_stream=None)
        return cpd

    def balanced_field_partials_radau(self):
        from dymos.examples.balanced_field.balanced_field_ode import BalancedFieldODEComp

        p = om.Problem()

        p.driver = om.ScipyOptimizeDriver()
        p.driver.declare_coloring()

        # First Phase: Brake release to V1 - both engines operable
        br_to_v1 = dm.Phase(ode_class=BalancedFieldODEComp, transcription=dm.Radau(num_segments=3),
                            ode_init_kwargs={'mode': 'runway'})
        br_to_v1.set_time_options(fix_initial=True, duration_bounds=(1, 1000), duration_ref=10.0)
        br_to_v1.add_state('r', fix_initial=True, lower=0, ref=1000.0, defect_ref=1000.0)
        br_to_v1.add_state('v', fix_initial=True, lower=0, ref=100.0, defect_ref=100.0)
        br_to_v1.add_parameter('alpha', val=0.0, opt=False, units='deg')
        br_to_v1.add_timeseries_output('*')

        # Second Phase: Rejected takeoff at V1 - no engines operable
        rto = dm.Phase(ode_class=BalancedFieldODEComp, transcription=dm.Radau(num_segments=3),
                       ode_init_kwargs={'mode': 'runway'})
        rto.set_time_options(fix_initial=False, duration_bounds=(1, 1000), duration_ref=1.0)
        rto.add_state('r', fix_initial=False, lower=0, ref=1000.0, defect_ref=1000.0)
        rto.add_state('v', fix_initial=False, lower=0, ref=100.0, defect_ref=100.0)
        rto.add_parameter('alpha', val=0.0, opt=False, units='deg')
        rto.add_timeseries_output('*')

        # Third Phase: V1 to Vr - single engine operable
        v1_to_vr = dm.Phase(ode_class=BalancedFieldODEComp, transcription=dm.Radau(num_segments=3),
                            ode_init_kwargs={'mode': 'runway'})
        v1_to_vr.set_time_options(fix_initial=False, duration_bounds=(1, 1000), duration_ref=1.0)
        v1_to_vr.add_state('r', fix_initial=False, lower=0, ref=1000.0, defect_ref=1000.0)
        v1_to_vr.add_state('v', fix_initial=False, lower=0, ref=100.0, defect_ref=100.0)
        v1_to_vr.add_parameter('alpha', val=0.0, opt=False, units='deg')
        v1_to_vr.add_timeseries_output('*')

        # Fourth Phase: Rotate - single engine operable
        rotate = dm.Phase(ode_class=BalancedFieldODEComp, transcription=dm.Radau(num_segments=3),
                          ode_init_kwargs={'mode': 'runway'})
        rotate.set_time_options(fix_initial=False, duration_bounds=(1.0, 5), duration_ref=1.0)
        rotate.add_state('r', fix_initial=False, lower=0, ref=1000.0, defect_ref=1000.0)
        rotate.add_state('v', fix_initial=False, lower=0, ref=100.0, defect_ref=100.0)
        rotate.add_control('alpha', order=1, opt=True, units='deg', lower=0, upper=10,
                           ref=10, val=[0, 10], control_type='polynomial')
        rotate.add_timeseries_output('*')

        # Fifth Phase: Climb to target speed and altitude at end of runway.
        climb = dm.Phase(ode_class=BalancedFieldODEComp, transcription=dm.Radau(num_segments=5),
                         ode_init_kwargs={'mode': 'climb'})
        climb.set_time_options(fix_initial=False, duration_bounds=(1, 100), duration_ref=1.0)
        climb.add_state('r', fix_initial=False, lower=0, ref=1000.0, defect_ref=1000.0)
        climb.add_state('h', fix_initial=True, lower=0, ref=1.0, defect_ref=1.0)
        climb.add_state('v', fix_initial=False, lower=0, ref=100.0, defect_ref=100.0)
        climb.add_state('gam', fix_initial=True, lower=0, ref=0.05, defect_ref=0.05)
        climb.add_control('alpha', opt=True, units='deg', lower=-10, upper=15, ref=10)
        climb.add_timeseries_output('*')

        # Instantiate the trajectory and add phases
        traj = dm.Trajectory()
        p.model.add_subsystem('traj', traj)
        traj.add_phase('br_to_v1', br_to_v1)
        traj.add_phase('rto', rto)
        traj.add_phase('v1_to_vr', v1_to_vr)
        traj.add_phase('rotate', rotate)
        traj.add_phase('climb', climb)

        # Add parameters common to multiple phases to the trajectory
        traj.add_parameter('m', val=174200., opt=False, units='lbm',
                           desc='aircraft mass',
                           targets={'br_to_v1': ['m'], 'v1_to_vr': ['m'], 'rto': ['m'],
                                    'rotate': ['m'], 'climb': ['m']})

        traj.add_parameter('T_nominal', val=27000 * 2, opt=False, units='lbf', static_target=True,
                           desc='nominal aircraft thrust',
                           targets={'br_to_v1': ['T']})

        traj.add_parameter('T_engine_out', val=27000, opt=False, units='lbf', static_target=True,
                           desc='thrust under a single engine',
                           targets={'v1_to_vr': ['T'], 'rotate': ['T'], 'climb': ['T']})

        traj.add_parameter('T_shutdown', val=0.0, opt=False, units='lbf', static_target=True,
                           desc='thrust when engines are shut down for rejected takeoff',
                           targets={'rto': ['T']})

        traj.add_parameter('mu_r_nominal', val=0.03, opt=False, units=None, static_target=True,
                           desc='nominal runway friction coefficient',
                           targets={'br_to_v1': ['mu_r'], 'v1_to_vr': ['mu_r'], 'rotate': ['mu_r']})

        traj.add_parameter('mu_r_braking', val=0.3, opt=False, units=None, static_target=True,
                           desc='runway friction coefficient under braking',
                           targets={'rto': ['mu_r']})

        traj.add_parameter('h_runway', val=0., opt=False, units='ft',
                           desc='runway altitude',
                           targets={'br_to_v1': ['h'], 'v1_to_vr': ['h'], 'rto': ['h'],
                                    'rotate': ['h']})

        traj.add_parameter('rho', val=1.225, opt=False, units='kg/m**3', static_target=True,
                           desc='atmospheric density',
                           targets={'br_to_v1': ['rho'], 'v1_to_vr': ['rho'], 'rto': ['rho'],
                                    'rotate': ['rho']})

        traj.add_parameter('S', val=124.7, opt=False, units='m**2', static_target=True,
                           desc='aerodynamic reference area',
                           targets={'br_to_v1': ['S'], 'v1_to_vr': ['S'], 'rto': ['S'],
                                    'rotate': ['S'], 'climb': ['S']})

        traj.add_parameter('CD0', val=0.03, opt=False, units=None, static_target=True,
                           desc='zero-lift drag coefficient',
                           targets={f'{phase}': ['CD0'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                      'rto', 'rotate', 'climb']})

        traj.add_parameter('AR', val=9.45, opt=False, units=None, static_target=True,
                           desc='wing aspect ratio',
                           targets={f'{phase}': ['AR'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                     'rto', 'rotate', 'climb']})

        traj.add_parameter('e', val=801, opt=False, units=None, static_target=True,
                           desc='Oswald span efficiency factor',
                           targets={f'{phase}': ['e'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                    'rto', 'rotate', 'climb']})

        traj.add_parameter('span', val=35.7, opt=False, units='m', static_target=True,
                           desc='wingspan',
                           targets={f'{phase}': ['span'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                       'rto', 'rotate', 'climb']})

        traj.add_parameter('h_w', val=1.0, opt=False, units='m', static_target=True,
                           desc='height of wing above CG',
                           targets={f'{phase}': ['h_w'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                      'rto', 'rotate', 'climb']})

        traj.add_parameter('CL0', val=0.5, opt=False, units=None, static_target=True,
                           desc='zero-alpha lift coefficient',
                           targets={f'{phase}': ['CL0'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                      'rto', 'rotate', 'climb']})

        traj.add_parameter('CL_max', val=2.0, opt=False, units=None, static_target=True,
                           desc='maximum lift coefficient for linear fit',
                           targets={f'{phase}': ['CL_max'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                         'rto', 'rotate', 'climb']})

        traj.add_parameter('alpha_max', val=10.0, opt=False, units='deg', static_target=True,
                           desc='angle of attack at maximum lift',
                           targets={f'{phase}': ['alpha_max'] for phase in ['br_to_v1', 'v1_to_vr',
                                                                            'rto', 'rotate', 'climb']})

        # Standard "end of first phase to beginning of second phase" linkages
        # Alpha changes from being a parameter in v1_to_vr to a polynomial control
        # in rotate, to a dynamic control in `climb`.
        traj.link_phases(['br_to_v1', 'v1_to_vr'], vars=['time', 'r', 'v'])
        traj.link_phases(['v1_to_vr', 'rotate'], vars=['time', 'r', 'v', 'alpha'])
        traj.link_phases(['rotate', 'climb'], vars=['time', 'r', 'v', 'alpha'])
        traj.link_phases(['br_to_v1', 'rto'], vars=['time', 'r', 'v'])

        # Less common "final value of r must be the match at ends of two phases".
        traj.add_linkage_constraint(phase_a='rto', var_a='r', loc_a='final',
                                    phase_b='climb', var_b='r', loc_b='final',
                                    ref=1000)

        # Define the constraints and objective for the optimal control problem
        v1_to_vr.add_boundary_constraint('v_over_v_stall', loc='final', lower=1.2, ref=100)

        rto.add_boundary_constraint('v', loc='final', equals=0., ref=100, linear=True)

        rotate.add_boundary_constraint('F_r', loc='final', equals=0, ref=100000)

        climb.add_boundary_constraint('h', loc='final', equals=35, ref=35, units='ft', linear=True)
        climb.add_boundary_constraint('gam', loc='final', equals=5, ref=5, units='deg', linear=True)
        climb.add_path_constraint('gam', lower=0, upper=5, ref=5, units='deg')
        climb.add_boundary_constraint('v_over_v_stall', loc='final', lower=1.25, ref=1.25)

        rto.add_objective('r', loc='final', ref=1000.0)

        #
        # Setup the problem and set the initial guess
        #
        p.setup(check=True)

        p.set_val('traj.br_to_v1.t_initial', 0)
        p.set_val('traj.br_to_v1.t_duration', 35)
        p.set_val('traj.br_to_v1.states:r', br_to_v1.interp('r', [0, 2500.0]))
        p.set_val('traj.br_to_v1.states:v', br_to_v1.interp('v', [0, 100.0]))
        p.set_val('traj.br_to_v1.parameters:alpha', 0, units='deg')

        p.set_val('traj.v1_to_vr.t_initial', 35)
        p.set_val('traj.v1_to_vr.t_duration', 35)
        p.set_val('traj.v1_to_vr.states:r', v1_to_vr.interp('r', [2500, 300.0]))
        p.set_val('traj.v1_to_vr.states:v', v1_to_vr.interp('v', [100, 110.0]))
        p.set_val('traj.v1_to_vr.parameters:alpha', 0.0, units='deg')

        p.set_val('traj.rto.t_initial', 35)
        p.set_val('traj.rto.t_duration', 35)
        p.set_val('traj.rto.states:r', rto.interp('r', [2500, 5000.0]))
        p.set_val('traj.rto.states:v', rto.interp('v', [110, 0]))
        p.set_val('traj.rto.parameters:alpha', 0.0, units='deg')

        p.set_val('traj.rotate.t_initial', 70)
        p.set_val('traj.rotate.t_duration', 5)
        p.set_val('traj.rotate.states:r', rotate.interp('r', [1750, 1800.0]))
        p.set_val('traj.rotate.states:v', rotate.interp('v', [80, 85.0]))
        p.set_val('traj.rotate.controls:alpha', 0.0, units='deg')

        p.set_val('traj.climb.t_initial', 75)
        p.set_val('traj.climb.t_duration', 15)
        p.set_val('traj.climb.states:r', climb.interp('r', [5000, 5500.0]), units='ft')
        p.set_val('traj.climb.states:v', climb.interp('v', [160, 170.0]), units='kn')
        p.set_val('traj.climb.states:h', climb.interp('h', [0, 35.0]), units='ft')
        p.set_val('traj.climb.states:gam', climb.interp('gam', [0, 5.0]), units='deg')
        p.set_val('traj.climb.controls:alpha', 5.0, units='deg')

        p.run_model()

        cpd = p.check_partials(compact_print=True, method='fd', out_stream=None)

        # Filter out those that include rhs_all in the path
        cpd = {path: data for path, data in cpd.items() if 'rhs_all' not in path}

        return cpd

    def min_time_climb_partials_gl(self):
        from dymos.examples.min_time_climb.min_time_climb_ode import MinTimeClimbODE

        p = om.Problem(model=om.Group())

        p.driver = om.ScipyOptimizeDriver()
        p.driver.declare_coloring()

        #
        # Instantiate the trajectory and phase
        #
        traj = dm.Trajectory()

        phase = dm.Phase(ode_class=MinTimeClimbODE,
                         transcription=dm.GaussLobatto(num_segments=15, compressed=False))

        traj.add_phase('phase0', phase)

        p.model.add_subsystem('traj', traj)

        #
        # Set the options on the optimization variables
        # Note the use of explicit state units here since much of the ODE uses imperial units
        # and we prefer to solve this problem using metric units.
        #
        phase.set_time_options(fix_initial=True, duration_bounds=(50, 400),
                               duration_ref=100.0)

        phase.add_state('r', fix_initial=True, lower=0, upper=1.0E6, units='m',
                        ref=1.0E3, defect_ref=1.0E3,
                        rate_source='flight_dynamics.r_dot')

        phase.add_state('h', fix_initial=True, lower=0, upper=20000.0, units='m',
                        ref=1.0E2, defect_ref=1.0E2,
                        rate_source='flight_dynamics.h_dot')

        phase.add_state('v', fix_initial=True, lower=10.0, units='m/s',
                        ref=1.0E2, defect_ref=1.0E2,
                        rate_source='flight_dynamics.v_dot')

        phase.add_state('gam', fix_initial=True, lower=-1.5, upper=1.5, units='rad',
                        ref=1.0, defect_ref=1.0,
                        rate_source='flight_dynamics.gam_dot')

        phase.add_state('m', fix_initial=True, lower=10.0, upper=1.0E5, units='kg',
                        ref=1.0E3, defect_ref=1.0E3,
                        rate_source='prop.m_dot')

        phase.add_control('alpha', units='deg', lower=-8.0, upper=8.0, scaler=1.0,
                          rate_continuity=True, rate_continuity_scaler=100.0,
                          rate2_continuity=False)

        phase.add_parameter('S', val=49.2386, units='m**2', opt=False, targets=['S'])
        phase.add_parameter('Isp', val=1600.0, units='s', opt=False, targets=['Isp'])
        phase.add_parameter('throttle', val=1.0, opt=False, targets=['throttle'])

        #
        # Setup the boundary and path constraints
        #
        phase.add_boundary_constraint('h', loc='final', equals=20000, scaler=1.0E-3)
        phase.add_boundary_constraint('aero.mach', loc='final', equals=1.0)
        phase.add_boundary_constraint('gam', loc='final', equals=0.0)

        phase.add_path_constraint(name='h', lower=100.0, upper=20000, ref=20000)
        phase.add_path_constraint(name='aero.mach', lower=0.1, upper=1.8)

        # Minimize time at the end of the phase
        phase.add_objective('time', loc='final', ref=1.0)

        p.model.linear_solver = om.DirectSolver()

        #
        # Setup the problem and set the initial guess
        #
        p.setup(check=True)

        p['traj.phase0.t_initial'] = 0.0
        p['traj.phase0.t_duration'] = 500

        p.set_val('traj.phase0.states:r', phase.interp('r', [0.0, 50000.0]))
        p.set_val('traj.phase0.states:h', phase.interp('h', [100.0, 20000.0]))
        p.set_val('traj.phase0.states:v', phase.interp('v', [135.964, 283.159]))
        p.set_val('traj.phase0.states:gam', phase.interp('gam', [0.0, 0.0]))
        p.set_val('traj.phase0.states:m', phase.interp('m', [19030.468, 10000.]))
        p.set_val('traj.phase0.controls:alpha', phase.interp('alpha', [0.0, 0.0]))

        p.run_model()

        cpd = p.check_partials(compact_print=True, method='fd', out_stream=None)

        # Filter out those that include rhs_all in the path
        cpd = {path: data for path, data in cpd.items() if 'rhs_disc' not in path and 'rhs_col' not in path}

        return cpd

    def test_check_partials_yes(self):
        """
        Run check_partials on a series of dymos problems and verify that partials information
        is displayed for core Dymos components when DYMOS_CHECK_PARTIALS == 'True'.
        """
        cp_save = dm.options['include_check_partials']
        dm.options['include_check_partials'] = True

        cases = [self.brach_explicit_partials,
                 self.balanced_field_partials_radau,
                 self.min_time_climb_partials_gl]

        partials = {}
        for c in cases:
            partials.update(c())

        dm.options['include_check_partials'] = cp_save

        assert len(partials.keys()) > 0

    @set_env_vars(CI='0')  # Make sure _no_check_partials isn't disabled
    def test_check_partials_no(self):
        """
        Run check_partials on a series of dymos problems and verify that partials information
        is not displayed for core Dymos components when DYMOS_CHECK_PARTIALS == 'False'.
        """
        cp_save = dm.options['include_check_partials']
        dm.options['include_check_partials'] = False

        cases = [self.brach_explicit_partials,
                 self.balanced_field_partials_radau,
                 self.min_time_climb_partials_gl]

        partials = {}
        for c in cases:
            partials.update(c())

        dm.options['include_check_partials'] = cp_save

        # Only `phase.ode` should show up in in the partials keys.
        self.assertSetEqual(set(partials.keys()), {'phase0.ode'})


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
