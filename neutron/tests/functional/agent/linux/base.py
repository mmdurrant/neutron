# Copyright 2014 Cisco Systems, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import random

from neutron.agent.linux import ip_lib
from neutron.agent.linux import ovs_lib
from neutron.agent.linux import utils
from neutron.common import constants as n_const
from neutron.openstack.common import uuidutils
from neutron.tests.functional.agent.linux import pinger
from neutron.tests.functional import base as functional_base


BR_PREFIX = 'test-br'
ICMP_BLOCK_RULE = '-p icmp -j DROP'
VETH_PREFIX = 'tst-vth'


#TODO(jschwarz): Move these two functions to neutron/tests/common/
def get_rand_name(max_length=None, prefix='test'):
    name = prefix + str(random.randint(1, 0x7fffffff))
    return name[:max_length] if max_length is not None else name


def get_rand_veth_name():
    return get_rand_name(max_length=n_const.DEVICE_NAME_MAX_LEN,
                         prefix=VETH_PREFIX)


class BaseLinuxTestCase(functional_base.BaseSudoTestCase):

    def check_command(self, cmd, error_text, skip_msg, root_helper=None):
        try:
            utils.execute(cmd, root_helper=root_helper)
        except RuntimeError as e:
            if error_text in str(e) and not self.fail_on_missing_deps:
                self.skipTest(skip_msg)
            raise

    def create_resource(self, name_prefix, creation_func, *args, **kwargs):
        """Create a new resource that does not already exist.

        :param name_prefix: The prefix for a randomly generated name
        :param creation_func: A function taking the name of the resource
               to be created as it's first argument.  An error is assumed
               to indicate a name collision.
        :param *args *kwargs: These will be passed to the create function.
        """
        while True:
            name = get_rand_name(max_length=n_const.DEVICE_NAME_MAX_LEN,
                                 prefix=name_prefix)
            try:
                return creation_func(name, *args, **kwargs)
            except RuntimeError:
                continue

    def create_veth(self):
        ip_wrapper = ip_lib.IPWrapper(self.root_helper)
        name1 = get_rand_veth_name()
        name2 = get_rand_veth_name()
        self.addCleanup(ip_wrapper.del_veth, name1)
        veth1, veth2 = ip_wrapper.add_veth(name1, name2)
        return veth1, veth2


class BaseOVSLinuxTestCase(BaseLinuxTestCase):
    def setUp(self):
        super(BaseOVSLinuxTestCase, self).setUp()
        self.ovs = ovs_lib.BaseOVS(self.root_helper)

    def create_ovs_bridge(self, br_prefix=BR_PREFIX):
        br = self.create_resource(br_prefix, self.ovs.add_bridge)
        self.addCleanup(br.destroy)
        return br

    def get_ovs_bridge(self, br_name):
        return ovs_lib.OVSBridge(br_name, self.root_helper)


class BaseIPVethTestCase(BaseLinuxTestCase):
    SRC_ADDRESS = '192.168.0.1'
    DST_ADDRESS = '192.168.0.2'
    BROADCAST_ADDRESS = '192.168.0.255'

    def setUp(self):
        super(BaseIPVethTestCase, self).setUp()
        self.check_sudo_enabled()
        self.pinger = pinger.Pinger(self)

    @staticmethod
    def _set_ip_up(device, cidr, broadcast, ip_version=4):
        device.addr.add(ip_version=ip_version, cidr=cidr, broadcast=broadcast)
        device.link.set_up()

    def _create_namespace(self):
        ip_cmd = ip_lib.IPWrapper(self.root_helper)
        name = "func-%s" % uuidutils.generate_uuid()
        namespace = ip_cmd.ensure_namespace(name)
        self.addCleanup(namespace.netns.delete, namespace.namespace)

        return namespace

    def prepare_veth_pairs(self, src_addr=None,
                           dst_addr=None,
                           broadcast_addr=None,
                           src_ns=None, dst_ns=None,
                           src_veth=None,
                           dst_veth=None):

        src_addr = src_addr or self.SRC_ADDRESS
        dst_addr = dst_addr or self.DST_ADDRESS
        broadcast_addr = broadcast_addr or self.BROADCAST_ADDRESS
        src_veth = src_veth or get_rand_veth_name()
        dst_veth = dst_veth or get_rand_veth_name()
        src_ns = src_ns or self._create_namespace()
        dst_ns = dst_ns or self._create_namespace()

        src_veth, dst_veth = src_ns.add_veth(src_veth,
                                             dst_veth,
                                             dst_ns.namespace)

        self._set_ip_up(src_veth, '%s/24' % src_addr, broadcast_addr)
        self._set_ip_up(dst_veth, '%s/24' % dst_addr, broadcast_addr)

        return src_ns, dst_ns
