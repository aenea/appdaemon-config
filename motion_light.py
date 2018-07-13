import appdaemon.plugins.hass.hassapi as hass


# Turns on lights in response to a motion sensor. The light turns off
# if the motion doesn't re-trigger within normal_run_seconds or after
# max_run_seconds. The light is dimmed for 30 seconds as a warning
# before the light is turned off

class MotionLight(hass.Hass):

    def initialize(self):
        self.active_modes = [
            item.casefold() for item in self.args['active_modes']
        ]        
        self.actuator = self.args['actuator_entity']
        self.brightness = self.args['brightness']
        self.normal_run_seconds = self.args['normal_run_seconds']
        self.max_run_seconds = self.args['max_run_seconds']
        self.max_timer = None
        self.off_timer = None
        self.sensor = self.args['sensor_entity']
        self.tracker = self.args['tracking_entity']

        self.listen_state(self.sensor_on, self.sensor, new='on')
        self.listen_state(
            self.actuator_off,
            self.actuator,
            old='on',
            new='off'
        )
        self.listen_state(
            self.actuator_on,
            self.actuator,
            old='off',
            new='on'
        )

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
            self.actuator, 
            attribute='state'
        ).casefold()

        # get the state of the lighting flag
        lighting_state = self.get_state(
            self.tracker,
            attribute='state'
        ).casefold()

        # turn on the light if it is not fully on
        if (switch_state == 'off' or lighting_state == 'stage' or
                lighting_state == 'warning'):

            # turn lighting state tracking flag to Automated
            self.select_option(self.tracker, 'Automated')

            if self.brightness is None:
                self.turn_on(self.actuator)
            else:
                self.turn_on(self.actuator, brightness_pct=self.brightness)

            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='motion_light: ',
                message='{} turned on'.format(self.actuator)
            )

        # cancel any existing timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
            self.max_timer = None
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # reset the max run and off timers
        if self.max_run_seconds > 0:
            self.max_timer = self.run_in(
                self.turn_off_warning,
                self.max_run_seconds
            )
        if self.normal_run_seconds > 0:
            self.off_timer = self.run_in(
                self.turn_off_warning,
                self.normal_run_seconds
            )

    def turn_off_warning(self, kwargs):

        # get the state of the lighting tracking flag
        lighting_state = self.get_state(
            self.tracker, 
            attribute='state'
        ).casefold()

        if lighting_state == 'automated':
            self.select_option(self.tracker, 'Warning')

            # dim the lights to warn about an impending turn off
            current_brightness = self.get_state(
                self.actuator,
                attribute='brightness'
            )
            self.turn_on(
                self.actuator,
                brightness=int(current_brightness * .4)
            )

            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='motion_light: ',
                message='{} dimmed by turn off warning'.format(self.actuator)
            )

            # schedule the final turn off
            self.off_timer = self.run_in(self.turn_off_actuator, 30)

    def turn_off_actuator(self, kwargs):

        lighting_state = self.get_state(
            self.tracker,
            attribute='state'
        ).casefold()

        # turn off the light if it was turned on by automation
        if lighting_state != 'manual':
            self.turn_off(self.actuator)

    def actuator_off(self, entity, attribute, old, new, kwargs):

        # cancel any remaining timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)

        # clear the timer handles
        self.max_timer = None
        self.off_timer = None

        self.call_service(
            'logbook/log',
            entity_id=self.actuator,
            domain='automation',
            name='motion_light: ',
            message='{} turned off'.format(self.actuator)
        )

        # turn off the tracking variable
        self.select_option(self.tracker, 'Off')

    def actuator_on(self, entity, attribute, old, new, kwargs):

        lighting_state = self.get_state(
            self.tracker,
            attribute='state'
        ).casefold()

        if lighting_state == 'off':
            self.select_option(self.tracker, 'Manual')
