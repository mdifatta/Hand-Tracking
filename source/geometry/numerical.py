from scipy.optimize import fsolve, minimize
import numpy as np
from geometry.transforms import *
from numpy.linalg import norm

# debug
from geometry.hand_localization_expl import drawpnts

# BASE PALM POINTS DIRECT INFERENCE

def line_projection_system(sols, params):
    return (sols[0] ** 2 - 2 * params["c01"] * sols[0] * sols[1] + sols[1] ** 2 - params["d01"] ** 2,
            sols[0] ** 2 - 2 * params["c02"] * sols[0] * sols[2] + sols[2] ** 2 - params["d02"] ** 2,
            sols[1] ** 2 - 2 * params["c12"] * sols[1] * sols[2] + sols[2] ** 2 - params["d12"] ** 2)


def line_projection_system_jac(sols, params):
    return [[2 * sols[0] - 2 * params["c01"] * sols[1],
            2 * sols[0] - 2 * params["c02"] * sols[2],
            0],
            [-2 * params["c01"] * sols[0] + 2 * sols[1],
             0,
             2 * sols[1] - 2 * params["c12"] * sols[2]],
            [0,
             -2 * params["c02"] * sols[0] + 2 * sols[2],
             -2 * params["c12"] * sols[1] + 2 * sols[2]]]


def get_points_projections_to_lines(basepts, lines, maxerr=1e-3, maxrestart=1000):
    params = {
        "c01": np.dot(lines[0], lines[1]),
        "c02": np.dot(lines[0], lines[2]),
        "c12": np.dot(lines[1], lines[2]),
        "d01": np.linalg.norm(basepts[0]-basepts[1]),
        "d02": np.linalg.norm(basepts[0]-basepts[2]),
        "d12": np.linalg.norm(basepts[1]-basepts[2])
    }

    dists = np.array([params["d01"], params["d02"], params["d12"]])
    cosines = np.array([params["c01"], params["c02"], params["c12"]])
    # avg = np.average(dists)
    # variance = np.var(dists)
    avg = dists[np.argmax(cosines)]/np.max(cosines)
    variance = np.var(dists / cosines)
    bestsol = None
    besterr = np.inf
    for i in range(maxrestart):
        start = np.random.normal(loc=avg, scale=variance, size=(3,))
        sol, info, stat, msg = fsolve(line_projection_system, start, params, full_output=True)
        err = np.linalg.norm(info["fvec"])
        if err < maxerr:
            if sol[0] < 0:
                sol = -sol
            return np.array([lines[i] * sol[i] for i in range(3)])
        if err < besterr:
            if sol[0] < 0:
                bestsol = -sol
            else:
                bestsol = sol
    print("WARNING: Maxrestarts expired, the proposed solution has error %f" % besterr)
    return np.array([lines[i] * bestsol[i] for i in range(3)])


def get_points_projection_to_lines_pair(basepts, lines, maxerr=1e-3, maxrestart=10, maxtrials=10):
    pts = get_points_projections_to_lines(basepts=basepts, lines=lines)
    pts2 = get_points_projections_to_lines(basepts=basepts, lines=lines)

    count = 1
    while np.linalg.norm(pts - pts2) < 1e-5 and count < maxtrials:
        count += 1
        pts2 = get_points_projections_to_lines(basepts=basepts,
                                               lines=lines,
                                               maxerr=maxerr,
                                               maxrestart=maxrestart)
    return pts, pts2


# CONSTRAINED FINGER INFERENCE

OBJ_LINE = 'v'
CENTER = 'c'
RAD = 'r'
NORM_COS = 'kn'
PLANE_COS = 'kp'
BASEREF = 'br'

numeric_dbg_canvas = None
numeric_dbg_cal = None

def prepare_problem_params(center, norm_v, tang_v, radius, normcos, planecos, objline):
    # perform a base change -> norm as x-axis, tang as y-axis
    # to optimize the objective evaluation
    conorm = np.cross(norm_v, tang_v)
    params = {
        BASEREF: np.stack((norm_v, tang_v, conorm)),
        RAD: radius,
        NORM_COS: normcos,
        PLANE_COS: planecos
    }
    params[CENTER] = params[BASEREF] @ center
    params[OBJ_LINE] = params[BASEREF] @ objline
    return params


def build_constraints(params: dict):
    return ({'type': 'ineq', 'fun': subject_to_cosplane, 'args': (params[PLANE_COS] ** 2,)},
            {'type': 'ineq', 'fun': subject_to_existence})


def build_bounds(params: dict):
    an_min = params[NORM_COS]
    an_max = 1.0
    at_max = np.sqrt(1.0 - params[NORM_COS] ** 2)
    return (an_min, an_max), (-at_max, at_max)


def truncate_by_bounds(proposed_sol, bounds):
    out = proposed_sol[:]
    for i in range(2):
        if out[i] < bounds[i][0]:
            out[i] = bounds[i][0]
        elif out[i] > bounds[i][1]:
            out[i] = bounds[i][1]
    return out


def trd_sol_elem(proposed_sol):
    arg = 1 - proposed_sol[0]**2 - proposed_sol[1]**2
    if arg <= 0:
        return np.zeros(shape=(2, 1))
    ret = np.sqrt(arg)
    return [[-ret], [ret]]


def rel_pnt(proposed_sol: np.ndarray, rad):
    return np.concatenate((np.tile(proposed_sol, (2, 1)),
                           trd_sol_elem(proposed_sol)), axis=1)*rad


def take_final_sol(proposed_sol: np.ndarray, params: dict):
    fp = rel_pnt(proposed_sol, params[RAD]) + params[CENTER]
    ret = -np.dot(fp, params[OBJ_LINE]) / norm(fp, axis=1)
    if ret[0] < ret[1]:
        return fp[0]
    return fp[1]

# lastloss = None
# lastcol = 128


def minimizing_obj(proposed_sol: np.ndarray, params: dict):
    fp = rel_pnt(proposed_sol, params[RAD]) + params[CENTER]
    ret = -np.dot(fp, params[OBJ_LINE]) / norm(fp, axis=1)
    return min(ret)

    # DEBUG CODE
    # global lastloss
    # global lastcol
    # if lastloss is not None:
    #     col = lastcol + (lastloss - loss)/0.01 * 5
    #     if col < 0:
    #         col = 0
    #     lastcol = col
    # else:
    #     lastcol = 128
    #     col = 128
    #     lastloss = loss
    # drawpnts([column_matmul(np.transpose(params[BASEREF]), fp1)],
    #          canvas=numeric_dbg_canvas,
    #          cal=numeric_dbg_cal,
    #          fill="#%02X%02X%02X"%(int(col), int(col), int(col)))

    # print("Loss: %f" % min(ret1, ret2))
    # import time
    # time.sleep(0.2)


def subject_to_cosplane(proposed_sol: np.ndarray, spcos):
    return norm(proposed_sol) ** 2 - spcos


def subject_to_existence(proposed_sol: np.ndarray):
    return 1 - norm(proposed_sol) ** 2


def extract_solution(proposed_sol: np.ndarray, params: dict):
    pnt = take_final_sol(proposed_sol, params)
    return np.transpose(params[BASEREF]) @ pnt


def find_best_point_in_cone(center, norm_vers, tang_vers, radius, normcos, planecos, objline, suggestion=None):

    # global numeric_dbg_canvas
    # numeric_dbg_canvas = dbgcanvas
    # global numeric_dbg_cal
    # numeric_dbg_cal = dbgcal
    # global lastloss
    # lastloss = None

    def checknorm(subj):
        nrm = norm(subj)
        if nrm < 0.999 or nrm > 1.001:
            return subj / nrm
        return subj

    norm_vers = checknorm(norm_vers)

    if np.dot(norm_vers, tang_vers) > 1e-8:
        tang_vers = np.cross(np.cross(norm_vers, tang_vers), norm_vers)

    tang_vers = checknorm(tang_vers)
    objline = checknorm(objline)

    params = prepare_problem_params(center, norm_vers, tang_vers, radius, normcos, planecos, objline)
    bounds = build_bounds(params)
    constr = build_constraints(params)

    starting_sol = np.array([1.0, 0.0])
    idx = 0
    if suggestion is not None:
        bestobj = minimizing_obj(starting_sol, params)
        for sugg in suggestion:
            suggested_vers = normalize(sugg-center)
            base_wise_sugg = (params[BASEREF] @ suggested_vers)[0:2]
            base_wise_sugg = truncate_by_bounds(base_wise_sugg, bounds)
            currobj = minimizing_obj(base_wise_sugg, params)
            idx += 1
            if bestobj > currobj:
                # print("Sugg. %d is better than previous. Taking it" % idx)
                starting_sol = base_wise_sugg
                bestobj = currobj

    def action():
        global res
        res = minimize(minimizing_obj, starting_sol, bounds=bounds, args=params, constraints=constr)

    # import timeit
    # print("Optimization problem solved in %f ms." % (1000 * timeit.timeit(action, number=1),))
    action()
    if not res.success:
        print("Optimization failure. Message: %s" % res.message)
        print(res.x)

    # print("COSPLANE CONSTR: %f" % subject_to_cosplane(proposed_sol=res.x, spcos=params[PLANE_COS]**2))
    # print("EXISTENCE CONSTR: %f" % subject_to_existence(proposed_sol=res.x))
    # print("OBJECTIVE: %f" % minimizing_obj(proposed_sol=res.x, params=params))
    # import time
    # time.sleep(2)
    # numeric_dbg_canvas.delete("debug")
    return extract_solution(res.x, params)
