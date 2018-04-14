import appdaemon.plugins.hass.hassapi as hass

#
# switchLight App
#
# Args: asdf
#asf

class PicoLight(hass.Hass):
    
    def initialize(self):
        self.actuator = self.args['actuator_entity']
        self.light_group = self.args['light_group']
        self.brightness = self.args['brightness']
        self.block_restart = False
        
        self.listen_state(self.switch_on, self.actuator, new='1')
        self.listen_state(self.switch_off, self.actuator, new='4')

    def switch_on(self, entity, attribute, old, new, kwargs):

        # turn on the light
        self.log("{} on".format(new))
        self.turn_on(self.light_group)

    def switch_off(self, entity, attribute, old, new, kwargs):

        # turn off the light
        self.log("{} off".format(new))
        self.turn_off(self.light_group)

