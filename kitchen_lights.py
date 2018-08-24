import appdaemon.plugins.hass.hassapi as hass


class KitchenLights(hass.Hass):

    def initialize(self):

        self.off_timer = None

        self.listen_state(
            self.sensor_off,
            'group.kitchen_occupancy',
            new='off'
        )

        self.listen_state(
            self.sensor_on,
            'group.kitchen_occupancy',
            new='on'
        )
    
    def sensor_off(self, entity, attribute, old, new, kwargs):

        # motion has stopped - wait for 10 minutes
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None
        
        self.off_timer = self.run_in(self.turn_off_lights, 600)

    def sensor_on(self, entity, attribute, old, new, kwargs):

        # motion has started - cancel any timers
        if self.off_timer is not None:
            self.cancel_timer(self.off_timer)
            self.off_timer = None

    def turn_off_lights(self, kwargs):

        # Turn off the kitchen lights if night mode is active
        # Moonlight the kitchen if appropriate

        if self.get_state('input_boolean.night_mode') == 'off':
            return

        if self.get_state('input_boolean.moonlight') == 'off':
            self.turn_off('group.kitchen_lights')
        else:
            self.turn_off('light.kitchen_light_switch_level')
            self.turn_on("group.kitchen_lights_moonlight", brightness_pct=10)
