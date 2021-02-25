import logging
import json

from ops.framework import (
    StoredState,
    EventBase,
    ObjectEvents,
    EventSource,
    Object
)

MANILA_DIR = '/etc/manila/'
MANILA_CONF = MANILA_DIR + 'manila.conf'


logger = logging.getLogger(__name__)


class ManilaPluginReadyEvent(EventBase):
    pass


class ManilaPluginEvents(ObjectEvents):
    manila_plugin_ready = EventSource(ManilaPluginReadyEvent)


class ManilaPluginProvides(Object):

    on = ManilaPluginEvents()
    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self.this_unit = self.model.unit
        self.relation_name = relation_name
        self.state.set_default(
            authentication_data={})
        self.framework.observe(
            charm.on[relation_name].relation_changed,
            self.on_changed)

    def on_changed(self, event):
        logging.info("relation manila-plugin on_changed")
        rel_data = event.relation.data.get(event.unit)
        if not rel_data:
            return
        auth_data = rel_data.get('_authentication_data')
        if auth_data:
            logger.info("relation manila-plugin is ready")
            self.state.authentication_data = json.loads(auth_data).get("data")
            self.on.manila_plugin_ready.emit()

    def send_backend_config(self, share_backend_name, rendered_configs):
        logging.info("Sending manila backend config")
        # This seems to be the relation variables format expected by the
        # remote reactive Manila charm.
        self.manila_plugin_rel.data[self.this_unit][
            '_name'] = share_backend_name
        self.manila_plugin_rel.data[self.this_unit][
            "_configuration_data"] = json.dumps(
                {"data": {MANILA_CONF: rendered_configs}})

    @property
    def authentication_data(self):
        return self.state.authentication_data

    @property
    def manila_plugin_rel(self):
        return self.model.get_relation(self.relation_name)
