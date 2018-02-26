import appdaemon.plugins.hass.hassapi as hass

#
# sensorLight App
#
# Args: asdf
#

class SensorLight(hass.Hass):

    def initialize(self):
        self.sensor = self.args['sensor_entity']
        self.actuator = self.args['actuator_entity']
        self.tracker = self.args['tracking_entity']
        self.delay = self.args['delay']
        self.max_run_seconds = self.args['max_run_seconds']
        self.brightness = self.args['brightness']
        self.max_timer = None
        self.off_timer = None

        self.listen_state(self.sensor_on, self.sensor, new='on')
        self.listen_state(self.sensor_off, self.sensor, new='off')
        self.listen_state(self.actuator_off, self.actuator, old='on', new='off',)
        
    def sensor_on(self, entity, attribute, old, new, kwargs):

        # get the state of the switch
        switch_state = self.get_state(self.actuator, attribute='state')

        # get the state of the lighting flag
        lighting_state = self.get_state(self.tracker, attribute='state')

        # turn on the light if it is off
        if switch_state == 'off' or lighting_state == 'Stage' or lighting_state == 'Warning':
            if self.brightness is None:
                self.turn_on(self.actuator)
            else:
                self.turn_on(self.actuator, brightness_pct=self.brightness)             
        
            # turn on the automation tracking flag
            self.select_option(self.tracker, 'Automated')

            self.log("{} turned on".format(self.actuator), level='INFO')

        # cancel any existing timers
        if self.max_timer is not None:
            self.cancel_timer(self.max_timer)
            self.max_timer = None

        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

        # set a timer to turn off the light after max_run_seconds
        if self.max_run_seconds > 0:
            self.max_timer = self.run_in(self.turn_off_actuator, self.max_run_seconds)

    def sensor_off(self, entity, attribute, old, new, kwargs):
        if self.delay > 0:
            if self.brightness is not None:
                self.off_timer = self.run_in(self.turn_off_warning, 30)
            else:
                self.off_timer = self.run_in(self.turn_off_actuator, self.delay)
        else:
            self.turn_off_actuator(self)

    def turn_off_warning(self, kwargs):

        # get the state of the lighting flag
        lighting_state = self.get_state(self.tracker, attribute='state')

        if lighting_state != "Off":        
            # dim the lights to warn about an impending turn off
            current_brightness = self.get_state(self.actuator, attribute='brightness')
            self.turn_on(self.actuator, brightness=int(current_brightness * .6))
            self.log("{} dimmed by turn off warning".format(self.actuator), level='INFO')

            # schedule the final turn off
            self.off_timer = self.run_in(self.turn_off_actuator, 30)
            self.select_option(self.tracker, 'Warning')

    def turn_off_actuator(self, kwargs):
        
        # turn off the light
        self.turn_off(self.actuator)
    
    def actuator_off(self, entity, attribute, old, new, kwargs):
        
        # clear the timer handles
        self.max_timer = None
        self.off_timer = None
        
        self.log("{} turned off".format(self.actuator))
        
        # turn off the tracking variable
        self.select_option(self.tracker, 'Off')
