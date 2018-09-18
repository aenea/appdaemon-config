import appdaemon.plugins.hass.hassapi as hass
import datetime


class HouseOccupancy(hass.Hass):

    def initialize(self):

        # state tracker for house occupancy
        self.climate = self.args['climate_entity']
        self.disabled_modes = []
        self.doors = self.args['doors_entity']
        self.occupancy = self.args['occupancy_entity']

        # react to someone arrive to an empty house
        self.listen_state(self.home_occupied, self.occupancy, new='on')

        # react to the house becoming unoccupied
        self.listen_state(self.home_unoccupied, self.occupancy, new='off')

        # react to the arrival of individuals
        self.listen_state(self.someone_arrives, 'device_tracker', new='home', old='not_home')

        # react to entry door status
        self.listen_state(self.door_opens, self.doors, new='on')

        # react to thermostat climate mode changes
        self.listen_state(self.climate_mode_change, self.climate, attribute='climate_mode')

        # trigger the bed time routine when quiet mode turns on
        self.listen_state(self.bed_time, 'input_boolean.quiet_mode', new='on')

        # trigger bed time routine when the button is pressed
        self.listen_state(self.bed_time, 'sensor.hallway_keypad', new='4')

        # react to night mode changes
        self.listen_state(self.night_mode_change, 'input_boolean.night_mode')

        # react to quiet mode turning off
        self.listen_state(self.quiet_mode_off, 'input_boolean.quiet_mode', new='off')

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
            'quiet_mode=%s '
            ')'
            %
            (
                self.home_occupancy,
                self.guest_mode,
                self.moonlight,
                self.night_mode,
                self.quiet_mode
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

    def door_opens(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log('porch light automation declined - ' + self.current_state)
            return

        # if the porch light was turned on by automation, turn
        # it off when an entry door opens
        porch_light_status = self.get_state(
            'input_select.front_porch_lights_tracker',
            attribute='state'
        )

        if porch_light_status.casefold() == 'on':
            self.select_option(
                'input_select.front_porch_lights_tracker',
                'off'
            )
            self.log(
                'porch light turned off by door opening - ' +
                self.current_state
            )

    def someone_arrives(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log('arrival automation declined - ' + self.current_state)
            return

        if self.night_mode == 'on':
            # turn on the porch light
            self.select_option(
                'input_select.front_porch_lights_tracker',
                'on'
            )
            self.log(
                'front porch light turned on for arrival - ' +
                self.current_state
            )

    def home_occupied(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'home occupation automation declined - ' +
                self.current_state
            )
            return

        # stop the dog music
        self.call_service(
            'media_player/squeezebox_call_method',
            entity_id='media_player.office',
            command='power',
            parameters='0'
        )
        self.log('dog music stopped')

        # set the thermostat to 'home' mode if necessary
        climate_mode = self.get_state(self.climate, attribute='climate_mode')
        if climate_mode.casefold() == 'away':
            self.call_service(
                'climate/set_hold_mode',
                entity_id=self.climate,
                hold_mode='home'
            )
            self.log('thermostat set to home mode')

        if self.night_mode == 'on':
            # turn on the welcome lights
            self.turn_on('group.welcome_lights')
            self.log('welcome lights turned on')

        self.log(
            'home occupation automation complete - ' +
            self.current_state
        )

    def home_unoccupied(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'home unoccupied automation declined - ' +
                self.current_state
            )
            return

        # turn off lights
        self.turn_off('group.lights')
        self.log('lights turned off')

        # turn off remotes
        self.turn_off('group.all_remotes')
        self.log('remotes turned off')

        # resume thermostat schedule
        self.call_service(
            'climate/ecobee_resume_program',
            entity_id=self.climate,
            resume_all='true'
        )
        self.log('thermostat schedule resumed')

        # turn off living room fan
        self.select_option(
            'input_select.living_room_fan_tracker',
            'off'
        )
        self.log('living room fan turned off')

        # turn off master bedroom fan
        self.select_option(
            'input_select.master_bedroom_fan_tracker',
            'off'
        )
        self.log('master bedroom room fan turned off')

        # start the dog music
        self.call_service(
            'media_player/squeezebox_call_method',
            entity_id='media_player.office',
            command='playlist',
            parameters=['loadtracks', 'album.titlesearch=Through a dogs ears']
        )
        self.log('dog music started')

        self.log(
            'home unoccupied automation complete - ' +
            self.current_state
        )

    def climate_mode_change(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'force home climate mode declined - ' +
                self.current_state
            )
            return

        # don't allow the thermostat to move to away mode if someone
        # is home
        if (
            new.casefold() == 'away' and
            self.home_occupancy == 'on'
        ):
            hold_mode = self.get_state('climate.home', attribute='hold_mode')
            if hold_mode is None or hold_mode.casefold() != 'home':
                self.call_service(
                    'climate/set_hold_mode',
                    entity_id=self.climate,
                    hold_mode='home'
                )
                self.log('climate mode forced to home ' + self.current_state)

    def bed_time(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'bed time routine declined - ' +
                self.current_state
            )
            return

        # turn off moonlighting
        self.turn_off('input_boolean.moonlight')
        self.log('moonlighting turned off')

        # turn on the bed time light scene
        self.call_service(
            'scene/turn_on',
            entity_id='scene.bed_time_lights'
        )
        self.log('bed time lights turned on')

        # turn off the remotes
        self.call_service(
            'remote/turn_off',
            entity_id='group.all_remotes'
        )
        self.log('remotes turned off')

        # set the thermostat mode to 'sleep'
        self.call_service(
            'climate/set_hold_mode',
            entity_id=self.climate,
            hold_mode='sleep'
        )
        self.log('thermostat set to sleep mode')

        # turn off living room fan
        self.select_option(
            'input_select.living_room_fan_tracker',
            'off'
        )
        self.log('living room fan turned off')

        self.log('bed time routine complete - ' + self.current_state)

    def night_mode_change(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'night mode routine declined - ' +
                self.current_state
            )
            return

        if new == 'on':
            # turn on moonlight mode
            self.turn_on('input_boolean.moonlight')
        elif new == 'off':
            # turn off moonlight mode
            self.turn_off('input_boolean.moonlight')

            # turn off the night lights if quiet mode is still active
            if self.quiet_mode == 'on':
                self.turn_off('group.night_lights')

    def quiet_mode_off(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'quiet mode routine declined - ' +
                self.current_state
            )
            return

        # turn off the night lights
        self.turn_off('group.night_lights')

        # turn off night mode if it after 4am
        if datetime.datetime.now().time() > datetime.time(hour=4):
            self.turn_off('input_boolean.night_mode')

        # resume the thermostat schedule
        self.call_service(
            'climate/ecobee_resume_program',
            entity_id='climate.home',
            resume_all='true'
        )

        self.log('left quiet mode')
