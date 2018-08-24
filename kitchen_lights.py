import appdaemon.plugins.hass.hassapi as hass


class KitchenLights(hass.Hass):

    def initialize(self):

        self.off_timer = None

        self.listen_state(
            self.sensor_off,
            'group.kitchen_occupancy',
            new='off'
        )
        self.listen_state(
            self.sensor_on,
            'group.kitchen_occupancy',
            new='on'
        )
        self.listen_state(
            self.night_mode_on,
            'input_boolean.night_mode',
            new='on'
        )
        self.listen_state(
            self.night_mode_on,
            'input_boolean.moonlight',
            new='on'
        )

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

    def night_mode_on(self, kwargs):

        # Night mode or moonlight mode has turned on
        # if no timers are active start a timer and then
        # turn off the lights if not cancelled by activity

        if self.off_timer is None:
            self.off_timer = self.run_in(self.turn_off_lights, 600)

    def turn_off_lights(self, kwargs):

        if self.night_mode == 'off':
            return
        if self.guest_mode == 'on':
            return
        if self.quiet_mode == 'on':
            return

        if self.moonlight == 'off':
            self.turn_off('group.kitchen_lights')

            self.log('kitchen lights turned off' + self.current_state)
        else:
            self.turn_off('group.kitchen_lights_moonlight_off')
            self.turn_on(
                "group.kitchen_lights_moonlight",
                brightness_pct=10,
                transition=20
            )

            self.log('kitchen lights moonlit' + self.current_state)
