import appdaemon.plugins.hass.hassapi as hass
#
# Provides scene support for the Homeseer dimmer
# switches
#

class HomeseerSwitch(hass.Hass):
    
    def initialize(self):

        self.actuator = self.args['actuator_entity']
        self.scene_id = self.args['scene_id']
        self.zwave_entity = self.args['zwave_entity']
        
        self.listen_event(self.scene_on, event='zwave.scene_activated', entity_id=self.zwave_entity, 
            scene_id=1, scene_data=self.scene_id)
        self.listen_event(self.scene_off, event='zwave.scene_activated', entity_id=self.zwave_entity, 
            scene_id=2, scene_data=self.scene_id)        

    def scene_on(self, event_name, data, kwargs):
        
        if self.scene_id == 3 or self.scene_id == 7860:
            # The top paddle has been double tapped. Turn the brightness to 100%
            self.turn_on(self.actuator, brightness_pct=100)
            self.log(self.actuator + " double tapped on", level='INFO')
        
    def scene_off(self, event_name, data, kwargs):
        
        if self.scene_id == 3 or self.scene_id == 7860:
            # The bottom paddle has been double tapped. Turn the brightness to 2%
            self.turn_on(self.actuator, brightness_pct=2)
            self.log(self.actuator + " double tapped off", level='INFO')

        elif self.scene_id == 4 or self.scene_id == 7920: 
            # The bottom paddle has been triple tapped. Turn on the bed time routine
            self.turn_on('input_boolean.bed_time')
            self.log("{} triple tapped off".format(self.actuator), level='INFO')

        