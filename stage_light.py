import appdaemon.plugins.hass.hassapi as hass

#
# StageLight - turns on lights at a dimmed level in adjoinging rooms in 
# response to a motion sensor event. This prevents walking into a dark room
# before the target room's motion sensor activates. The target room's lights 
# will come # on normally when it's motion sensor activates. Stage lights 
# turn off if the # room's motion sensor doesn't trigger after a configurable 
# delay
#
# Args: 
# 
# sensor_entity - The motion sensor in the adjoining room
# actuator_entity - The switch/lights to turn on
# tracking_entity - An input_select variable to track the lighting state of
# the room 
# delay - How long to keep the stage lighting on before timing out
# brightness - Lighting level of the stage lighting
#

class StageLight(hass.Hass):

    def initialize(self):
        self.sensor = self.args['sensor_entity']
        self.actuator = self.args['actuator_entity']
        self.tracker = self.args['tracking_entity']
        self.delay = self.args['delay']
        self.brightness = self.args['brightness']
        self.off_timer = None

        self.listen_state(self.sensor_on, self.sensor, new='on', old='off')
        
    def sensor_on(self, entity, attribute, old, new, kwargs):

        # get the state of the switch
        switch_state = self.get_state(self.actuator, attribute='state')

        # turn on the switch if it is off
        if switch_state == 'off':
            self.turn_on(self.actuator, brightness_pct=self.brightness)

            self.log("Stage light for {} turned on".format(self.actuator), level='INFO')

            # set the tracking flag
            self.select_option(self.tracker, 'Stage')
        else:
            self.log("Stage light for {} declined because light is already on".format(self.actuator), 
                level='INFO')

        # cancel any existing timers
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # create a callback to turn off the light
        if self.delay > 0:
            self.off_timer = self.run_in(self.actuator_off, self.delay)
        else:
            self.actuator_off(self)

    def actuator_off(self, kwargs):

        # Remove the timer handle
        self.off_timer = None
        
        # get the state of the lighting flag
        lighting_state = self.get_state(self.tracker, attribute='state')
        
        # turn off the light if the state is still 'Stage'
        if lighting_state == 'Stage':
            self.turn_off(self.actuator)
                        
            self.log("Stage light for {} turned off".format(self.actuator), level='INFO')
        
            # turn off the tracking variable
            self.select_option(self.tracker, 'Off')
        else:
            self.log("Turn off of stage light for {} declined because lighting state has changed to {}".format(
                self.actuator, lighting_state), level='INFO')
