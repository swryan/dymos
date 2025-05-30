import functools
import numpy as np

from scipy.linalg import block_diag
import scipy.sparse as sp

from dymos.utils.lgl import lgl
from dymos.utils.lgr import lgr
from dymos.utils.cgl import cgl
from dymos.utils.hermite import hermite_matrices
from dymos.utils.lagrange import lagrange_matrices


def gauss_lobatto_subsets_and_nodes(n, seg_idx, compressed=False):
    """
    Provides node information and the location of the nodes for n Legendre-Gauss-Lobatto nodes on the range [-1, 1].

    Parameters
    ----------
    n : int
        The total number of nodes in the Gauss-Lobatto segment.  Must be
        an odd number.
    seg_idx : int
        The index of this segment within its phase.
    compressed : bool
        True if the subset requested is for a phase with compressed transcription.

    Returns
    -------
    dict
        A dictionary with the following keys:
        'state_disc' Gives the indices of the state discretization nodes
        'state_input' Gives the indices of the state input nodes
        'control_disc' Gives the indices of the control discretization nodes
        'control_input' Gives the indices of the control input nodes
        'segment_ends' Gives the indices of the nodes at the start (even) and end (odd) of a segment
        'col' Gives the indices of the collocation nodes.
        'all' Gives all node indices.
    np.array
        The location of all nodes on [-1, 1].
    np.array
        The weights of all nodes on [-1, 1].

    Notes
    -----
    Subset 'state_input' is the same as subset 'state_disc' if `compressed == False` or
    `first_seg == True`.  The same is true of subsets 'control_input' and 'control_disc'.
    """
    if n < 2:
        raise ValueError('The number of nodes must be larger than 1.')

    subsets = {
        'state_disc': np.arange(0, n, 2, dtype=int),
        'state_input': np.arange(0, n, 2, dtype=int) if not compressed or seg_idx == 0
        else np.arange(2, n, 2, dtype=int),
        'control_disc': np.arange(n, dtype=int),
        'control_input': np.arange(n, dtype=int) if not compressed or seg_idx == 0
        else np.arange(1, n, dtype=int),
        'segment_ends': np.array([0, n-1], dtype=int),
        'col': np.arange(1, n, 2, dtype=int),
        'all': np.arange(n, dtype=int),
        'solution': np.arange(n, dtype=int),
    }

    return subsets, *lgl(n)


def chebyshev_gauss_lobatto_subsets_and_nodes(n, seg_idx, compressed=False):
    """
    Provides node information and the location of the nodes for n Legendre-Gauss-Lobatto nodes on the range [-1, 1].

    Parameters
    ----------
    n : int
        The total number of nodes in the Gauss-Lobatto segment.  Must be
        an odd number.
    seg_idx : int
        The index of this segment within its phase.
    compressed : bool
        True if the subset requested is for a phase with compressed transcription.

    Returns
    -------
    dict
        A dictionary with the following keys:
        'state_disc' Gives the indices of the state discretization nodes
        'state_input' Gives the indices of the state input nodes
        'control_disc' Gives the indices of the control discretization nodes
        'control_input' Gives the indices of the control input nodes
        'segment_ends' Gives the indices of the nodes at the start (even) and end (odd) of a segment
        'col' Gives the indices of the collocation nodes.
        'all' Gives all node indices.
    np.array
        The location of all nodes on [-1, 1].
    np.array
        The weights of all nodes on [-1, 1].

    Notes
    -----
    Subset 'state_input' is the same as subset 'state_disc' if `compressed == False` or
    `first_seg == True`.  The same is true of subsets 'control_input' and 'control_disc'.
    """
    if n < 2:
        raise ValueError('The number of nodes must be larger than 1.')

    subsets = {
        'state_disc': np.arange(n, dtype=int),
        'state_input': np.arange(n, dtype=int) if not compressed or seg_idx == 0
        else np.arange(1, n, 2, dtype=int),
        'control_disc': np.arange(n, dtype=int),
        'control_input': np.arange(n, dtype=int) if not compressed or seg_idx == 0
        else np.arange(1, n, dtype=int),
        'segment_ends': np.array([0, n-1], dtype=int),
        'col': np.arange(n, dtype=int),
        'all': np.arange(n, dtype=int),
        'solution': np.arange(n, dtype=int),
    }

    return subsets, *cgl(n)


def radau_pseudospectral_subsets_and_nodes(n, seg_idx, compressed=False):
    """
    Provides node information and the location of the nodes for n Radau nodes on the range [-1, 1].

    Parameters
    ----------
    n : int
        The total number of nodes in the Radau Pseudospectral segment (including right endpoint).
    seg_idx : int
        The index of this segment within its phase.
    compressed : bool
        True if the subset requested is for a phase with compressed transcription.

    Returns
    -------
    dict
        A dictionary with the following keys:
        'state_disc' gives the indices of the state discretization nodes.
        'state_input' gives the indices of the state input nodes.
        'control_disc' gives the indices of the control discretization nodes.
        'control_input' gives the indices of the control input nodes.
        'segment_ends' gives the indices of the nodes at the start (even) and end (odd) of a segment.
        'col' gives the indices of the collocation nodes.
        'all' gives all node indices.
    np.array
        The location of all nodes on [-1, 1].
    np.array
        The weights of all nodes on [-1, 1].

    Notes
    -----
    Subset 'state_input' is the same as subset 'state_disc' if `compressed == False` or
    `first_seg == True`.  For Radau-Pseudospectral transcription, subset 'control_input' is always
    the same as subset 'control_disc'.
    """
    subsets = {
        'state_disc': np.arange(n + 1, dtype=int),
        'state_input': np.arange(n + 1, dtype=int) if not compressed or seg_idx == 0
        else np.arange(1, n + 1, dtype=int),
        'control_disc': np.arange(n, dtype=int),
        'control_input': np.arange(n, dtype=int),
        'segment_ends': np.array([0, n], dtype=int),
        'col': np.arange(n, dtype=int),
        'all': np.arange(n + 1, dtype=int),
        'solution': np.arange(n + 1, dtype=int),
    }

    return subsets, *lgr(n, include_endpoint=True)


def birkhoff_subsets_and_nodes(n, grid, seg_idx, compressed=False):
    """
    Provides node information and the location of the nodes for n Radau nodes on the range [-1, 1].

    Parameters
    ----------
    n : int
        The total number of nodes in the segment.
    grid : str
        The type of Gaussian grid used in the transcription.
    seg_idx : int
        The index of this segment within its phase.
    compressed : bool
        True if the subset requested is for a phase with compressed transcription.

    Returns
    -------
    dict
        A dictionary with the following keys:
        'state_disc' gives the indices of the state discretization nodes.
        'state_input' gives the indices of the state input nodes.
        'control_disc' gives the indices of the control discretization nodes.
        'control_input' gives the indices of the control input nodes.
        'segment_ends' gives the indices of the nodes at the start (even) and end (odd) of a segment.
        'col' gives the indices of the collocation nodes.
        'all' gives all node indices.
    np.array
        The location of all nodes on [-1, 1].
    np.array
        The weights of all nodes on [-1, 1].

    Notes
    -----
    Subset 'state_input' is the same as subset 'state_disc' if `compressed == False` or
    `first_seg == True`.  For Radau-Pseudospectral transcription, subset 'control_input' is always
    the same as subset 'control_disc'.
    """
    acceptable_grids = {'lgl', 'lgr', 'cgl'}

    subsets = {
        'state_disc': np.arange(n, dtype=int),
        'state_input': np.arange(n, dtype=int),
        'control_disc': np.arange(n, dtype=int),
        'control_input': np.arange(n, dtype=int),
        'segment_ends': np.array([0, n], dtype=int),
        'col': np.arange(n, dtype=int),
        'solution': np.arange(n, dtype=int),
    }

    if grid == 'lgl':
        nodes, weights = lgl(n)
        subsets['all'] = np.arange(n, dtype=int)
    elif grid == 'lgr':
        nodes, weights = lgr(n, include_endpoint=False)
        subsets['all'] = np.arange(n, dtype=int)
    elif grid == 'cgl':
        nodes, weights = cgl(n)
        subsets['all'] = np.arange(n, dtype=int)
    else:
        raise ValueError(f'Unrecognized grid. Acceptable values are one of {acceptable_grids}')

    return subsets, nodes, weights


def uniform_subsets_and_nodes(n, *args, **kwargs):
    """
    Provides a dict of node info and locations for a uniformly distributed set of n nodes on the range [-1, 1].

    This distribution is not to be used to define polynomials, since equally-spaced nodes
    result in poor polynomial fitting. Most subsets here aside from `all`, `segment_ends`, and
    `solution` are not defined for the uniform distribution.

    Parameters
    ----------
    n : int
        The total number of nodes in the Radau Pseudospectral segment (including right endpoint).
    *args : Iterable
        Non-keyword arguments that make this function consistent with radau_subsets_and_nodes and
        gauss_lobatto_subsets_and_nodes, but whose additional arguments have no bearing on the uniform grid.
    **kwargs : dict
        Keyword arguments that make this function consistent with radau_subsets_and_nodes and
        gauss_lobatto_subsets_and_nodes, but whose keyword arguments have no bearing on the uniform grid.

    Returns
    -------
    dict
        A dictionary with the following keys:
        'state_disc' gives the indices of the state discretization nodes.
        'state_input' gives the indices of the state input nodes.
        'control_disc' gives the indices of the control discretization nodes.
        'control_input' gives the indices of the control input nodes.
        'segment_ends' gives the indices of the nodes at the start (even) and end (odd) of a segment.
        'col' gives the indices of the collocation nodes.
        'all' gives all node indices.
    np.array
        The location of all nodes on [-1, 1].
    """
    subsets = {
        'state_disc': np.empty(0, dtype=int),
        'state_input': np.empty(0, dtype=int),
        'control_disc': np.empty(0, dtype=int),
        'control_input': np.empty(0, dtype=int),
        'segment_ends': np.array([0, n], dtype=int),
        'col': np.empty(0, dtype=int),
        'all': np.arange(n + 1, dtype=int),
        'solution': np.arange(n + 1, dtype=int),
    }
    weights = np.ones(n + 1)
    weights[1:-1] = 2.0
    return subsets, np.linspace(-1, 1, n + 1), weights


def make_subset_map(from_subset_idxs, to_subset_idxs):
    """
    Creates a map from one subset to another using the indices of each subset within all nodes.

    Parameters
    ----------
    from_subset_idxs : iterable of int
        Subset indices for the subset from which we are mapping values.
    to_subset_idxs : iterable of int
        Subset indices for the subset to which we are mapping values.

    Returns
    -------
    numpy.array of int
        An index map which, when applied to values in the from_subset, will provide values
        in the to_subset.
    """
    offset = 0
    subset_map = []
    for i in range(len(to_subset_idxs)):
        if to_subset_idxs[i] not in from_subset_idxs:
            offset += 1
        subset_map.append(i - offset)
    return np.array(subset_map)


class GridData(object):
    """
    Properties associated with the GridData of a phase.

    GridData contains properties associated
    with the "grid" or "mesh" of a phase - the number of segments, the
    polynomial order of each segment, and the relative lengths of the segments.
    In turn, these three defining properties determine various other properties,
    such as indexing arrays used to extract the discretization or collocation
    nodes from a list of all nodes within the phase.

    Parameters
    ----------
    num_segments : int
        The number of segments in the phase.
    transcription : str
        Case-insensitive distribution (e.g., ('gauss-lobatto', 'radau-ps', 'explicit', 'uniform')).
    transcription_order : int or int ndarray[:] or str
        The order of the state transcription in each segment, as a scalar or a vector.
    segment_ends : Iterable[num_segments + 1] or None
        The segments nodes on some arbitrary interval.
        This will be normalized to the interval [-1, 1].
    compressed : bool
        If the transcription is compressed, then states and controls at shared
        nodes of adjacent segments are only specified once, and then broadcast
        to the appropriate indices.
    num_steps_per_segment : int or None
        The number of steps to take in each segment, for explicitly integrated phases.

    Attributes
    ----------
    transcription : str
        The transcription to which this GridData instance applies.  One of
        'gauss-lobatto' or 'radau-ps'.
    num_segments : int
        The number of segments in the phase
    segment_ends : ndarray or None
        The segment boundaries in non-dimensional phase time (phase tau space).
        If given as a Iterable, it must be of length (num_segments+1) and it
        must be monotonically increasing.
        If None, then the segments are equally spaced.
    num_steps_per_segment : int
        The number of steps to take in each segment of the phase, for explicit phases.
    num_nodes : int
        The total number of nodes in the phase
    node_weight : ndarray
        The quadrature weight for each node on the interval [-1, 1].
    node_stau : ndarray
        The locations of each node in non-dimensional segment time (segment tau space).
    node_ptau : ndarray
        The locations of each node in non-dimensional phase time (phase tau space).
    node_dptau_dstau : ndarray
        The ratio of phase tau to segment tau at each node.
    segment_indices : int ndarray[:,2]
        Array where each row contains the start and end indices into the nodes.
    subset_node_indices : dict of int ndarray[:]
        Dict keyed by subset name where each entry are the indices of the nodes
        belonging to that given subset.
    subset_segment_indices: dict of int ndarray[num_seg,:]
        Dict keyed by subset name where each entry are the indices of the nodes
        belonging to the given subset, indexed into subset_node_indices!
    subset_num_nodes: dict of int
        A dict keyed by subset name that provides the total number of
        nodes in the phase which belong to the given subset.
    subset_num_nodes_per_segment: dict of list
        A dict keyed by subset name that provides a list of ints giving the number of
        nodes which belong to the given subset in each segment.
    compressed: bool
        True if the transcription is compressed (connecting nodes of adjacent segments
        are not duplicated in the inputs).
    input_maps: dict of int ndarray[:]
        Dict keyed by the map name that provides a mapping for src_indices to
        and from "compressed" form.
    """
    def __init__(self, num_segments, transcription, transcription_order=None,
                 segment_ends=None, compressed=False, num_steps_per_segment=1):
        if segment_ends is None:
            segment_ends = np.linspace(-1, 1, num_segments + 1)
        else:
            if len(segment_ends) != num_segments + 1:
                raise ValueError('segment_ends must be of length (num_segments + 1)')
            # Assert monotonic increasing
            if not np.all(np.diff(segment_ends) > 0):
                raise ValueError('segment_ends must be monotonically increasing')
            segment_ends = np.atleast_1d(segment_ends)

        v0 = segment_ends[0]
        v1 = segment_ends[-1]
        segment_ends = -1. + 2 * (segment_ends - v0) / (v1 - v0)

        # List of all GridData attributes

        self.num_segments = num_segments

        self.segment_ends = segment_ends

        self.num_nodes = 0

        self.num_steps_per_segment = 0

        self.node_weight = np.empty(0,)

        self.node_stau = np.empty(0,)

        self.node_ptau = np.empty(0,)

        self.node_dptau_dstau = np.empty(0,)

        self.segment_indices = np.empty((num_segments, 2), dtype=int)

        self.subset_node_indices = {}

        self.subset_segment_indices = {}

        self.subset_num_nodes = {}

        self.subset_num_nodes_per_segment = {}

        self.compressed = compressed

        self.input_maps = {'state_input_to_disc': np.empty(0, dtype=int),
                           'dynamic_control_input_to_disc': np.empty(0, dtype=int)}

        if transcription.lower() in ['radau', 'radau-ps', 'lgr']:
            self.transcription = 'radau-ps'
        elif transcription.lower() in ['gausslobatto', 'gauss-lobatto', 'lgl']:
            self.transcription = 'gauss-lobatto'
        elif transcription.lower() in ['chebyshev-gauss-lobatto', 'cgl']:
            self.transcription = 'chebyshev-gauss-lobatto'
        elif transcription.lower() in ['birkhoff']:
            self.transcription = 'birkhoff'
        elif transcription.lower() in ['uniform']:
            self.transcription = 'uniform'
        else:
            raise ValueError(f'Unknown transcription: {transcription}')

        # Define get_subsets and node points based on the transcription scheme
        if self.transcription == 'gauss-lobatto':
            get_subsets_and_nodes = gauss_lobatto_subsets_and_nodes
        if self.transcription == 'chebyshev-gauss-lobatto':
            get_subsets_and_nodes = chebyshev_gauss_lobatto_subsets_and_nodes
        elif self.transcription == 'radau-ps':
            get_subsets_and_nodes = radau_pseudospectral_subsets_and_nodes
        elif self.transcription == 'uniform':
            get_subsets_and_nodes = uniform_subsets_and_nodes
        elif self.transcription == 'birkhoff':
            get_subsets_and_nodes = functools.partial(birkhoff_subsets_and_nodes, grid=self.grid_type)

        # Make sure transcription_order is a vector
        if isinstance(transcription_order, str):
            self.transcription_order = num_segments * [transcription_order]
        elif np.ndim(transcription_order) == 0:  # scalar
            self.transcription_order = np.ones(num_segments, int) * transcription_order
        elif np.size(transcription_order) == 1:  # length-1 array
            self.transcription_order = np.ones(num_segments, int) * np.asarray(transcription_order)[0]
        else:
            self.transcription_order = np.asarray(transcription_order, dtype=int)

        # Make sure num_steps_per_segment is a vector
        num_steps_per_segment = np.ones(num_segments, int) * num_steps_per_segment
        self.num_steps_per_segment = num_steps_per_segment

        # Build up the arrays segment by segment
        self.segment_indices[0, 0] = 0
        ind0 = 0  # index of the first node in the segment
        for iseg in range(num_segments):
            subsets_i, nodes_i, weights_i = get_subsets_and_nodes(self.transcription_order[iseg],
                                                                  seg_idx=iseg,
                                                                  compressed=compressed)

            if iseg == 0:
                subset_ind0 = {name: 0 for name in subsets_i}
                # index of the first node in the segment for each subset
                subset_ind1 = subset_ind0.copy()
                # index of the last node in the segment for each subset

            num_nodes_i = len(nodes_i)
            self.num_nodes += num_nodes_i

            # Append our nodes in segment tau space
            self.node_stau = np.concatenate((self.node_stau, nodes_i))

            # Append our node weights
            self.node_weight = np.concatenate((self.node_weight, weights_i))

            # Append our nodes in phase tau space
            v0 = segment_ends[iseg]
            v1 = segment_ends[iseg + 1]
            self.node_ptau = np.concatenate((self.node_ptau, v0 + 0.5 * (nodes_i + 1) * (v1 - v0)))
            self.node_dptau_dstau = np.concatenate((self.node_dptau_dstau,
                                                    0.5 * (v1 - v0) * np.ones_like(nodes_i)))

            self.segment_indices[iseg, 1] = self.segment_indices[iseg, 0] + num_nodes_i
            if iseg < num_segments - 1:
                self.segment_indices[iseg + 1, 0] = self.segment_indices[iseg, 1]

            for subset_name, subset_idxs_i in subsets_i.items():
                if iseg == 0:
                    self.subset_num_nodes[subset_name] = 0
                    self.subset_num_nodes_per_segment[subset_name] = []
                    self.subset_segment_indices[subset_name] = np.zeros((num_segments, 2),
                                                                        dtype=int)
                    self.subset_node_indices[subset_name] = np.empty(0, dtype=int)

                if subset_idxs_i is None:
                    num_subset_nodes_i = 0
                else:
                    num_subset_nodes_i = len(subset_idxs_i)

                self.subset_num_nodes[subset_name] += num_subset_nodes_i
                self.subset_num_nodes_per_segment[subset_name].append(num_subset_nodes_i)
                subset_ind1[subset_name] += num_subset_nodes_i

                self.subset_segment_indices[subset_name][iseg, 0] = subset_ind0[subset_name]
                self.subset_segment_indices[subset_name][iseg, 1] = subset_ind1[subset_name]

                self.subset_node_indices[subset_name] = \
                    np.concatenate((self.subset_node_indices[subset_name], subset_idxs_i + ind0))

                subset_ind0[subset_name] += num_subset_nodes_i

            ind0 += num_nodes_i  # The first node in the next segment

        state_input_idxs = self.subset_node_indices['state_input']
        state_disc_idxs = self.subset_node_indices['state_disc']

        control_input_idxs = self.subset_node_indices['control_input']
        control_disc_idxs = self.subset_node_indices['control_disc']

        self.input_maps['state_input_to_disc'] = make_subset_map(state_input_idxs, state_disc_idxs)

        self.input_maps['dynamic_control_input_to_disc'] = make_subset_map(control_input_idxs,
                                                                           control_disc_idxs)

    def __eq__(self, other):
        """
        Compare this GridData with an object with other and return True if they are equivalent.

        Parameters
        ----------
        other : GridData

        Returns
        -------
        bool
            True if other is equivalent to self, otherwise False.
        """
        if isinstance(other, GridData):
            return self.transcription == other.transcription and \
                self.num_segments == other.num_segments and \
                np.all(self.segment_ends == other.segment_ends) and \
                self.compressed == other.compressed and \
                np.all(self.transcription_order == other.transcription_order) and \
                np.all(self.num_steps_per_segment == other.num_steps_per_segment)
        else:
            return False

    def __repr__(self):
        return f'{self.__class__.__name__}(num_seg={self.num_segments}, order={self.transcription_order}) at <{id(self)}>'

    def is_aligned_with(self, other, tol=1.0E-12):
        """
        Check that the segment distribution in GridData object `other` matches that of this GridData object.

        Parameters
        ----------
        other : GridData
            GridData object against which this one is being compared.
        tol : float
            The absolute tolerance in difference between segment end locations in phase tau space.

        Returns
        -------
        bool
            True if the two GridData objects have the same number of segments and their segments match to within
            the specified tolerance, otherwise False.
        """
        # The segment distribution needs to be the same in from the input grid to the output grid.
        return self.num_segments == other.num_segments and \
            (np.abs(self.segment_ends - other.segment_ends) <= tol).all()

    def phase_lagrange_matrices(self, given_set_name, eval_set_name, sparse=False):
        """
        Compute the matrices mapping values at some nodes to values and derivatives at new nodes.

        Parameters
        ----------
        given_set_name : str
            Name of the set of nodes with which to perform the interpolation.
        eval_set_name : str
            Name of the set of nodes at which to evaluate the values and derivatives.
        sparse : bool
            If True, the returned matrix will be in scipy CSR sparse format.  Otherwise, it is
            returned as a dense numpy.array.

        Returns
        -------
        ndarray[num_eval_set, num_given_set]
            Matrix containing the values at the new nodes.
        ndarray[num_eval_set, num_given_set]
            Matrix containing the time derivatives at the new nodes.

        Notes
        -----
        The values are mapped using the equation:

        .. math::

            x_{eval} = \\left[ L \\right] x_{given}

        And the derivatives are mapped with the equation:

        .. math::

            \\dot{x}_{eval} = \\left[ D \\right] x_{given} \\frac{d \\tau}{dt}
        """
        L_blocks = []
        D_blocks = []

        for iseg in range(self.num_segments):
            i1, i2 = self.subset_segment_indices[given_set_name][iseg, :]
            indices = self.subset_node_indices[given_set_name][i1:i2]
            nodes_given = self.node_stau[indices]

            i1, i2 = self.subset_segment_indices[eval_set_name][iseg, :]
            indices = self.subset_node_indices[eval_set_name][i1:i2]
            nodes_eval = self.node_stau[indices]

            L_block, D_block = lagrange_matrices(nodes_given, nodes_eval)

            L_blocks.append(L_block)
            D_blocks.append(D_block)

        L = block_diag(*L_blocks)
        D = block_diag(*D_blocks)

        if sparse:
            L = sp.csr_matrix(L)
            D = sp.csr_matrix(D)

        return L, D

    def phase_hermite_matrices(self, given_set_name, eval_set_name, sparse=False):
        """
        Compute the matrices mapping values at some nodes to values and derivatives at new nodes.

        Parameters
        ----------
        given_set_name : str
            Name of the set of nodes with which to perform the interpolation.
        eval_set_name : str
            Name of the set of nodes at which to evaluate the values and derivatives.
        sparse : bool
            If True, the returned matrix will be in scipy CSR sparse format.  Otherwise, it is
            returned as a dense numpy.array.

        Returns
        -------
        ndarray[num_eval_set, num_given_set]
            Matrix that maps values at given nodes to values at eval nodes.
            This is A_i in the equations above.
        ndarray[num_eval_set, num_given_set]
            Matrix that maps derivatives at given nodes to values at eval nodes.
            This is B_i in the equations above.
        ndarray[num_eval_set, num_given_set]
            Matrix that maps values at given nodes to derivatives at eval nodes.
            This is A_d in the equations above.
        ndarray[num_eval_set, num_given_set]
            Matrix that maps derivatives at given nodes to derivatives at eval nodes.
            This is A_d in the equations above.

        Notes
        -----
        The equation for Hermite interpolation of the values is:

        .. math::

            x_{eval} = \\left[ A_i \\right] x_{given}
                             + \\frac{dt}{d\\tau} \\left[ B_i \\right] \\dot{x}_{given}

        Hermite interpolation of the derivatives is performed as:

        .. math::

            \\dot{x}_{eval} = \\frac{d\\tau}{dt} \\left[ A_d \\right] x_{given}
                                   + \\left[ B_d \\right] \\dot{x}_{given}
        """
        Ai_list = []
        Bi_list = []
        Ad_list = []
        Bd_list = []

        for iseg in range(self.num_segments):
            i1, i2 = self.subset_segment_indices[given_set_name][iseg, :]
            indices = self.subset_node_indices[given_set_name][i1:i2]
            nodes_given = self.node_stau[indices]

            i1, i2 = self.subset_segment_indices[eval_set_name][iseg, :]
            indices = self.subset_node_indices[eval_set_name][i1:i2]
            nodes_eval = self.node_stau[indices]

            Ai_seg, Bi_seg, Ad_seg, Bd_seg = hermite_matrices(nodes_given, nodes_eval)

            Ai_list.append(Ai_seg)
            Bi_list.append(Bi_seg)
            Ad_list.append(Ad_seg)
            Bd_list.append(Bd_seg)

        Ai = block_diag(*Ai_list)
        Bi = block_diag(*Bi_list)
        Ad = block_diag(*Ad_list)
        Bd = block_diag(*Bd_list)

        if sparse:
            Ai = sp.csr_matrix(Ai)
            Bi = sp.csr_matrix(Bi)
            Ad = sp.csr_matrix(Ad)
            Bd = sp.csr_matrix(Bd)

        return Ai, Bi, Ad, Bd


class GaussLobattoGrid(GridData):
    """
    A GridData object that provides the node information for a Gauss-Lobatto distribution.

    Parameters
    ----------
    num_segments : int
        The number of segments in the phase.
    nodes_per_seg : int or iterable
        The number of nodes in each segment. As an integer, it applies to each segment. If a sequence, its length
        must be equal to num_segments.
    segment_ends : Iterable[num_segments + 1] or None
        The segments nodes on some arbitrary interval.
        This will be normalized to the interval [-1, 1].
    compressed : bool
        If the transcription is compressed, then states and controls at shared
        nodes of adjacent segments are only specified once, and then broadcast
        to the appropriate indices.
    """
    def __init__(self, num_segments, nodes_per_seg, segment_ends=None, compressed=False):
        self.grid_type = 'lgl'
        super().__init__(num_segments=num_segments, transcription='gauss-lobatto',
                         transcription_order=np.asarray(nodes_per_seg, dtype=int),
                         segment_ends=segment_ends, compressed=compressed)


class ChebyshevGaussLobattoGrid(GridData):
    """
    A GridData object that provides the node information for a Gauss-Lobatto distribution.

    Parameters
    ----------
    num_segments : int
        The number of segments in the phase.
    nodes_per_seg : int or iterable
        The number of nodes in each segment. As an integer, it applies to each segment. If a sequence, its length
        must be equal to num_segments.
    segment_ends : Iterable[num_segments + 1] or None
        The segments nodes on some arbitrary interval.
        This will be normalized to the interval [-1, 1].
    compressed : bool
        If the transcription is compressed, then states and controls at shared
        nodes of adjacent segments are only specified once, and then broadcast
        to the appropriate indices.
    """
    def __init__(self, num_segments, nodes_per_seg, segment_ends=None, compressed=False):
        self.grid_type = 'cgl'
        super().__init__(num_segments=num_segments, transcription='chebyshev-gauss-lobatto',
                         transcription_order=np.asarray(nodes_per_seg, dtype=int),
                         segment_ends=segment_ends, compressed=compressed)


class BirkhoffGrid(GridData):
    """
    A GridData object that provides the node information for the Birkhoff transcription.

    Parameters
    ----------
    num_nodes : int
        The number of nodes in the grid.
    grid_type : str
        The type of Gaussian grid used for the transcription. May be 'lgl' or 'cgl'.
    """
    def __init__(self, num_nodes, grid_type='cgl'):
        self.grid_type = grid_type
        super().__init__(num_segments=1, transcription='birkhoff',
                         transcription_order=num_nodes)


class RadauGrid(GridData):
    """
    A GridData object that provides the node information for a Radau distribution.

    Parameters
    ----------
    num_segments : int
        The number of segments in the phase.
    nodes_per_seg : int or iterable
        The number of nodes in each segment. As an integer, it applies to each segment. If a sequence, its length
        must be equal to num_segments.
    segment_ends : Iterable[num_segments + 1] or None
        The segments nodes on some arbitrary interval.
        This will be normalized to the interval [-1, 1].
    compressed : bool
        If the transcription is compressed, then states and controls at shared
        nodes of adjacent segments are only specified once, and then broadcast
        to the appropriate indices.
    """
    def __init__(self, num_segments, nodes_per_seg, segment_ends=None, compressed=False):
        self.grid_type = 'lgr'
        super().__init__(num_segments=num_segments, transcription='radau-ps',
                         transcription_order=np.asarray(nodes_per_seg, dtype=int) - 1,
                         segment_ends=segment_ends, compressed=compressed)


class UniformGrid(GridData):
    """
    A GridData object that provides the node information for a uniform distribution.

    Parameters
    ----------
    num_segments : int
        The number of segments in the phase.
    nodes_per_seg : int or iterable
        The number of nodes in each segment. As an integer, it applies to each segment. If a sequence, its length
        must be equal to num_segments.
    segment_ends : Iterable[num_segments + 1] or None
        The segments nodes on some arbitrary interval.
        This will be normalized to the interval [-1, 1].
    compressed : bool
        If the transcription is compressed, then states and controls at shared
        nodes of adjacent segments are only specified once, and then broadcast
        to the appropriate indices.
    """
    def __init__(self, num_segments, nodes_per_seg, segment_ends=None, compressed=False):
        self.grid_type = 'uniform'
        super().__init__(num_segments=num_segments, transcription='uniform',
                         transcription_order=np.asarray(nodes_per_seg) - 1,
                         segment_ends=segment_ends, compressed=compressed)
