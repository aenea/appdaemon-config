import appdaemon.plugins.hass.hassapi as hass


# Adjusts the ecobee thermostat according to state

class Climate(hass.Hass):

    def initialize(self):
        self.disabled_modes = [
            item.casefold() for item in self.args['disabled_modes']
        ]
        if 'windows_entity' in self.args:
            self.windows_entity = self.args['windows_entity']
        else:
            self.windows_entity = None

        self.climate_entity = self.args['climate_entity']

        # react to all windows closing
        if self.windows_entity is not None:
            self.listen_state(self.windows_closed, self.windows_entity, new='off')

        # react to a window opening
        if self.windows_entity in not None:
            self.listen_state(self.window_open, self.windows_entity, new='on')

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
            'home_occupancy=%s, '
            'guest_mode=%s, '
            'moonlight=%s, '
            'night_mode=%s, '
            'quiet_mode=%s, '
            'windows_state=%s'
            ')'
            %
            (
                self.home_occupancy,
                self.guest_mode,
                self.moonlight,
                self.night_mode,
                self.quiet_mode,
                self.windows_state
            )
        )

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
    def windows_state(self):
        return self.get_state(self.windows_entity)

    def windows_closed(self, entity, attribute, old, new, kwargs):

        # all the windows have closed - turn the climate control on
        self.call_service(
            'climate/set_operation_mode',
            entity_id='climate.home',
            operation_mode='auto'
        )
        self.log(
            'all windows are closed, climate control set to auto - '
            self.current_state
        )

    def window_open(self, entity, attribute, old, new, kwargs):

        # a window is open - turn the climate control off
        self.call_service(
            'climate/set_operation_mode',
            entity_id='climate.home',
            operation_mode='off'
        )
        self.log(
            'a windows is open - climate control turned off - '
            self.current_state
        )