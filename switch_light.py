import appdaemon.plugins.hass.hassapi as hass

#
# switchLight App
#
# Args: asdf
#asf

class SwitchLight(hass.Hass):
    
    def initialize(self):
        self.actuator = self.args['actuator_entity']
        self.light_group = self.args['light_group']
        self.brightness = self.args['brightness']
        self.block_restart = False
        
        self.listen_state(self.switch_on, self.actuator, new='on')
        self.listen_state(self.switch_off, self.actuator, new='off')
        self.listen_state(self.light_on, self.light_group, new='on')
        self.listen_state(self.light_off, self.light_group, new='off')

    def clear_blocking_flag(self, kwargs):
        
        # Clear the blocking flag
        self.block_restart = False

    def switch_on(self, entity, attribute, old, new, kwargs):
        
        if (old == 'off'):            
            # turn on the light to the previous dimmer level
            self.turn_on(self.light_group)
            self.log(self.actuator + " turned on")
        else:
            # the dimmer level has changed, adust the lights
            dimmer_level = self.get_state(self.actuator, 
                                          attribute='brightness')
            self.turn_on(self.light_group, brightness=dimmer_level)
            self.log('{} dimmer level changed to {}'.format(
                     self.actuator, dimmer_level))
        
    def switch_off(self, entity, attribute, old, new, kwargs):
        
        # Block a quick restart. Restarts can happen from the switch 
        # synchronization logic or from the circadian light routine
        self.block_restart = True
        self.run_in(self.clear_blocking_flag, 2)

        # Turn off the light
        self.turn_off(self.light_group)
        self.log(self.actuator + " turned off")

    def light_on(self, entity, attribute, old, new, kwargs):
        
        # Turn the lights off if the lights turn on while a restart
        # is blocked
        if self.block_restart == True:
            self.turn_off(self.light_group)

        # Synchronize the switch with the state of the lights
        switch_state = self.get_state(self.actuator, attribute="state")
        if switch_state == 'off':
            self.turn_on(self.actuator)
            self.log(self.actuator + " turned on to synchronize state")
    
    def light_off(self, entity, attribute, old, new, kwargs):
        
        # Synchronize the switch with the state of the lights
        switch_state = self.get_state(self.actuator, attribute="state")
        if switch_state == 'on':
            self.turn_off(self.actuator)
            self.log(self.actuator + " turned off to syncrhonize state")
