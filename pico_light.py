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
        self.listen_state(self.brighter, self.actuator, new='8')
        self.listen_state(self.dimmer, self.actuator, new='16')

    def switch_on(self, entity, attribute, old, new, kwargs):

        # turn on the light
        self.log("{} on".format(new))
        self.turn_on(self.light_group)

    def switch_off(self, entity, attribute, old, new, kwargs):

        # turn off the light
        self.log("{} off".format(new))
        self.turn_off(self.light_group)

    def brighter(self, entity, attribute, old, new, kwargs):

        # get the current brightness
        current_brightness = int(float(self.get_state(
            self.light_group,
            attribute='brightness')
        ))
        brightness_pct = int((current_brightness / 255) * 100)
        self.log(brightness_pct)
        
        # round the current brightness to the nearest 10
        current_brightness = round(brightness_pct / 10, 0) * 10

        # increase the brightness up by 10%
        current_brightness += 10
        
        if current_brightness > 100:
            current_brightness = 100

        # change the light brightness
        self.call_service(
            'light/lifx_set_state',
            entity_id=self.light_group, 
            brightness_pct=current_brightness
        )

    def dimmer(self, entity, attribute, old, new, kwargs):

        # get the current brightness
        current_brightness = int(float(self.get_state(
            self.light_group,
            attribute='brightness')
        ))
        brightness_pct = int((current_brightness / 255) * 100)
        self.log(brightness_pct)
        
        # round the current brightness to the nearest 10
        current_brightness = round(brightness_pct / 10, 0) * 10

        # round the current brightness to the nearest 10
        current_brightness = round(current_brightness / 10, 0) * 10

        # decrease the brightness up by 10%
        current_brightness -= 10
        
        if current_brightness < 5:
            current_brightness = 5

        # change the light brightness
        self.call_service(
            'light/lifx_set_state',
            entity_id=self.light_group, 
            brightness_pct=current_brightness
        )


