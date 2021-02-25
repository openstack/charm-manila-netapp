#!/usr/bin/env python3

import logging
import os

from ops.main import main
import ops.model

import ops_openstack.adapters
import ops_openstack.core

import charmhelpers.core.templating as ch_templating
import charmhelpers.contrib.openstack.templating as os_templating

import interface_manila_plugin


logger = logging.getLogger(__name__)


class ManilaPluginAdapter(ops_openstack.adapters.OpenStackOperRelationAdapter):

    def __init__(self, relation):
        super(ManilaPluginAdapter, self).__init__(relation)


class ManilaNetappAdapters(ops_openstack.adapters.OpenStackRelationAdapters):

    relation_adapters = {
        'options': ops_openstack.adapters.ConfigurationAdapter,
        'manila-plugin': ManilaPluginAdapter,
    }


class ManilaNetappCharm(ops_openstack.core.OSBaseCharm):

    REQUIRED_RELATIONS = ['manila-plugin']

    release = 'default'

    def __init__(self, framework):
        super().__init__(framework)
        logging.info("Using {} class".format(self.release))
        self.manila_plugin = interface_manila_plugin.ManilaPluginProvides(
            self,
            'manila-plugin')
        self.options = ops_openstack.adapters.ConfigurationAdapter(
            self)
        self.adapters = ManilaNetappAdapters(
            [self.manila_plugin],
            self,
            self.options)
        self.framework.observe(
            self.on.config_changed,
            self.send_config)
        self.framework.observe(
            self.manila_plugin.on.manila_plugin_ready,
            self.send_config)

    def send_config(self, event):
        if not self.custom_status_check():
            return
        if self.options.driver_handles_share_servers:
            if not self.manila_plugin.authentication_data:
                logging.warning(
                    "Manila plugin authentication_data is required when "
                    "'driver-handles-share-servers' config is enabled.")
                event.defer()
                return
        rendered_configs = ch_templating.render(
            source=os.path.basename(interface_manila_plugin.MANILA_CONF),
            template_loader=os_templating.get_loader(
                'templates/', self.release),
            target=None,
            context=self.adapters)
        self.manila_plugin.send_backend_config(
            self.options.share_backend_name, rendered_configs)
        self.state.is_started = True
        self.update_status()

    def custom_status_check(self):
        required_configs = [
            'share-backend-name',
            'management-address',
            'admin-name',
            'admin-password']
        if self.options.driver_handles_share_servers:
            required_configs.append('root-volume-aggregate-name')
        else:
            required_configs.append('vserver-name')
        missing_configs = []
        for config in required_configs:
            if not self.model.config.get(config):
                missing_configs.append(config)
        if len(missing_configs) > 0:
            msg = 'Missing configs: {}'.format(missing_configs)
            logger.warning(msg)
            self.unit.status = ops.model.BlockedStatus(msg)
            return False
        return True


if __name__ == '__main__':
    main(ManilaNetappCharm)
