import appdaemon.plugins.hass.hassapi as hass

class HouseOccupancy(hass.Hass):

    def initialize(self):

        self.sensor = self.args['sensor_entity']

        self.listen_state(self.house_occupied, self.sensor, new='on')
        self.listen_state(self.house_unoccupied, self.sensor, new='off')
        self.listen_state(self.set_occupancy_state, 'group.presence_all')

    def set_occupancy_state(self, entity, attribute, old, new, kwargs):

        # the house occupancy tracks with everyone's presence
        if new == 'Home':
            self.turn_on('input_boolean.house_occupancy')
            self.log("Someone has arrived", level='INFO')
        else:
            self.turn_off('input_boolean.house_occupancy')
            self.log("Everyone has left", level='INFO')

    # someone has arrived to an empty house
    def house_occupied(self, entity, attribute, old, new, kwargs):

        self.log("House is occupied", level='INFO')

        # stop the dog music
        self.call_service('media_player/squeezebox_call_method', 
          entity_id='media_player.office', 
          command='power', 
          parameters='0')
        self.log("Dog music stopped", level='INFO')

        # clear the thermostat away mode
        self.call_service('climate/set_away_mode', 
          entity_id='climate.Home',
          away_mode='false')
        self.log("Thermostat away mode cleared", level='INFO')

        # get the house mode
        house_mode = self.get_state('input_select.house_mode', attribute='state')
        
        if house_mode == 'Night':
            # turn on the welcome lights
            self.turn_on('group.welcome_lights')
            self.log("Welcome lights turned on", level='INFO')
        else:
            self.log("Welcome lights declined, house mode is {}"
            .format(house_mode))

    # everone has left the house
    def house_unoccupied(self, entity, attribute, old, new, kwargs):

        self.log("House is not occupied", level='INFO')

        # turn off lights
        self.turn_off('group.all_lights')
        self.turn_off('group.all_switches')
        self.log("All lights turned off", level='INFO')

        # turn off remotes
        self.turn_off('group.remotes')
        self.log('All remotes turned off', level='INFO')

        # set the thermostat away mode
        self.call_service('climate/set_away_mode', 
          entity_id='climate.Home',
          away_mode='true')
        self.log("Thermostat away mode cleared", level='INFO')

        # start the dog music
        self.call_service('media_player/squeezebox_call_method', 
          entity_id='media_player.office', 
          command='playlist', 
          parameters=['loadtracks', 'album.titlesearch=Through a dogs ears'])
        self.log("Dog music started", level='INFO')




