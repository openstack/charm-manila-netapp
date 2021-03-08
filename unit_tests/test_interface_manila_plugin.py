import json
import sys

sys.path.append('lib')  # noqa
sys.path.append('src')  # noqa

from unittest import (
    TestCase,
)

from ops.framework import Object
from ops.charm import CharmBase
from ops.testing import Harness

import interface_manila_plugin


class TestReceiver(Object):

    def __init__(self, parent, key):
        super().__init__(parent, key)
        self.observed_events = []

    def on_manila_plugin_ready(self, event):
        self.observed_events.append(event)


class TestManilaPluginProvides(TestCase):

    def setUp(self):
        self.harness = Harness(CharmBase, meta='''
            name: manila-netapp
            provides:
              manila-plugin:
                interface: manila-plugin
                scope: container
        ''')
        self.addCleanup(self.harness.cleanup)

    def test_on_changed(self):
        self.harness.begin()
        self.harness.charm.manila_plugin = \
            interface_manila_plugin.ManilaPluginProvides(
                self.harness.charm,
                'manila-plugin')
        receiver = TestReceiver(self.harness.framework, 'receiver')
        self.harness.framework.observe(
            self.harness.charm.manila_plugin.on.manila_plugin_ready,
            receiver.on_manila_plugin_ready)
        rel_id = self.harness.add_relation('manila-plugin', 'manila')
        self.harness.add_relation_unit(rel_id, 'manila/0')
        self.harness.update_relation_data(
            rel_id,
            'manila/0',
            {
                '_authentication_data': json.dumps({
                    'data': 'test-manila-auth-data'
                })
            })

        self.assertEqual(
            self.harness.charm.manila_plugin.authentication_data,
            'test-manila-auth-data')
        self.assertEqual(len(receiver.observed_events), 1)
        self.assertIsInstance(
            receiver.observed_events[0],
            interface_manila_plugin.ManilaPluginReadyEvent)

    def test_send_backend_config(self):
        self.harness.begin()
        self.harness.charm.manila_plugin = \
            interface_manila_plugin.ManilaPluginProvides(
                self.harness.charm,
                'manila-plugin')
        rel_id = self.harness.add_relation('manila-plugin', 'manila')
        self.harness.add_relation_unit(rel_id, 'manila/0')
        self.harness.update_relation_data(
            rel_id,
            'manila/0',
            {
                '_authentication_data': json.dumps({
                    'data': 'test-manila-auth-data'
                })
            })

        self.harness.charm.manila_plugin.send_backend_config(
            'test-backend-name', 'test-rendered-configs')
        rel_unit_data = self.harness.get_relation_data(
            rel_id, self.harness.charm.manila_plugin.this_unit.name)
        self.assertEqual(
            rel_unit_data.get('_name'), 'test-backend-name')
        expected_data = {
            'data': {
                interface_manila_plugin.MANILA_CONF: 'test-rendered-configs'
            }
        }
        self.assertEqual(
            rel_unit_data.get('_configuration_data'),
            json.dumps(expected_data))
