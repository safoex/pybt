import yarp
import time


__A_return_var = None

_yarp = {'nav_write': '...', 'nav_read': '...', 'vis_write': '...', 'vis_read': '...', 'places': {
    'table1': '..',
    'table2': '..',
    'charge': '..',
}}

_threshold = {
    'soda' : 10000,
    'box' : 10000,
    'sprayer' : 10000,
    'mug' : 10000
}

_yarp_actions = {

}
_objects = {

}

yarp.Network.init()


class Nav:
    def __init__(self):
        self.input_nav = yarp.Port()
        self.output_nav = yarp.Port()
        input_port_name = '/robotGoto/status:o'
        local_name = '/local123/nav_status'
        local_out_name = '/local123/nav_cmd'
        self.input_nav.open(local_name)
        self.output_nav.open(local_out_name)
        output_port_name = '/navigationGui/yarpviewTarget:i'
        yarp.Network.connect(input_port_name, local_name)
        yarp.Network.connect(local_out_name, output_port_name)
        time.sleep(1)
        self.places = {
            'table2': [79, 21, 80, 0],
            'table1': [44, 45, 25, 41],
            'table2_r': [76, 24, 68, 42],
            'table1_r': [48, 48, 55, 54]
        }
        self.status = 'navigation_status_moving'
        self.last_task = None

    def step(self):
        x = yarp.Bottle()
        self.input_nav.read(x)
        self.status = x.get(0).asString()

    def goto(self, place):
        if place in self.places:
            x = yarp.Bottle()
            for v in self.places[place]:
                x.addInt(v)
            self.last_task = place
            self.output_nav.write(x)

    def wait_for_reached(self, starting_from, place, delay=0.1):
        self.step()
        if time.clock() - starting_from > delay:
            if self.status == "navigation_status_goal_reached" or self.status == "navigation_status_idle":
                print(self.last_task)
                if place[-1] == 'r':
                    for o in ['soda', 'sprayer', 'virus']:
                        globals()['has_no'][place[:-2]][o] = "RUNNING"
                        globals()['wiped'][place[:-2]][o] = 'SUCCESS'
                globals()['location'] = self.last_task
                return True
        return False

nav = Nav()

class Detection:
    def __init__(self):
        self.input_local_port = yarp.Port()
        input_port_name = '/detection/dets:o'
        local_name = '/local123/test_vis'
        self.input_local_port.open(local_name)
        yarp.Network.connect(input_port_name, local_name)
        time.sleep(1)
        # while True:

    def step(self):
        self.make_vision(self.get_vision())

    def get_vision(self):
        vis = yarp.Bottle()
        self.input_local_port.read(vis)
        res = []
        for i in range(4):
            if vis.get(i).asList() is None:
                break
            box = [vis.get(i).asList().get(j).asDouble() for j in range(4)]
            if box[0] == 0 and box[2] == 0:
                break
            conf = vis.get(i).asList().get(4).asDouble()
            name = vis.get(i).asList().get(5).asString()
            res.append((box, conf, name))
        return res

    FILTER_TIME = 0.4

    def make_vision(self, res):
        t = time.clock()

        if len(res) > 0:
            for box, conf, name in res:
                _objects[name] = {
                    'box': box,
                    't': t
                }
        to_remove = []

        for n, v in _objects.items():
            if t - v['t'] > self.FILTER_TIME:
                to_remove.append(n)
        for k in to_remove:
            print('remove ', k)
            _objects.pop(k)


det = Detection()


class Wiper:
    wipe_traj = {

        'r_shoulder_pitch_point': (0, [6, 6, 43.4, 43.4, 38, ]),
        'r_shoulder_roll_point': (1, [15, 82, 82, 75, 39, ]),
        'r_shoulder_yaw_joint': (2, [-13.59, -13.59, -13.59, -13.59, -13.59, ]),
        'r_elbow_joint': (3, [7.5, 7.5, 7.5, 43.1, 50, ])
    }
    EPS = 1

    def __init__(self):
        self.arm_rpc = yarp.Port()
        arm_rpc_local = '/local123/arm_rpc'
        self.arm_rpc.open(arm_rpc_local)
        output_port_name = '/cer/right_arm/rpc:i'
        yarp.Network.connect(arm_rpc_local, output_port_name)
        self.goal_traj = []
        self.traj_step = None

    def check_if_achieved_point(self, point):
        if isinstance(point, list):
            point = {i: v for i, v in enumerate(point)}

        return all([abs(self.get_enc_joint(joint) - angle) < self.EPS for joint, angle in point.items()])

    def get_current_point(self):
        return [self.get_enc_joint(joint) for joint in range(4)]

    def get_point_from_traj_step(self, i):
        point = {}
        for name, (num, pts) in self.wipe_traj.items():
            point[num] = pts[i]
        return point

    def goto_traj_step(self, i):
        self.goto_point(self.get_point_from_traj_step(i))

    def check_traj_step(self, i):
        return self.check_if_achieved_point(self.get_point_from_traj_step(i))

    def goto_point(self, point):
        if isinstance(point, list):
            point = {i: v for i, v in enumerate(point)}

        for joint, angle in point.items():
            if not self.check_if_achieved_point({joint: angle}):
                self.goto_joint(joint, angle)

    def goto_joint(self, joint, angle):
        cmd = yarp.Bottle()
        reply = yarp.Bottle()
        cmd.addString('set')
        cmd.addString('pos')
        cmd.addInt(joint)
        cmd.addDouble(angle)
        self.arm_rpc.write(cmd, reply)

    def get_enc_joint(self, joint):
        cmd = yarp.Bottle()
        reply = yarp.Bottle()
        cmd.addString('get')
        cmd.addString('enc')
        cmd.addInt(joint)
        self.arm_rpc.write(cmd, reply)
        return reply.get(2).asDouble()

    def traj_follower(self, pose):
        pts = list(reversed(range(5))) if pose == 'normal' else list(range(5))
        self.goal_traj = pts
        self.traj_step = 0
        other_pose = 'wipe' if pose == 'normal' else 'normal'
        self.goto_traj_step(pts[0])

        def fwr():
            if self.check_traj_step(self.goal_traj[self.traj_step]):
                if self.traj_step == len(self.goal_traj) - 1:
                    globals()['r_pose'][pose] = 'SUCCESS'
                    globals()['r_pose'][other_pose] = 'FAILURE'
                    globals()[globals()['__A_return_var']] = True
                    return True
                else:
                    self.traj_step += 1
                    self.goto_traj_step(self.goal_traj[self.traj_step])
                    return False
        return fwr

    def pre_wipe_pose(self):
        for i in range(5):
            self.goto_traj_step(i)
            while not self.check_traj_step(i):
                time.sleep(0.1)

    def post_wipe_pose(self):
        for i in range(4, -1, -1):
            self.goto_traj_step(i)
            while not self.check_traj_step(i):
                time.sleep(0.1)


wiper = Wiper()

def move_closer(object):
    pass


def goto(place):
    print(place)
    nav.goto(place)
    st_time = time.clock()
    _yarp_actions[__A_return_var] = lambda : nav.wait_for_reached(st_time, place)

def put(object):
    globals()[__A_return_var] = True
    globals()['grasped'] = None


def grasp(object):
    globals()[__A_return_var] = True
    globals()['grasped'] = object

def detect(obj):
    print('detect ', obj)
    globals()[__A_return_var] = True
    globals()['seen'][obj] = 'SUCCESS' if obj in _objects else 'FAILURE'


LIGHT_ON_DELAY = 0.5


def light_on(place):
    kitchen_places = [
        'table1',
        'table2'
    ]
    print("LIGHT ON")
    time_now = time.clock()


    def f():
        if (time.clock() - time_now) > LIGHT_ON_DELAY:
            globals()['luminousity'] = 'SUCCESS'
            return True
        else:
            return False
    _yarp_actions[__A_return_var] = f


def detect_on(obj, place):
    print('detect on ', obj, place)
    if globals()["location"] == place:
        print(_objects)
        globals()['has_no'][place][obj] = 'FAILURE' if obj in _objects else 'SUCCESS'
    globals()[__A_return_var] = True


def measure(obj):
    print("measure ", obj)
    if obj not in _objects:
        globals()['close_to_object'][obj] = 'RUNNING'
    else:
        print(_objects[obj])
        box =_objects[obj]['box']
        print(box)
        sq = (box[0] - box[2]) ** 2 + (box[1] - box[3])**2
        globals()['close_to_object'][obj] = 'SUCCESS' if sq < _threshold[obj] else 'FAILURE'
    globals()[__A_return_var] = True


def to_pose(pose):
    print('to pose ', pose)
    _yarp_actions[__A_return_var] = wiper.traj_follower(pose)


def wipe(place):
    goto(place + '_r')


def _yarp_routine():
    nav.step()
    det.step()
    _check_results()


def _check_results():
    to_pop = []
    for var, checker in _yarp_actions.items():
        if checker():
            globals()[var] = "SUCCESS"
            to_pop.append(var)
    for v in to_pop:
        _yarp_actions.pop(v)

test = None
if __name__ == "__main__":
    __A_return_var = 'aazza'
    # to_pose('normal')
    wiper.goto_traj_step(0)
    while len(_yarp_actions) > 0:
        _yarp_routine()
        time.sleep(0.2)
