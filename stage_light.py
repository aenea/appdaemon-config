import appdaemon.plugins.hass.hassapi as hass

#
# StageLight - turns on lights at a dimmed level in adjoinging rooms in
# response to a motion sensor event. This prevents walking into a dark room
# before the target room's motion sensor activates. The target room's lights
# will come # on normally when it's motion sensor activates. Stage lights
# turn off if the # room's motion sensor doesn't trigger after a configurable
# delay
#
# Args:
#
# sensor_entity - The motion sensor in the adjoining room
# actuator_entity - The switch/lights to turn on
# tracking_entity - An input_select variable to track the lighting state of
# the room
# delay - How long to keep the stage lighting on before timing out
# brightness - Lighting level of the stage lighting
#


class StageLight(hass.Hass):

    def initialize(self):
        self.active_modes = [
            item.casefold() for item in self.args['active_modes']
        ]        
        self.actuator = self.args['actuator_entity']
        self.brightness = self.args['brightness']
        self.off_timer = None
        self.run_time_seconds = self.args['delay']
        self.sensor = self.args['sensor_entity']
        self.tracker = self.args['tracking_entity']

        self.listen_state(self.sensor_on, self.sensor, new='on', old='off')

    def sensor_on(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        ).casefold()
        if automation_mode not in self.active_modes:
            return

        # get the state of the switch
        switch_state = self.get_state(
            self.actuator, attribute='state'
        ).casefold()

        # turn on the switch if it is off
        if switch_state == 'off':
            self.turn_on(self.actuator, brightness_pct=self.brightness)

            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='stage_light: ',
                message='{} staged'.format(self.actuator)
            )

            # set the tracking flag
            self.select_option(self.tracker, 'Stage')
        else:
            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='stage_light: ',
                message=(
                    '{} declined staging - already on'.format(self.actuator)
                )
            )

        # cancel any existing timers
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # create a callback to turn off the light
        if self.run_time_seconds > 0:
            self.off_timer = self.run_in(
                self.actuator_off,
                self.run_time_seconds
            )
        else:
            self.actuator_off(self)

    def actuator_off(self, kwargs):

        # cancel any existing timers
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)

        # Remove the timer handle
        self.off_timer = None

        # get the state of the lighting flag
        lighting_state = self.get_state(
            self.tracker,
            attribute='state'
        ).casefold()

        # turn off the light if the state is still 'Stage'
        if lighting_state == 'stage':
            self.turn_off(self.actuator)

            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='stage_light: ',
                message='Stage light for {} turned off'.format(self.actuator)
            )

            # turn off the tracking variable
            self.select_option(self.tracker, 'Off')
        else:
            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='stage_light: ',
                message=(
                    'Stage light for {} not turned off - state has '
                    'changed to {}'.format(self.actuator, lighting_state)
                )
            )
