import numpy as np
import openmdao.api as om

from ...grid_data import GridData
from ...._options import options as dymos_options


class GaussLobattoInterleaveComp(om.ExplicitComponent):
    r"""
    Class definition for the GaussLobattoInterleaveComp.

    Provides a contiguous output at all nodes for inputs which are only known at
    state discretiation or collocation nodes.

    Parameters
    ----------
    **kwargs : dict
        Dictionary of optional arguments.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._no_check_partials = not dymos_options['include_check_partials']

    def initialize(self):
        """
        Declare component options.
        """
        self._varnames = {}
        self.options.declare('grid_data', types=GridData, desc='Container object for grid info')

        # Sources is used internally to map the source of a connection to the timeseries to
        # the corresponding input variable.  This is used to ensure that we don't need to connect
        # the same source to this timeseries multiple times.
        self._sources = {'state_disc': {}, 'col': {}}

    def add_var(self, name, shape, units, disc_src, col_src):
        """
        Add a variable to be interleaved.

        In general these need to be variables whose values are stored separately for state
        discretization or collocation nodes (such as states or ODE outputs).

        Parameters
        ----------
        name : str
            The name of variable as it should appear in the outputs of the
            component ('interleave_comp.all_values:{name}').
        shape : tuple
            The shape of the variable at each instance in time.
        units : str
            The units of the variable.
        disc_src : str
            The source path of the variable's inputs at the discretization nodes.
        col_src : str
            The source path of the variable's inputs at the collocation nodes.

        Returns
        -------
        bool
            True if the variable was added to the interleave comp, False if not due to it already
            being there.
        """
        if name in self._varnames:
            return False

        num_disc_nodes = self.options['grid_data'].subset_num_nodes['state_disc']
        num_col_nodes = self.options['grid_data'].subset_num_nodes['col']
        num_nodes = self.options['grid_data'].subset_num_nodes['all']
        added_source = False

        size = np.prod(shape)

        self._varnames[name] = {}
        self._varnames[name]['state_disc'] = f'disc_values:{name}'
        self._varnames[name]['col'] = f'col_values:{name}'
        self._varnames[name]['all'] = f'all_values:{name}'

        # Check to see if the given disc source has already been used
        # We'll assume that the col source will be the same as well, no need to check both.
        if disc_src in self._sources['state_disc']:
            self._varnames[name]['state_disc'] = self._sources['state_disc'][disc_src]
            self._varnames[name]['col'] = self._sources['col'][col_src]
        else:
            self.add_input(
                name=self._varnames[name]['state_disc'],
                shape=(num_disc_nodes,) + shape,
                desc=f'Values of {name} at discretization nodes',
                units=units)
            self.add_input(
                name=self._varnames[name]['col'],
                shape=(num_col_nodes,) + shape,
                desc=f'Values of {name} at collocation nodes',
                units=units)
            self._sources['state_disc'][disc_src] = self._varnames[name]['state_disc']
            self._sources['col'][col_src] = self._varnames[name]['col']
            added_source = True

        self.add_output(
            name=self._varnames[name]['all'],
            shape=(num_nodes,) + shape,
            desc=f'Values of {name} at all nodes',
            units=units)

        start_rows = self.options['grid_data'].subset_node_indices['state_disc'] * size
        r = (start_rows[:, np.newaxis] + np.arange(size, dtype=int)).ravel()
        c = np.arange(size * num_disc_nodes, dtype=int)

        self.declare_partials(of=self._varnames[name]['all'],
                              wrt=self._varnames[name]['state_disc'],
                              rows=r, cols=c, val=1.0)

        start_rows = self.options['grid_data'].subset_node_indices['col'] * size
        r = (start_rows[:, np.newaxis] + np.arange(size, dtype=int)).ravel()
        c = np.arange(size * num_col_nodes, dtype=int)

        self.declare_partials(of=self._varnames[name]['all'],
                              wrt=self._varnames[name]['col'],
                              rows=r, cols=c, val=1.0)

        return added_source

    def compute(self, inputs, outputs):
        """
        Compute outputs for all nodes.

        Parameters
        ----------
        inputs : `Vector`
            `Vector` containing inputs.
        outputs : `Vector`
            `Vector` containing outputs.
        """
        disc_idxs = self.options['grid_data'].subset_node_indices['state_disc']
        col_idxs = self.options['grid_data'].subset_node_indices['col']

        for name, varnames in self._varnames.items():
            outputs[varnames['all']][disc_idxs] = inputs[varnames['state_disc']]
            outputs[varnames['all']][col_idxs] = inputs[varnames['col']]
