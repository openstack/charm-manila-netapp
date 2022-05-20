import copy
import json
import sys

sys.path.append('lib')  # noqa
sys.path.append('src')  # noqa

from unittest import (
    mock,
    TestCase,
)
from ops.model import ActiveStatus, BlockedStatus, UnknownStatus
from ops.testing import Harness

import charm


class TestManilaNetappCharm(TestCase):

    REQUIRED_CHARM_CONFIG_BY_DEFAULT = {
        'management-address': '10.0.0.1',
        'admin-password': 'my-secret-password',
        'vserver-name': 'svm0',
    }

    def setUp(self):
        self.harness = Harness(charm.ManilaNetappCharm)
        self.addCleanup(self.harness.cleanup)

    def test_custom_status_check_default_config(self):
        self.harness.disable_hooks()
        self.harness.begin()

        self.assertFalse(self.harness.charm.custom_status_check())
        expected_status = BlockedStatus('Missing configs: {}'.format(
            list(self.REQUIRED_CHARM_CONFIG_BY_DEFAULT.keys())))
        self.assertEqual(self.harness.charm.unit.status, expected_status)

    def test_custom_status_check_valid_config(self):
        self.harness.update_config(self.REQUIRED_CHARM_CONFIG_BY_DEFAULT)
        self.harness.disable_hooks()
        self.harness.begin()

        self.assertTrue(self.harness.charm.custom_status_check())

    @mock.patch.object(
        charm.ops_openstack.core.OSBaseCharm,
        'install_pkgs')
    @mock.patch.object(
        charm.interface_manila_plugin.ManilaPluginProvides,
        'send_backend_config')
    @mock.patch('charmhelpers.contrib.openstack.templating.get_loader')
    @mock.patch('charmhelpers.core.templating.render')
    def test_send_config_dhss_disabled(self, _render, _get_loader,
                                       _send_backend_config, _install_pkgs):
        _render.return_value = 'test-rendered-manila-backend-config'
        _get_loader.return_value = 'test-loader'
        self.harness.update_config(self.REQUIRED_CHARM_CONFIG_BY_DEFAULT)
        rel_id = self.harness.add_relation('manila-plugin', 'manila')
        self.harness.add_relation_unit(rel_id, 'manila/0')
        self.harness.begin_with_initial_hooks()

        self.assertTrue(self.harness.charm.state.is_started)
        _render.assert_called_once_with(
            source='manila.conf',
            template_loader='test-loader',
            target=None,
            context=self.harness.charm.adapters)
        _get_loader.assert_called_once_with(
            'templates/', 'default')
        _send_backend_config.assert_called_once_with(
            'netapp-ontap', 'test-rendered-manila-backend-config')
        _install_pkgs.assert_called_once_with()
        self.assertEqual(
            self.harness.charm.unit.status, ActiveStatus('Unit is ready'))

    @mock.patch.object(
        charm.ops_openstack.core.OSBaseCharm,
        'install_pkgs')
    @mock.patch.object(
        charm.interface_manila_plugin.ManilaPluginProvides,
        'send_backend_config')
    @mock.patch('charmhelpers.contrib.openstack.templating.get_loader')
    @mock.patch('charmhelpers.core.templating.render')
    def test_send_config_dhss_enabled(self, _render, _get_loader,
                                      _send_backend_config, _install_pkgs):
        _render.return_value = 'test-rendered-manila-backend-config'
        _get_loader.return_value = 'test-loader'
        config = copy.deepcopy(self.REQUIRED_CHARM_CONFIG_BY_DEFAULT)
        config['driver-handles-share-servers'] = True
        config['root-volume-aggregate-name'] = 'test_cluster_01_VM_DISK_1'
        self.harness.update_config(config)
        self.harness.begin_with_initial_hooks()

        # Validate workflow with incomplete relation data
        self.assertFalse(self.harness.charm.state.is_started)
        _render.assert_not_called()
        _get_loader.assert_not_called()
        _send_backend_config.assert_not_called()
        _install_pkgs.assert_called_once_with()
        self.assertEqual(self.harness.charm.unit.status, UnknownStatus())

        # Validate workflow with complete relation data
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
        self.assertTrue(self.harness.charm.state.is_started)
        _render.assert_called_once_with(
            source='manila.conf',
            template_loader='test-loader',
            target=None,
            context=self.harness.charm.adapters)
        _get_loader.assert_called_once_with(
            'templates/', 'default')
        _send_backend_config.assert_called_once_with(
            'netapp-ontap', 'test-rendered-manila-backend-config')
        self.assertEqual(
            self.harness.charm.unit.status, ActiveStatus('Unit is ready'))
