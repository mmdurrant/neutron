# Copyright (c) 2012 OpenStack Foundation.
# All Rights Reserved.
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

import contextlib
import mock
from oslo import messaging

from neutron.agent import rpc
from neutron.openstack.common import context
from neutron.tests import base


class AgentRPCPluginApi(base.BaseTestCase):
    def _test_rpc_call(self, method):
        agent = rpc.PluginApi('fake_topic')
        ctxt = context.RequestContext('fake_user', 'fake_project')
        expect_val = 'foo'
        with contextlib.nested(
            mock.patch.object(agent.client, 'call'),
            mock.patch.object(agent.client, 'prepare'),
        ) as (
            mock_call, mock_prepare
        ):
            mock_prepare.return_value = agent.client
            mock_call.return_value = expect_val
            func_obj = getattr(agent, method)
            if method == 'tunnel_sync':
                actual_val = func_obj(ctxt, 'fake_tunnel_ip')
            else:
                actual_val = func_obj(ctxt, 'fake_device', 'fake_agent_id')
        self.assertEqual(actual_val, expect_val)

    def test_get_device_details(self):
        self._test_rpc_call('get_device_details')

    def test_get_devices_details_list(self):
        self._test_rpc_call('get_devices_details_list')

    def test_devices_details_list_unsupported(self):
        agent = rpc.PluginApi('fake_topic')
        ctxt = context.RequestContext('fake_user', 'fake_project')
        expect_val_get_device_details = 'foo'
        expect_val = [expect_val_get_device_details]
        with contextlib.nested(
            mock.patch.object(agent.client, 'call'),
            mock.patch.object(agent.client, 'prepare'),
        ) as (
            mock_call, mock_prepare
        ):
            mock_prepare.return_value = agent.client
            mock_call.side_effect = [messaging.UnsupportedVersion('1.2'),
                                    expect_val_get_device_details]
            func_obj = getattr(agent, 'get_devices_details_list')
            actual_val = func_obj(ctxt, ['fake_device'], 'fake_agent_id')
        self.assertEqual(actual_val, expect_val)

    def test_update_device_down(self):
        self._test_rpc_call('update_device_down')

    def test_tunnel_sync(self):
        self._test_rpc_call('tunnel_sync')


class AgentPluginReportState(base.BaseTestCase):
    def test_plugin_report_state_use_call(self):
        topic = 'test'
        reportStateAPI = rpc.PluginReportStateAPI(topic)
        expected_agent_state = {'agent': 'test'}
        with contextlib.nested(
            mock.patch.object(reportStateAPI.client, 'call'),
            mock.patch.object(reportStateAPI.client, 'cast'),
            mock.patch.object(reportStateAPI.client, 'prepare'),
        ) as (
            mock_call, mock_cast, mock_prepare
        ):
            mock_prepare.return_value = reportStateAPI.client
            ctxt = context.RequestContext('fake_user', 'fake_project')
            reportStateAPI.report_state(ctxt, expected_agent_state,
                                        use_call=True)
            self.assertEqual(mock_call.call_args[0][0], ctxt)
            self.assertEqual(mock_call.call_args[0][1], 'report_state')
            self.assertEqual(mock_call.call_args[1]['agent_state'],
                             {'agent_state': expected_agent_state})
            self.assertIsInstance(mock_call.call_args[1]['time'], str)

    def test_plugin_report_state_cast(self):
        topic = 'test'
        reportStateAPI = rpc.PluginReportStateAPI(topic)
        expected_agent_state = {'agent': 'test'}
        with contextlib.nested(
            mock.patch.object(reportStateAPI.client, 'call'),
            mock.patch.object(reportStateAPI.client, 'cast'),
            mock.patch.object(reportStateAPI.client, 'prepare'),
        ) as (
            mock_call, mock_cast, mock_prepare
        ):
            mock_prepare.return_value = reportStateAPI.client
            ctxt = context.RequestContext('fake_user', 'fake_project')
            reportStateAPI.report_state(ctxt, expected_agent_state)
            self.assertEqual(mock_cast.call_args[0][0], ctxt)
            self.assertEqual(mock_cast.call_args[0][1], 'report_state')
            self.assertEqual(mock_cast.call_args[1]['agent_state'],
                             {'agent_state': expected_agent_state})
            self.assertIsInstance(mock_cast.call_args[1]['time'], str)


class AgentRPCMethods(base.BaseTestCase):
    def test_create_consumers(self):
        endpoints = [mock.Mock()]
        expected = [
            mock.call(new=True),
            mock.call().create_consumer('foo-topic-op', endpoints,
                                        fanout=True),
            mock.call().consume_in_threads()
        ]

        call_to_patch = 'neutron.common.rpc.create_connection'
        with mock.patch(call_to_patch) as create_connection:
            rpc.create_consumers(endpoints, 'foo', [('topic', 'op')])
            create_connection.assert_has_calls(expected)

    def test_create_consumers_with_node_name(self):
        endpoints = [mock.Mock()]
        expected = [
            mock.call(new=True),
            mock.call().create_consumer('foo-topic-op', endpoints,
                                        fanout=True),
            mock.call().create_consumer('foo-topic-op.node1', endpoints,
                                        fanout=False),
            mock.call().consume_in_threads()
        ]

        call_to_patch = 'neutron.common.rpc.create_connection'
        with mock.patch(call_to_patch) as create_connection:
            rpc.create_consumers(endpoints, 'foo', [('topic', 'op', 'node1')])
            create_connection.assert_has_calls(expected)
