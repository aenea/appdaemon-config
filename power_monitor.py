import appdaemon.plugins.hass.hassapi as hass

class PowerMonitor(hass.Hass):

    def initialize(self):

        self.max_idle_seconds = self.args['max_idle_seconds']
        self.off_load = self.args['off_load']
        self.on_load = self.args['on_load']
        self.sensor_entity = self.args['sensor_entity']
        self.tracking_entity = self.args['tracking_entity']
        self.idle_timer = None

        self.listen_state(self.sensor_report, self.sensor_entity)

    def sensor_report(self, entity, attribute, old, new, kwargs):

        # get the current state of the entity
        entity_state = self.get_state(self.tracking_entity, attribute='state')
        self.log("power {}, state {}".format(new, entity_state), level='INFO')
        
        if float(new) <= self.off_load and entity_state == 'Running':
            self.log("Idle", level='INFO')
            self.log("{} timer".format(self.idle_timer), level='INFO')

            # start an idle timer if one is not already running
            if self.idle_timer is None:
                self.log("Starting timer")
                self.idle_timer = self.run_in(self.entity_idle, self.max_idle_seconds)
        
        elif float(new) >= self.on_load and entity_state == 'Idle':
            # mark the entity as running
            self.select_option(self.tracking_entity, 'Running')

            # cancel any running idle timers
            if self.idle_timer is not None:
                self.cancel_timer(self.idle_timer)

            self.log("{} is running.".format(self.sensor_entity), level='INFO')

    def entity_idle(self, kwargs):

        # get the current state of the entity
        entity_state = self.get_state(self.tracking_entity, attribute='state')

        if entity_state is not 'Idle':
            # mark the entity as idle
            self.select_option(self.tracking_entity, 'Idle')

            self.log("{} is running.".format(self.sensor_entity), level='INFO')

                