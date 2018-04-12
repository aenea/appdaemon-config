import appdaemon.plugins.hass.hassapi as hass


class HouseOccupancy(hass.Hass):

    def initialize(self):

        self.sensor = self.args['sensor_entity']

        self.listen_state(self.home_occupied, self.sensor, new='on')
        self.listen_state(self.home_unoccupied, self.sensor, new='off')
        self.listen_state(self.set_occupancy_on, 'group.presence_all',
                          new='home', old='not_home')
        self.listen_state(self.set_occupancy_off, 'group.presence_all',
                          new='not_home', old='home')
        self.listen_state(self.someone_arrives, 'device_tracker', new='home')
        self.listen_state(
            self.door_opens,
            'binary_sensor.back_door_sensor_sensor',
            new='on'
        )
        self.listen_state(
            self.climate_mode_change,
            'climate.home',
            attribute='climate_mode'
        )

    def door_opens(self, entity, attribute, old, new, kwargs):

        # Turn off the porch light when the back door opens if
        # the porch light was turned on by automation
        porch_light_status = self.get_state(
            'input_select.front_porch_light_status',
            attribute='state'
        )

        if porch_light_status.casefold() == 'automated':
            self.turn_off('switch.front_porch_light_switch_switch')

    def set_occupancy_on(self, entity, attribute, old, new, kwargs):

        self.turn_on(self.sensor)
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=('someone has arrived to an empty house')
        )

    def set_occupancy_off(self, entity, attribute, old, new, kwargs):

        self.turn_off(self.sensor)
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=('everyone has left')
        )

    def someone_arrives(self, entity, attribute, old, new, kwargs):

        # get the house mode
        house_mode = self.get_state(
            'input_select.house_mode',
            attribute='state'
        )

        if house_mode.casefold() == 'night':
            # turn on the porch light
            self.select_option(
                'input_select.front_porch_light_status',
                'Automated'
            )
            self.turn_on('switch.porch_light_switch_switch')
            self.call_service(
                'logbook/log',
                entity_id=self.sensor,
                domain='automation',
                name='house_occupancy: ',
                message=('porch light turned on for arrival')
            )

        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(
                '{} has arrived. House mode is {}'.format(
                    entity, house_mode
                )
            )
        )

    def home_occupied(self, entity, attribute, old, new, kwargs):

        # stop the dog music
        self.call_service(
            'media_player/squeezebox_call_method',
            entity_id='media_player.office',
            command='power',
            parameters='0'
        )
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(' dog music stopped')
        )

        # get the house mode
        house_mode = self.get_state(
            'input_select.house_mode',
            attribute='state'
        )

        if house_mode.casefold() == 'night':
            # turn on the welcome lights
            self.turn_on('group.welcome_lights')
            self.call_service(
                'logbook/log',
                entity_id=self.sensor,
                domain='automation',
                name='house_occupancy: ',
                message=('welcome lights turned on')
            )
        else:
            self.call_service(
                'logbook/log',
                entity_id=self.sensor,
                domain='automation',
                name='house_occupancy: ',
                message=(
                    'welcome lights declined - house mode is {}'.format(
                        house_mode
                    )
                )
            )

    def home_unoccupied(self, entity, attribute, old, new, kwargs):

        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(' house is not occupied')
        )

        # turn off lights
        self.turn_off('group.lights')
        self.turn_off('group.switches')
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(' all lights turned off')
        )

        # turn off remotes
        self.turn_off('group.remotes')
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(' all remotes turned off')
        )

        # resume thermostat schedule
        self.call_service(
            'climate/set_hold_mode',
            entity_id='climate.home',
            hold_mode='None'
        )
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(' thermostat schedule resumed')
        )

        # start the dog music
        self.call_service(
            'media_player/squeezebox_call_method',
            entity_id='media_player.office',
            command='playlist',
            parameters=['loadtracks', 'album.titlesearch=Through a dogs ears']
        )
        self.call_service(
            'logbook/log',
            entity_id=self.sensor,
            domain='automation',
            name='house_occupancy: ',
            message=(' dog music started')
        )

    def climate_mode_change(self, entity, attribute, old, new, kwargs):

        # Is the house occupied?
        house_occupancy = self.get_state(
            'group.presence_all',
            attribute='state'
        )

        # don't allow the thermostat to move to away mode if someone
        # is home
        if new.casefold() == 'away' and house_occupancy == 'home':
            self.call_service(
                'climate/set_hold_mode',
                entity_id='climate.home',
                hold_mode='home'
            )
