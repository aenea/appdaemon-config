import appdaemon.plugins.hass.hassapi as hass


class FanControl(hass.Hass):

    def initialize(self):
        self.active_modes = self.args['active_modes']
        self.fan_off_temp = int(self.args['fan_off_temp'])
        self.fan_on_temp = int(self.args['fan_on_temp'])
        self.fan_off_trigger = self.args['fan_off_trigger']
        self.fan_on_trigger = self.args['fan_on_trigger']
        self.temp_sensor = self.args['temp_sensor']
        self.tracking_entity = self.args['tracking_entity']

        self.listen_state(self.temp_change, self.temp_sensor)
        self.listen_state(
            self.temp_change,
            'input_select.automation_mode'
        )

    def temp_change(self, entity, attribute, old, new, kwargs):

        # is the automation mode in an allowed state?
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in self.active_modes:
            return

        # get the current temperature
        current_temp = float(self.get_state(
            self.temp_sensor,
            attribute='state'
        ))

        # get the current state of the fan
        fan_state = self.get_state(
            self.tracking_entity,
            attribute='state'
        ).casefold()

        self.log(automation_mode)
        self.log(current_temp)

        # turn on the fan if it's too warm
        if current_temp >= self.fan_on_temp:
            if fan_state == 'manual':
                # turn off living room fan
                self.call_service(
                    'ifttt/trigger',
                    event=self.fan_on_trigger
                )
                self.select_option(
                    'input_select.living_room_fan_status',
                    'Automated'
                )
                self.call_service(
                    'logbook/log',
                    entity_id=self.occupancy,
                    domain='automation',
                    name='fan_control: ',
                    message=(
                        ' living room fan turned on. Temperature is {}'.format(
                            current_temp
                        )
                    )
                )

        # turn off the fan if it's too cool
        if current_temp < self.fan_off_temp:
            if fan_state == 'automated':
                # turn off living room fan
                self.call_service(
                    'ifttt/trigger',
                    event=self.fan_off_trigger
                )
                self.select_option(
                    'input_select.living_room_fan_status',
                    'Manual'
                )
                self.call_service(
                    'logbook/log',
                    entity_id=self.occupancy,
                    domain='automation',
                    name='fan_control: ',
                    message=(
                        ' living room fan turned off. '
                        'Temperature is {}'.format(
                            current_temp
                        )
                    )
                )