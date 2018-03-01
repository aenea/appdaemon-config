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

    def set_occupancy_on(self, entity, attribute, old, new, kwargs):

        self.turn_on('input_boolean.home_occupancy')
        self.log("Someone has arrived to an empty house", level='INFO')

    def set_occupancy_off(self, entity, attribute, old, new, kwargs):        
    
        self.turn_off('input_boolean.home_occupancy')
        self.log("Everyone has left", level='INFO')

    def someone_arrives(self, entity, attribute, old, new, kwargs):
        
        # get the house mode
        house_mode = self.get_state('input_select.house_mode',
          attribute='state')
        
        if house_mode == 'Night':
            # turn on the porch light
            self.select_option('input_select.porch_light_status',
                               'Automated')
            self.turn_on('switch.porch_light_switch_switch')            
            self.log('Porch light turned on for arrival', level='INFO')
                    
        self.log('{} has arrived. House mode is {}'.format(entity,
          house_mode))


    # someone has arrived to an empty house
    def home_occupied(self, entity, attribute, old, new, kwargs):

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
    def home_unoccupied(self, entity, attribute, old, new, kwargs):

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
        self.log("Thermostat away mode set", level='INFO')

        # start the dog music
        self.call_service('media_player/squeezebox_call_method', 
          entity_id='media_player.office', 
          command='playlist', 
          parameters=['loadtracks', 'album.titlesearch=Through a dogs ears'])
        self.log("Dog music started", level='INFO')




