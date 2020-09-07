from copy import copy

from py_trees import Status

import giskardpy.identifier as identifier
from giskardpy.plugin import GiskardBehavior
from giskardpy.symengine_controller import InstantaneousController
from collections import OrderedDict, namedtuple

import kineverse.gradients.gradient_math as gm

class ControllerPlugin(GiskardBehavior):
    def __init__(self, name):
        super(ControllerPlugin, self).__init__(name)
        self.path_to_functions = self.get_god_map().get_data(identifier.data_folder)
        self.nWSR = self.get_god_map().get_data(identifier.nWSR)
        self.soft_constraints = None
        self.joint_constraints = None
        self.qp_data = {}
        self.get_god_map().safe_set_data(identifier.qp_data, self.qp_data)  # safe dict on godmap and work on ref
        self.rc_prismatic_velocity = self.get_god_map().get_data(identifier.rc_prismatic_velocity)
        self.rc_continuous_velocity = self.get_god_map().get_data(identifier.rc_continuous_velocity)
        self.rc_revolute_velocity = self.get_god_map().get_data(identifier.rc_revolute_velocity)
        self.rc_other_velocity = self.get_god_map().get_data(identifier.rc_other_velocity)

    def initialise(self):
        super(ControllerPlugin, self).initialise()
        self.init_controller()

    def setup(self, timeout=0.0):
        return super(ControllerPlugin, self).setup(5.0)

    def init_controller(self):
        self.soft_constraints = self.get_god_map().get_data(identifier.soft_constraint_identifier)
        self.joint_constraints = self.get_god_map().get_data(identifier.joint_constraint_identifier)
        # self.hard_constraints = self.get_god_map().get_data(identifier.hard_constraint_identifier)

        self.controller = InstantaneousController(u'{}/{}/'.format(self.path_to_functions,
                                                                   self.get_robot().get_name()))

        # joint_to_symbols_str = OrderedDict(
        #     (x, self.get_god_map().to_symbol(identifier.joint_states + [x, u'position'])) for x in self.get_robot().controlled_joints)

        joint_position_symbols = self.get_god_map().get_data(identifier.controlled_joint_symbols)
        joint_to_symbols_str = OrderedDict((self.get_god_map().expr_to_key[str(s)], s) for s in sorted(joint_position_symbols, key=lambda x:str(x)))


        self.controller.update_constraints(joint_to_symbols_str,
                                           self.soft_constraints,
                                           self.joint_constraints)
        self.controller.compile()

        self.qp_data[identifier.weight_keys[-1]], \
        self.qp_data[identifier.b_keys[-1]], \
        self.qp_data[identifier.bA_keys[-1]], \
        self.qp_data[identifier.xdot_keys[-1]] = self.controller.get_qpdata_key_map()

    @profile
    def update(self):
        state_vars = self.controller.get_expr()
        expr = self.god_map.get_values(state_vars)

        next_cmd, \
        self.qp_data[identifier.H[-1]], \
        self.qp_data[identifier.A[-1]], \
        self.qp_data[identifier.lb[-1]], \
        self.qp_data[identifier.ub[-1]], \
        self.qp_data[identifier.lbA[-1]], \
        self.qp_data[identifier.ubA[-1]], \
        self.qp_data[identifier.xdot_full[-1]] = self.controller.get_cmd(expr, self.nWSR)
        self.get_god_map().safe_set_data(identifier.cmd, next_cmd)

        return Status.RUNNING
