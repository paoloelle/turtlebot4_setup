#!/usr/bin/env python3
# Copyright 2022 Clearpath Robotics, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @author Roni Kreinin (rkreinin@clearpathrobotics.com)

import argparse

import sys

import robot_upstart


parser = argparse.ArgumentParser()

parser.add_argument('--domain', type=int, default=0)
parser.add_argument('--rmw', type=str, default='rmw_cyclonedds_cpp')
parser.add_argument('--workspace', type=str, default='/opt/ros/galactic/setup.bash')
parser.add_argument('--discovery', type=str, default='off')

args = parser.parse_args()

model = 'standard'

try:
    with open('/etc/turtlebot4') as f:
        info = f.readline()
        if 'lite' in info:
            model = 'lite'
except FileNotFoundError:
    pass


domain_id = 0
if (args.domain >= 0 and args.domain <= 101) or \
   (args.domain >= 215 and args.domain <= 232):
    domain_id = args.domain
else:
    print('Invalid ROS_DOMAIN_ID: {0}'.format(args.domain))
    parser.print_help()
    sys.exit(2)

rmw = 'rmw_cyclonedds_cpp'
if args.rmw == 'rmw_fastrtps_cpp' or args.rmw == 'rmw_cyclonedds_cpp':
    rmw = args.rmw
else:
    print('Invalid RMW {0}'.format(args.rmw))
    parser.print_help()
    sys.exit(3)

workspace = args.workspace

discovery = 'off'
if args.discovery == 'off' or args.discovery == 'on':
    if args.discovery == 'on':
        rmw = 'rmw_fastrtps_cpp'
        discovery = 'on'
else:
    print('Invalid Discovery state {0}'.format(args.discovery))
    parser.print_help()
    sys.exit(4)

print('Installing TurtleBot 4 {0}. ROS_DOMAIN_ID={1}, RMW_IMPLEMENTATION={2}'.format(model, domain_id, rmw))

if rmw == 'rmw_cyclonedds_cpp':
    rmw_config = '/etc/cyclonedds_rpi.xml'
else:
    rmw_config = None

turtlebot4_job = robot_upstart.Job(name='turtlebot4',
                                   rmw=rmw,
                                   rmw_config=rmw_config,
                                   workspace_setup=workspace,
                                   ros_domain_id=domain_id)

turtlebot4_job.symlink = True
turtlebot4_job.add(package='turtlebot4_bringup', filename='launch/{0}.launch.py'.format(model))
turtlebot4_job.install()


class TurtleBot4Extras(robot_upstart.providers.Generic):
    def post_install(self):
        pass

    def generate_install(self):
        with open('/etc/turtlebot4_discovery/discovery.conf') as f:
            discovery_conf_contents = f.read()
        with open('/etc/turtlebot4_discovery/discovery.sh') as f:
            discovery_sh_contents = f.read()
        return {
            "/lib/systemd/system/discovery.service": {
                "content": discovery_conf_contents,
                "mode": 0o644
            },
            "/usr/sbin/discovery": {
                "content": discovery_sh_contents,
                "mode": 0o755
            },
            "/etc/systemd/system/multi-user.target.wants/discovery.service": {
                "symlink": "/lib/systemd/system/discovery.service"
            }}


if discovery == 'on':
    discovery_job = robot_upstart.Job(workspace_setup=workspace)
    discovery_job.install(Provider=TurtleBot4Extras)
