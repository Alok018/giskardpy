import hashlib
import warnings
from collections import OrderedDict
from itertools import chain
from giskardpy.qp_problem_builder import QProblemBuilder
from giskardpy.robot import Robot


class InstantaneousController(object):
    """
    This class handles constraints and computes joint commands using symengine and qpOases.
    """

    # TODO should anybody who uses this class know about constraints?


    def __init__(self, path_to_functions):
        """
        :type robot: Robot
        :param path_to_functions: location where compiled functions are stored
        :type: str
        """
        self.path_to_functions = path_to_functions
        self.controlled_joints = []
        self.hard_constraints = {}
        self.joint_constraints = {}
        self.soft_constraints = {}
        self.free_symbols = None
        self.qp_problem_builder = None
        # self.state_ids = None

    def get_qpdata_key_map(self):
        b_keys = []
        weights_keys = []
        xdot_keys = []
        bA_keys = []
        for iJ, k in enumerate(self.joint_constraints.keys()):
            key = u'j -- ' + str(k)
            b_keys.append(key)
            weights_keys.append(key)
            xdot_keys.append(key)

        for iH, k in enumerate(self.hard_constraints.keys()):
            key = u'h -- ' + str(k)
            bA_keys.append(key)

        for iS, k in enumerate(self.soft_constraints.keys()):
            key = str(k)
            bA_keys.append(key)
            weights_keys.append(key)
            xdot_keys.append(key)
        return weights_keys, b_keys, bA_keys, xdot_keys

    def update_constraints(self, joint_to_symbols_str, soft_constraints, joint_constraints):
        """
        Triggers a recompile if the number of soft constraints has changed.
        :type soft_constraints: dict
        :type free_symbols: set
        """
        # TODO bug if soft constraints get replaced, actual amount does not change.
        self.soft_constraints.update(soft_constraints)
        self.qp_problem_builder = None
        self.joint_to_symbols_str = joint_to_symbols_str

        self.joint_constraints = joint_constraints


    def compile(self):
        self.qp_problem_builder = QProblemBuilder(self.joint_constraints,
                                                  self.soft_constraints,
                                                  list(self.joint_to_symbols_str.values()))

    @profile
    def get_cmd(self, substitutions, nWSR=None):
        """
        Computes joint commands that satisfy constrains given substitutions.
        :param substitutions: maps symbol names as str to floats.
        :type substitutions: dict
        :param nWSR: magic number, if None throws errors, increase this until it stops.
        :type nWSR: int
        :return: maps joint names to command
        :rtype: dict
        """
        next_cmd, H, A, lb, ub, lbA, ubA, xdot_full = self.qp_problem_builder.get_cmd(substitutions, nWSR)
        if next_cmd is None:
            pass
        return {name: next_cmd[symbol] for name, symbol in self.joint_to_symbols_str.items()}, \
               H, A, lb, ub, lbA, ubA, xdot_full

    def get_expr(self):
        return self.qp_problem_builder.get_expr()
        # return self.state_ids
