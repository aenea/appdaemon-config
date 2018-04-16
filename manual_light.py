import appdaemon.plugins.hass.hassapi as hass


class ManualLight(hass.Hass):

    def initialize(self):

        self.actuator = self.args['actuator_entity']
        self.max_run_time = self.args['max_run_time']
        self.tracking_entity = self.args['tracking_entity']
        self.off_timer = None

        self.listen_state(self.actuator_on, self.actuator, new='on')
        self.listen_state(self.actuator_off, self.actuator, new='off')

    def actuator_on(self, entity, attribute, old, new, kwargs):

        # get the current state of the entity
        entity_state = self.get_state(self.tracking_entity, attribute='state')

        if entity_state == 'Automated':
            # start a timer to turn off the light
            self.off_timer = self.run_in(
                self.turn_off_actuator,
                self.max_run_time
            )

    def actuator_off(self, entity, attribute, old, new, kwargs):

        # clear the status flag
        self.select_option(self.tracking_entity, 'Off')

    def turn_off_actuator(self, kwargs):

        # get the current state of the entity
        entity_state = self.get_state(self.tracking_entity, attribute='state')

        if entity_state == 'Automated':
            # turn off the actuator
            self.turn_off(self.actuator)

        # cancel any pending timers
        self.cancel_timer(self.off_timer)
        self.off_timer = None
