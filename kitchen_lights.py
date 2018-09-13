import appdaemon.plugins.hass.hassapi as hass


class KitchenLights(hass.Hass):

    def initialize(self):

        self.off_timer = None

        self.listen_state(self.sensor_off, 'group.kitchen_occupancy', new='off')
        self.listen_state(self.sensor_on, 'group.kitchen_occupancy', new='on')
        self.listen_state(self.night_mode_on, 'input_boolean.night_mode', new='on')
        self.listen_state(self.night_mode_on, 'input_boolean.moonlight', new='on')

    @property
    def guest_mode(self):
        return self.get_state('input_boolean.guest_mode')

    @property
    def moonlight(self):
        return self.get_state('input_boolean.moonlight')

    @property
    def home_occupancy(self):
        return self.get_state('input_boolean.home_occupancy')

    @property
    def night_mode(self):
        return self.get_state('input_boolean.night_mode')

    @property
    def quiet_mode(self):
        return self.get_state('input_boolean.quiet_mode')

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
        if 'day' in self.disabled_modes:
            if self.night_mode == 'off':
                self.log(
                    'automation declined for night mode - ' +
                    self.current_state
                )
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
            'guest_mode=%s, '
            'moonlight=%s, '
            'night_mode=%s, '
            'quiet_mode=%s, '
            ')'
            %
            (
                self.guest_mode,
                self.moonlight,
                self.night_mode,
                self.quiet_mode,
            )
        )

    def sensor_off(self, entity, attribute, old, new, kwargs):

        # motion has stopped - wait for 10 minutes
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        self.off_timer = self.run_in(self.turn_off_lights, 600)

    def sensor_on(self, entity, attribute, old, new, kwargs):

        # motion has started - cancel any timers
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

    def night_mode_on(self, entity, attribute, old, new, kwargs):

        # Night mode or moonlight mode has turned on
        # if no timers are active start a timer and then
        # turn off the lights if not cancelled by activity

        if self.off_timer is None:
            self.off_timer = self.run_in(self.turn_off_lights, 600)
        else:
            self.log(
                'kitchen moonlight timer declined timer already active - ' +
                self.current_state
            )

    def turn_off_lights(self, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest', 'away', 'day', 'quiet'])
        if self.allowed_mode is False:
            self.log(
                'kitchen light turn off declined - ' +
                self.current_state
            )
            return

        if self.moonlight == 'off':
            self.turn_off('group.kitchen_lights')

            self.log('kitchen lights turned off - ' + self.current_state)
        else:
            self.call_service(
                'scene.turn_on',
                entity_id='scene.kitchen_moonlight'
            )

            self.log('kitchen lights moonlit - ' + self.current_state)
