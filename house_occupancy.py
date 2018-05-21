import appdaemon.plugins.hass.hassapi as hass


class HouseOccupancy(hass.Hass):

    def initialize(self):

        # state tracker for house occupancy
        self.occupancy = self.args['occupancy_entity']
        self.doors = self.args['doors_entity']
        self.climate = self.args['climate_entity']

        # react to arrivals
        self.listen_state(self.home_occupied, self.occupancy, new='on')
        # react to departures
        self.listen_state(self.home_unoccupied, self.occupancy, new='off')
        # set ocupancy state
        self.listen_state(
            self.set_occupancy_on,
            'group.presence_all',
            new='home',
            old='not_home'
        )
        # set occupancy state
        self.listen_state(
            self.set_occupancy_off,
            'group.presence_all',
            new='not_home',
            old='home'
        )
        # track the arrival of individuals
        self.listen_state(
            self.someone_arrives,
            'device_tracker',
            new='home',
            old='not_home'
        )

        # track entry door status
        self.listen_state(self.door_opens, self.doors, new='on')

        # track thermostat climate mode changes
        self.listen_state(
            self.climate_mode_change,
            self.climate,
            attribute='climate_mode'
        )

        # track sleep status
        self.listen_state(
            self.bed_time,
            'input_boolean.bed_time',
            new='on',
            old='off'
        )

    def door_opens(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        allowed_modes = set(['normal', 'away', 'sleep'])
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in allowed_modes:
            return

        # if the porch light was turned on by automation, turn
        # it off when an entry door opens
        porch_light_status = self.get_state(
            'input_select.front_porch_light_status',
            attribute='state'
        )

        if porch_light_status.casefold() == 'automated':
            self.turn_off('switch.front_porch_light_switch_switch')

    def set_occupancy_on(self, entity, attribute, old, new, kwargs):

        self.turn_on(self.occupancy)
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=('someone has arrived to an empty house')
        )

    def set_occupancy_off(self, entity, attribute, old, new, kwargs):

        self.turn_off(self.occupancy)
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=('everyone has left')
        )

    def someone_arrives(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        allowed_modes = set(['normal', 'away', 'sleep'])
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in allowed_modes:
            return

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
                entity_id=self.occupancy,
                domain='automation',
                name='house_occupancy: ',
                message=('porch light turned on for arrival')
            )

        # log the arrival
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=(
                '{} has arrived. House mode is {}'.format(
                    entity, house_mode
                )
            )
        )

    def home_occupied(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        allowed_modes = set(['normal', 'away', 'sleep'])
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in allowed_modes:
            return
        else:
            # Set the automation mode to 'Normal'
            self.select_option('input_select.automation_mode', 'Normal')

        # stop the dog music
        self.call_service(
            'media_player/squeezebox_call_method',
            entity_id='media_player.office',
            command='power',
            parameters='0'
        )
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=(' dog music stopped')
        )

        # set the thermostat to 'home' mode if necessary
        climate_mode = self.get_state(self.climate, attribute='climate_mode')
        if climate_mode.casefold() == 'away':
            self.call_service(
                'climate/set_hold_mode',
                entity_id=self.climate,
                hold_mode='home'
            )
            self.call_service(
                'logbook/log',
                entity_id=self.occupancy,
                domain='automation',
                name='house_occupancy: ',
                message=('thermostat climate set to Home')
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
                entity_id=self.occupancy,
                domain='automation',
                name='house_occupancy: ',
                message=('welcome lights turned on')
            )
        else:
            self.call_service(
                'logbook/log',
                entity_id=self.occupancy,
                domain='automation',
                name='house_occupancy: ',
                message=(
                    'welcome lights declined - house mode is {}'.format(
                        house_mode
                    )
                )
            )

    def home_unoccupied(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        allowed_modes = set(['normal', 'away', 'sleep'])
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in allowed_modes:
            return

        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=(' house is not occupied')
        )

        # turn off lights
        self.turn_off('group.all_lights')
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=(' all lights turned off')
        )

        # turn off remotes
        self.turn_off('group.remotes')
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=(' all remotes turned off')
        )

        # resume thermostat schedule
        self.call_service(
            'climate/ecobee_resume_program',
            entity_id=self.climate,
            resume_all='true'
        )
        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
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
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=(' dog music started')
        )

        # set the house to away mode
        self.select_option('input_select.automation_mode', 'Away')

    def climate_mode_change(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        allowed_modes = set(['normal', 'away', 'sleep'])
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in allowed_modes:
            return

        # Is the house occupied?
        house_occupancy = self.get_state(self.occupancy, attribute='state')

        # don't allow the thermostat to move to away mode if someone
        # is home
        if new.casefold() == 'away' and house_occupancy.casefold() == 'on':
            self.call_service(
                'climate/set_hold_mode',
                entity_id=self.climate,
                hold_mode='home'
            )

    def bed_time(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        allowed_modes = set(['normal', 'away', 'sleep'])
        automation_mode = self.get_state(
            'input_select.automation_mode',
            attribute='state'
        )
        automation_mode = automation_mode.casefold()
        if automation_mode not in allowed_modes:
            return
        else:
            self.select_option('input_select.automation_mode', 'Sleep')

        # turn off all the lights
        self.turn_off('group.lights_sleep_off')

        # turn on the night lights
        self.turn_on(
            'light.kitchen_sink_light_switch_level',
            brightness_pct='2'
        )

        # turn off the remotes
        self.call_service(
            'remote/turn_off',
            entity_id='remote.living_room'
        )
        self.call_service(
            'remote/turn_off',
            entity_id='remote.tv_room'
        )

        # set the thermostat mode to 'sleep'
        self.call_service(
            'climate/set_hold_mode',
            entity_id=self.climate,
            hold_mode='sleep'
        )

        self.call_service(
            'logbook/log',
            entity_id=self.occupancy,
            domain='automation',
            name='house_occupancy: ',
            message=('Bed time routine triggered')
        )

        # flip the flag back off
        self.turn_off('input_boolean.bed_time')
