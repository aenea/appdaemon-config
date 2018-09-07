import appdaemon.plugins.hass.hassapi as hass


class SensorLight(hass.Hass):

    def initialize(self):
        self.disabled_modes = [
            item.casefold() for item in self.args['disabled_modes']
        ]
        self.sensor = self.args['sensor_entity']
        self.stage_entity = self.args['stage_entity']
        self.actuator = self.args['actuator_entity']
        self.allow_moonlight = self.args['allow_moonlight']
        self.moonlight_pct = self.args['moonlight_pct']
        self.tracker = self.args['tracking_entity']
        self.delay = self.args['delay']
        self.max_run_seconds = self.args['max_run_seconds']
        self.brightness = self.args['brightness']
        self.max_timer = None
        self.off_timer = None

        self.listen_state(self.sensor_on, self.sensor, new='on')
        self.listen_state(self.sensor_off, self.sensor, new='off')
#        if self.stage_entity is not None:
#            self.listen_state(self.stage_sensor_on, self.stage_entity, new='on')
        self.listen_state(self.actuator_off, self.actuator, new='off')

        self.listen_state(
            self.tracker_off,
            self.tracker,
            new='off'
        )
        self.listen_state(
            self.tracker_on,
            self.tracker,
            new='on'
        )
#        self.listen_state(
#            self.tracker_stage,
#            self.tracker,
#            new='stage'
#        )

    @property
    def allowed_mode(self):

        # is the automation mode in an allowed state?
        if 'away' in self.disabled_modes:
            if self.home_occupancy == 'off':
                self.log(
                    'automation declined for occupancy - ' +
                    self.current_state
                )
                return False
        if 'guest' in self.disabled_modes:
            if self.guest_mode == 'on':
                self.log(
                    'automation declined for guest mode - ' +
                    self.current_state
                )
                return False
        if 'quiet' in self.disabled_modes:
            if self.quiet_mode == 'on':
                self.log(
                    'automation declined for quiet mode - ' +
                    self.current_state
                )
                return False

        return True

    @property
    def current_state(self):

        return (
            'current_state('
            'actuator_value=%s, '
            'home_occupancy=%s, '
            'guest_mode=%s, '
            'moonlight=%s, '
            'night_mode=%s, '
            'quiet_mode=%s, '
            'tracker_value=%s, '
            ')'
            %
            (
                self.actuator_value,
                self.home_occupancy,
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
    def home_occupancy(self):
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

    def actuator_off(self, entity, attribute, old, new, kwargs):

        # if the light was turned off manually, turn off the tracker
        if self.tracker_value != 'off':
            self.select_option(self.tracker, 'off')
            self.log(
                self.actuator +
                ' turned off manually - ' +
                self.current_state
            )

        # cancel any existing timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
            self.max_timer = None

        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

    def sensor_off(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        if self.allowed_mode is False:
            return

        if self.delay > 0:
            self.off_timer = self.run_in(
                self.turn_off_tracker,
                self.delay
            )
            self.log('sensor off delay timer started - ' + self.current_state)
        else:
            self.select_option(self.tracker, 'off')
            self.log('sensor off - ' + self.current_state)

    def sensor_on(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        if self.allowed_mode is False:
            return

        # cancel any existing timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
            self.max_timer = None

        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # turn on the tracking flag
        self.select_option(self.tracker, 'on')
        self.log('sensor on - ' + self.current_state)

    def stage_sensor_on(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        if self.allowed_mode is False:
            self.log(
                'stage declined for automation mode ' +
                self.current_state
            )
            return

        if self.tracker_value != 'off' or self.tracker != 'stage':
            self.log('stage declined for lighting mode ' + self.current_state)
            return

        # cancel any existing timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
            self.max_timer = None

        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # turn on the tracking flag
        self.select_option(self.tracker, 'stage')
        self.log('stage sensor on - ' + self.current_state)

    def tracker_off(self, entity, attribute, old, new, kwargs):

        if self.allow_moonlight is True and self.moonlight == 'on':
            self.turn_on(self.actuator, brightness_pct=self.moonlight_pct)
            self.log(self.actuator + ' moonlit - ' + self.current_state)
        else:
            self.turn_off(self.actuator)

    def tracker_on(self, entity, attribute, old, new, kwargs):

        if self.brightness is None:
            self.turn_on(self.actuator)
        else:
            self.turn_on(self.actuator, brightness_pct=self.brightness)

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
                self.turn_off_tracker,
                self.max_run_seconds
            )

    def tracker_stage(self, entity, attribute, old, new, kwargs):

        if self.brightness is None:
            self.turn_on(self.actuator)
        else:
            self.turn_on(self.actuator, brightness_pct=self.moonlight_pct)

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
                self.turn_off_tracker,
                self.max_run_seconds
            )

    def turn_off_tracker(self, kwargs):

        # wrapper function for the turn off call backs
        self.select_option(self.tracker, 'off')
        self.log('light turned off by time out - ' + self.current_state)
