import numpy as np

import qpoases
from qpoases import PyReturnValue
import casadi as ca

from giskardpy.exceptions import MAX_NWSR_REACHEDException, QPSolverException
from giskardpy import logging


class QPSolver(object):
    # RETURN_VALUE_DICT = {value: name for name, value in vars(PyReturnValue).items()}

    def __init__(self, dim_a, dim_b):
        """
        :param dim_a: number of joint constraints + number of soft constraints
        :type int
        :param dim_b: number of hard constraints + number of soft constraints
        :type int
        """

        # self.qpProblem = qpoases.PySQProblem(dim_a, dim_b)
        # options = qpoases.PyOptions()
        # options.setToMPC()
        # options.printLevel = qpoases.PyPrintLevel.NONE
        # self.qpProblem.setOptions(options)
        # self.xdot_full = np.zeros(dim_a)
        #
        self.started = False

    def init_problem(self, H, g, A, lb, ub, lbA, ubA, nWSR=None):
        qp = {}
        qp['h'] = ca.DM(H).sparsity()
        qp['a'] = ca.DM(A).sparsity()
        # opts = {'verbose': False,
        #         'print_time': False,
        #         'print_info':False,
        #         'print_header':False,
        #         'print_iter':False
        #         }
        # self.qp_problem = ca.conic('S', 'qrqp', qp, opts)
        # opts = {'osqp': { 'verbose': False,
        #                   'time_limit': 1.
        #                   },
        #         'warm_start_primal': True}
        # self.qp_problem = ca.conic('S', 'osqp', qp, opts)
        opts = {'verbose': False,
                'print_time': False,
                'printLevel': 'none',
                }
        self.qp_problem = ca.conic('S', 'qpoases', qp, opts)
        self.started = True
        r = self.qp_problem(h=H, g=g, a=A, lba=lbA, uba=ubA, lbx=lb, ubx=ub)
        self.x_opt = np.array(r['x'])
        return self.x_opt

    def hot_start(self, H, g, A, lb, ub, lbA, ubA, nWSR=None):
        H = ca.sparsify(ca.DM(H))
        A = ca.sparsify(ca.DM(A))
        r = self.qp_problem(h=H, g=g, a=A, lba=lbA, uba=ubA, lbx=lb, ubx=ub, x0=self.x_opt)
        self.x_opt = np.array(r['x'])
        return self.x_opt

    def solve(self, H, g, A, lb, ub, lbA, ubA, nWSR=None):
        """
        x^T*H*x + x^T*g
        s.t.: lbA < A*x < ubA
        and    lb <  x  < ub
        :param H: 2d diagonal weight matrix, shape = (jc (joint constraints) + sc (soft constraints)) * (jc + sc)
        :type np.array
        :param g: 1d zero vector of len joint constraints + soft constraints
        :type np.array
        :param A: 2d jacobi matrix of hc (hard constraints) and sc, shape = (hc + sc) * (number of joints)
        :type np.array
        :param lb: 1d vector containing lower bound of x, len = jc + sc
        :type np.array
        :param ub: 1d vector containing upper bound of x, len = js + sc
        :type np.array
        :param lbA: 1d vector containing lower bounds for the change of hc and sc, len = hc+sc
        :type np.array
        :param ubA: 1d vector containing upper bounds for the change of hc and sc, len = hc+sc
        :type np.array
        :param nWSR:
        :type np.array
        :return: x according to the equations above, len = joint constraints + soft constraints
        :type np.array
        """
        if not self.started:
            return self.init_problem(H, g, A, lb, ub, lbA, ubA)
        else:
            return self.hot_start(H, g, A, lb, ub, lbA, ubA)
        # number_of_retries = 2
        # while number_of_retries > 0:
        #     if nWSR is None:
        #         nWSR = np.array([sum(A.shape) * 2])
        #     else:
        #         nWSR = np.array([nWSR])
        #     number_of_retries -= 1
        #     if not self.started:
        #         success = self.init_problem(H, g, A, lb, ub, lbA, ubA, nWSR)
        #         if success == PyReturnValue.MAX_NWSR_REACHED:
        #             self.started = False
        #             raise MAX_NWSR_REACHEDException(u'Failed to initialize QP-problem.')
        #     else:
        #         success = self.qpProblem.hotstart(H, g, A, lb, ub, lbA, ubA, nWSR)
        #         if success == PyReturnValue.MAX_NWSR_REACHED:
        #             self.started = False
        #             raise MAX_NWSR_REACHEDException(u'Failed to hot start QP-problem.')
        #     if success == PyReturnValue.SUCCESSFUL_RETURN:
        #         self.started = True
        #         break
        #     elif success == PyReturnValue.NAN_IN_LB:
        #         # TODO nans get replaced with 0 document this somewhere
        #         # TODO might still be buggy when nan occur when the qp problem is already initialized
        #         lb[np.isnan(lb)] = 0
        #         nWSR = None
        #         self.started = False
        #         number_of_retries += 1
        #         continue
        #     elif success == PyReturnValue.NAN_IN_UB:
        #         ub[np.isnan(ub)] = 0
        #         nWSR = None
        #         self.started = False
        #         number_of_retries += 1
        #         continue
        #     elif success == PyReturnValue.NAN_IN_LBA:
        #         lbA[np.isnan(lbA)] = 0
        #         nWSR = None
        #         self.started = False
        #         number_of_retries += 1
        #         continue
        #     elif success == PyReturnValue.NAN_IN_UBA:
        #         ubA[np.isnan(ubA)] = 0
        #         nWSR = None
        #         self.started = False
        #         number_of_retries += 1
        #         continue
        #     else:
        #         logging.loginfo(u'{}; retrying with A rounded to 5 decimal places'.format(self.RETURN_VALUE_DICT[success]))
        #         r = 5
        #         A = np.round(A, r)
        #         nWSR = None
        #         self.started = False
        # else:  # if not break
        #     self.started = False
        #     raise QPSolverException(self.RETURN_VALUE_DICT[success])
        #
        # self.qpProblem.getPrimalSolution(self.xdot_full)
        # return self.xdot_full
