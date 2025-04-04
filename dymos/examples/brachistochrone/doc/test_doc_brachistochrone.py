import os
import unittest

try:
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use('Agg')
    plt.style.use('ggplot')
except ImportError:
    matplotlib = None

from openmdao.utils.testing_utils import use_tempdirs, require_pyoptsparse


@use_tempdirs
class TestBrachistochroneForDocs(unittest.TestCase):

    def tearDown(self):
        for filename in ['total_coloring.pkl', 'SLSQP.out', 'SNOPT_print.out', 'SNOPT_summary.out']:
            if os.path.exists(filename):
                os.remove(filename)

    def test_brachistochrone_partials(self):
        import numpy as np
        import openmdao.api as om
        from dymos.utils.testing_utils import assert_check_partials
        from dymos.examples.brachistochrone.doc.brachistochrone_ode import BrachistochroneODE

        num_nodes = 5

        p = om.Problem(model=om.Group())

        ivc = p.model.add_subsystem('vars', om.IndepVarComp())
        ivc.add_output('v', shape=(num_nodes,), units='m/s')
        ivc.add_output('theta', shape=(num_nodes,), units='deg')

        p.model.add_subsystem('ode', BrachistochroneODE(num_nodes=num_nodes))

        p.model.connect('vars.v', 'ode.v')
        p.model.connect('vars.theta', 'ode.theta')

        p.setup(force_alloc_complex=True)

        p.set_val('vars.v', 10*np.random.random(num_nodes))
        p.set_val('vars.theta', 10*np.random.uniform(1, 179, num_nodes))

        p.run_model()
        cpd = p.check_partials(method='cs', compact_print=True)
        assert_check_partials(cpd)

    @unittest.skipIf(matplotlib is None, "This test requires matplotlib")
    def test_brachistochrone_for_docs_gauss_lobatto(self):
        import openmdao.api as om
        from openmdao.utils.assert_utils import assert_near_equal
        import dymos as dm
        from dymos.examples.plotting import plot_results
        from dymos.examples.brachistochrone import BrachistochroneODE
        import matplotlib.pyplot as plt

        #
        # Initialize the Problem and the optimization driver
        #
        p = om.Problem(model=om.Group())
        p.driver = om.ScipyOptimizeDriver()
        p.driver.declare_coloring()

        #
        # Create a trajectory and add a phase to it
        #
        traj = p.model.add_subsystem('traj', dm.Trajectory())

        phase = traj.add_phase('phase0',
                               dm.Phase(ode_class=BrachistochroneODE,
                                        transcription=dm.GaussLobatto(num_segments=10)))

        #
        # Set the variables
        #
        phase.set_time_options(fix_initial=True, duration_bounds=(.5, 10))

        phase.add_state('x', fix_initial=True, fix_final=True)

        phase.add_state('y', fix_initial=True, fix_final=True)

        phase.add_state('v', fix_initial=True, fix_final=False)

        phase.add_control('theta', continuity=True, rate_continuity=True,
                          units='deg', lower=0.01, upper=179.9)

        phase.add_parameter('g', units='m/s**2', val=9.80665)
        #
        # Minimize time at the end of the phase
        #
        phase.add_objective('time', loc='final', scaler=10)

        p.model.linear_solver = om.DirectSolver()

        #
        # Setup the Problem
        #
        p.setup()

        #
        # Set the initial values
        #
        phase.set_time_val(initial=0.0, duration=2.0)

        phase.set_state_val('x', [0, 10])
        phase.set_state_val('y', [10, 5])
        phase.set_state_val('v', [0, 9.9])

        phase.set_control_val('theta', [5, 100.5])

        #
        # Solve for the optimal trajectory
        #
        dm.run_problem(p)

        # Test the results
        assert_near_equal(p.get_val('traj.phase0.timeseries.time')[-1], 1.8016, tolerance=1.0E-3)

        # Generate the explicitly simulated trajectory
        exp_out = traj.simulate()

        plot_results([('traj.phase0.timeseries.x', 'traj.phase0.timeseries.y',
                       'x (m)', 'y (m)'),
                      ('traj.phase0.timeseries.time', 'traj.phase0.timeseries.theta',
                       'time (s)', 'theta (deg)')],
                     title='Brachistochrone Solution\nHigh-Order Gauss-Lobatto Method',
                     p_sol=p, p_sim=exp_out)

        plt.show()

    @unittest.skipIf(matplotlib is None, "This test requires matplotlib")
    def test_brachistochrone_for_docs_radau(self):
        import openmdao.api as om
        from openmdao.utils.assert_utils import assert_near_equal
        import dymos as dm
        from dymos.examples.plotting import plot_results
        from dymos.examples.brachistochrone import BrachistochroneODE

        #
        # Initialize the Problem and the optimization driver
        #
        p = om.Problem(model=om.Group())
        p.driver = om.ScipyOptimizeDriver()
        p.driver.declare_coloring()

        #
        # Create a trajectory and add a phase to it
        #
        traj = p.model.add_subsystem('traj', dm.Trajectory())

        phase = traj.add_phase('phase0',
                               dm.Phase(ode_class=BrachistochroneODE,
                                        transcription=dm.Radau(num_segments=10)))

        #
        # Set the variables
        #
        phase.set_time_options(fix_initial=True, duration_bounds=(.5, 10))

        phase.add_state('x', fix_initial=True, fix_final=True)

        phase.add_state('y', fix_initial=True, fix_final=True)

        phase.add_state('v', fix_initial=True, fix_final=False)

        phase.add_control('theta', continuity=True, rate_continuity=True,
                          units='deg', lower=0.01, upper=179.9)

        phase.add_parameter('g', units='m/s**2', val=9.80665)

        #
        # Minimize time at the end of the phase
        #
        phase.add_objective('time', loc='final', scaler=10)

        p.model.linear_solver = om.DirectSolver()

        #
        # Setup the Problem
        #
        p.setup()

        #
        # Set the initial values
        #
        phase.set_time_val(initial=0.0, duration=2.0)

        phase.set_state_val('x', [0, 10])
        phase.set_state_val('y', [10, 5])
        phase.set_state_val('v', [0, 9.9])

        phase.set_control_val('theta', [5, 100.5])

        #
        # Solve for the optimal trajectory
        #
        dm.run_problem(p)

        # Test the results
        assert_near_equal(p.get_val('traj.phase0.timeseries.time')[-1], 1.8016,
                          tolerance=1.0E-3)

        # Generate the explicitly simulated trajectory
        exp_out = traj.simulate()

        plot_results([('traj.phase0.timeseries.x', 'traj.phase0.timeseries.y',
                       'x (m)', 'y (m)'),
                      ('traj.phase0.timeseries.time', 'traj.phase0.timeseries.theta',
                       'time (s)', 'theta (deg)')],
                     title='Brachistochrone Solution\nRadau Pseudospectral Method',
                     p_sol=p, p_sim=exp_out)

        plt.show()

    @require_pyoptsparse(optimizer='IPOPT')
    def test_brachistochrone_for_docs_coloring_demo(self):
        import openmdao.api as om
        from openmdao.utils.assert_utils import assert_near_equal
        import dymos as dm
        from dymos.examples.plotting import plot_results
        from dymos.examples.brachistochrone import BrachistochroneODE

        #
        # Initialize the Problem and the optimization driver
        #
        p = om.Problem(model=om.Group())
        p.driver = om.pyOptSparseDriver(optimizer='IPOPT')
        p.driver.declare_coloring(tol=1.0E-12)

        #
        # Create a trajectory and add a phase to it
        #
        traj = p.model.add_subsystem('traj', dm.Trajectory())

        #
        # In this case the phase has many segments to demonstrate the impact of coloring.
        #
        phase = traj.add_phase('phase0',
                               dm.Phase(ode_class=BrachistochroneODE,
                                        transcription=dm.Radau(num_segments=100)))

        #
        # Set the variables
        #
        phase.set_time_options(fix_initial=True, duration_bounds=(.5, 10))

        phase.add_state('x', fix_initial=True, fix_final=True)

        phase.add_state('y', fix_initial=True, fix_final=True)

        phase.add_state('v', fix_initial=True, fix_final=False)

        phase.add_control('theta', continuity=True, rate_continuity=True,
                          units='deg', lower=0.01, upper=179.9)

        phase.add_parameter('g', units='m/s**2', val=9.80665)

        #
        # Minimize time at the end of the phase
        #
        phase.add_objective('time', loc='final', scaler=10)

        p.model.linear_solver = om.DirectSolver()

        #
        # Setup the Problem
        #
        p.setup()

        #
        # Set the initial values
        #
        phase.set_time_val(initial=0.0, duration=2.0)

        phase.set_state_val('x', [0, 10])
        phase.set_state_val('y', [10, 5])
        phase.set_state_val('v', [0, 9.9])

        phase.set_control_val('theta', [5, 100.5])

        #
        # Solve for the optimal trajectory
        #
        dm.run_problem(p)

        # Test the results
        assert_near_equal(p.get_val('traj.phase0.timeseries.time')[-1], 1.8016,
                          tolerance=1.0E-3)

        # Generate the explicitly simulated trajectory
        exp_out = traj.simulate()

        plot_results([('traj.phase0.timeseries.x', 'traj.phase0.timeseries.y',
                       'x (m)', 'y (m)'),
                      ('traj.phase0.timeseries.time', 'traj.phase0.timeseries.theta',
                       'time (s)', 'theta (deg)')],
                     title='Brachistochrone Solution\nRadau Pseudospectral Method',
                     p_sol=p, p_sim=exp_out)

        plt.show()

    @require_pyoptsparse(optimizer='IPOPT')
    def test_brachistochrone_for_docs_coloring_demo_solve_segments(self):
        import openmdao.api as om
        from openmdao.utils.assert_utils import assert_near_equal
        import dymos as dm
        from dymos.examples.plotting import plot_results
        from dymos.examples.brachistochrone import BrachistochroneODE

        #
        # Initialize the Problem and the optimization driver
        #
        p = om.Problem(model=om.Group())
        p.driver = om.pyOptSparseDriver(optimizer='IPOPT')
        p.driver.opt_settings['print_level'] = 0
        # p.driver.declare_coloring()

        #
        # Create a trajectory and add a phase to it
        #
        traj = p.model.add_subsystem('traj', dm.Trajectory())

        #
        # In this case the phase has many segments to demonstrate the impact of coloring.
        #
        phase = traj.add_phase('phase0',
                               dm.Phase(ode_class=BrachistochroneODE,
                                        transcription=dm.Radau(num_segments=100,
                                                               solve_segments='forward')))

        #
        # Set the variables
        #
        phase.set_time_options(fix_initial=True, duration_bounds=(.5, 10))

        phase.add_state('x', fix_initial=True)

        phase.add_state('y', fix_initial=True)

        phase.add_state('v', fix_initial=True)

        phase.add_control('theta', continuity=True, rate_continuity=True,
                          units='deg', lower=0.01, upper=179.9)

        phase.add_parameter('g', units='m/s**2', val=9.80665)

        #
        # Replace state terminal bounds with nonlinear constraints
        #
        phase.add_boundary_constraint('x', loc='final', equals=10)
        phase.add_boundary_constraint('y', loc='final', equals=5)

        #
        # Minimize time at the end of the phase
        #
        phase.add_objective('time', loc='final', scaler=10)

        p.model.linear_solver = om.DirectSolver()

        #
        # Setup the Problem
        #
        p.setup()

        #
        # Set the initial values
        #
        phase.set_time_val(initial=0.0, duration=2.0)

        phase.set_state_val('x', [0, 10])
        phase.set_state_val('y', [10, 5])
        phase.set_state_val('v', [0, 9.9])

        phase.set_control_val('theta', [5, 100.5])

        #
        # Solve for the optimal trajectory
        #
        dm.run_problem(p)

        # Test the results
        assert_near_equal(p.get_val('traj.phase0.timeseries.time')[-1], 1.8016,
                          tolerance=1.0E-3)

        # Generate the explicitly simulated trajectory
        exp_out = traj.simulate()

        plot_results([('traj.phase0.timeseries.x', 'traj.phase0.timeseries.y',
                       'x (m)', 'y (m)'),
                      ('traj.phase0.timeseries.time', 'traj.phase0.timeseries.theta',
                       'time (s)', 'theta (deg)')],
                     title='Brachistochrone Solution\nRadau Pseudospectral Method',
                     p_sol=p, p_sim=exp_out)

        plt.show()


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
