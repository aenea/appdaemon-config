import appdaemon.plugins.hass.hassapi as hass


class SensorLight(hass.Hass):

    def initialize(self):
        self.disabled_modes = [
            item.casefold() for item in self.args['disabled_modes']
        ]
        self.sensor = self.args['sensor_entity']
        self.actuator = self.args['actuator_entity']
        self.tracker = self.args['tracking_entity']
        self.delay = self.args['delay']
        self.max_run_seconds = self.args['max_run_seconds']
        self.brightness = self.args['brightness']
        self.max_timer = None
        self.off_timer = None

        self.listen_state(self.sensor_on, self.sensor, new='on')
        self.listen_state(self.sensor_off, self.sensor, new='off')
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

    def current_state(self):

        return (
            'current_state('
            'actuator_value=%s, '
            'away_mode=%s, '
            'guest_mode=%s, '
            'moonlight=%s, '
            'night_mode=%s, '
            'quiet_mode=%s, '
            'tracker_value=%s, '
            ')'
            %
            (
                self.actuator_value,
                self.away_mode,
                self.guest_mode,
                self.moonlight,
                self.night_mode,
                self.quiet_mode,
                self.tracker_value
            )
        )

    @property
    def actuator_value(self):
        return self.get_state(self.actuator)

    @property
    def away_mode(self):
        return self.get_state('input_boolean.home_occupancy')

    @property
    def guest_mode(self):
        return self.get_state('input_boolean.guest_mode')

    @property
    def moonlight(self):
        return self.get_state('input_boolean.moonlight')

    @property
    def night_mode(self):
        return self.get_state('input_boolean.night_mode')

    @property
    def quiet_mode(self):
        return self.get_state('input_boolean.quiet_mode')

    @property
    def tracker_value(self):
        return self.get_state(self.tracker)

    def sensor_on(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        if 'away' in self.disabled_modes:
            if self.get_state(input_boolean.home_occupancy) == 'off':
                return
        if 'guest' in self.disabled_modes:
            if self.get_state(input_boolean.guest_mode) == 'on':
                return
        if 'quiet' in self.disabled_modes:
            if self.get_state(input_boolean.quiet_mode) == 'on':
                return

        # get the state of the switch
        switch_state = self.get_state(self.actuator, attribute='state')

        # get the state of the tracking flag
        lighting_state = self.get_state(self.tracker, attribute='state')

        # turn on the light if it is not fully on
        if (switch_state == 'off' or lighting_state == 'Stage' or
                lighting_state == 'Warning'):

            # turn on the automation tracking flag
            self.select_option(self.tracker, 'Automated')

            if self.brightness is None:
                self.turn_on(self.actuator)
            else:
                self.turn_on(self.actuator, brightness_pct=self.brightness)

            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='sensor_light: ',
                message='{} turned on'.format(self.actuator)
            )

        # cancel any existing timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
            self.max_timer = None

        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # set a timer to turn off the light after max_run_seconds
        if self.max_run_seconds > 0:
            self.max_timer = self.run_in(
                self.turn_off_actuator,
                self.max_run_seconds
            )
            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='sensor_light: ',
                message='{} scheduled for turn off in {} seconds'.format(
                    self.actuator,
                    self.max_run_seconds
                )
            )

    def sensor_off(self, entity, attribute, old, new, kwargs):

        # check for guest mode
        guest_mode = self.get_state(
            'input_boolean.guest_mode',
            attribute='state'
        )
        if guest_mode is True:
            return

        if self.delay > 0:
            self.off_timer = self.run_in(
                self.turn_off_actuator,
                self.delay
            )
        else:
            self.turn_off_actuator(self)

    def turn_off_warning(self, kwargs):

        # get the state of the lighting flag
        lighting_state = self.get_state(self.tracker, attribute='state')

        if lighting_state == 'Automated':
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
                name='sensor_light: ',
                message='{} dimmed by turn off warning'.format(self.actuator)
            )

            # schedule the final turn off
            self.off_timer = self.run_in(self.turn_off_actuator, 30)

    def turn_off_actuator(self, kwargs):

        lighting_state = self.get_state(
            self.tracker,
            attribute='state'
        )
        # if self.brightness is not None and lighting_state == 'Automated':
        #    self.turn_off_warning()

        # turn off the light if it was turned on by automation
        if lighting_state != 'Manual':
            self.turn_off(self.actuator)

    def actuator_off(self, entity, attribute, old, new, kwargs):

        # check for guest mode
        guest_mode = self.get_state(
            'input_boolean.guest_mode',
            attribute='state'
        )
        if guest_mode is True:
            return

        # clear the timer handles
        self.max_timer = None
        self.off_timer = None

        self.call_service(
            'logbook/log',
            entity_id=self.actuator,
            domain='automation',
            name='sensor_light: ',
            message='{} turned off'.format(self.actuator)
        )

        # turn off the tracking variable
        self.select_option(self.tracker, 'Off')

    def actuator_on(self, entity, attribute, old, new, kwargs):

        lighting_state = self.get_state(
            self.tracker,
            attribute='state'
        )

        if lighting_state == 'Off':
            self.select_option(self.tracker, 'Manual')
