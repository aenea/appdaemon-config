import appdaemon.plugins.hass.hassapi as hass


# Uses the Bond IFTTT channel to control fans through their wireless
# remote interface. Turns on the fan if the temperature >= on_temp.
# Turns off the fan if the temperature <= off_temp. Listens for changes
# to the house automation mode and re-evalutes if the mode changes to
# an allowed mode

class FanControl(hass.Hass):

    def initialize(self):
        self.disabled_modes = [
            item.casefold() for item in self.args['disabled_modes']
        ]
        self.fan_off_temp = float(self.args['fan_off_temp'])
        self.fan_on_temp = float(self.args['fan_on_temp'])
        self.fan_off_trigger = self.args['fan_off_trigger']
        self.fan_on_trigger = self.args['fan_on_trigger']
        self.temp_sensor = self.args['temp_sensor']
        self.tracking_entity = self.args['tracking_entity']

        self.listen_state(self.temp_change, self.temp_sensor)
        self.listen_state(
            self.temp_change,
            'input_boolean.home_occupancy'
        )

    @property
    def allowed_mode(self):

        # is the automation mode in an allowed state?
        if 'away' in self.disabled_modes:
            if self.home_occupancy == 'off':
                self.log(
                    'automation declined for occupancy - ' +
                    self.current_state()
                )
                return False
        if 'guest' in self.disabled_modes:
            if self.guest_mode == 'on':
                self.log(
                    'automation declined for guest mode - ' +
                    self.current_state()
                )
                return False
        if 'quiet' in self.disabled_modes:
            if self.quiet_mode == 'on':
                self.log(
                    'automation declined for quiet mode - ' +
                    self.current_state()
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
    def tracker_value(self):
        return self.get_state(self.tracker)

    def temp_change(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        if self.allowed_mode is False:
            return

        # get the current temperature
        current_temp = float(self.get_state(
            self.temp_sensor,
            attribute='state'
        ))

        # turn on the fan if it's too warm
        if current_temp >= self.fan_on_temp:
            if self.tracker_value == 'off':
                # turn on living room fan
                self.select_option(
                    self.tracking_entity,
                    'on'
                )
                self.log((
                    'fan turned on. Temperature is {} - ' +
                    self.current_state).format(current_temp)
                )

        # turn off the fan if it's too cool
        if current_temp < self.fan_off_temp:
            if self.tracker_value == 'on':
                # turn off living room fan
                self.select_option(
                    self.tracking_entity,
                    'off'
                )
                self.log((
                    'fan turned off. Temperature is {} - ' +
                    self.current_state).format(current_temp)
                )

    def tracker_off(self, entity, attribute, old, new, kwargs):

        # call IFTTT to turn off the fan
        self.call_service(
            'ifttt/trigger',
            event=self.fan_off_trigger
        )

    def tracker_on(self, entity, attribute, old, new, kwargs):

        # call IFTTT to turn on the fan
        self.call_service(
            'ifttt/trigger',
            event=self.fan_on_trigger
        )
