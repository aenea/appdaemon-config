import appdaemon.plugins.hass.hassapi as hass
import time
#
# switchLight App
#
# Args: asdf
# asf


class PicoLight(hass.Hass):

    def initialize(self):
        self.actuator = self.args['actuator_entity']
        self.light_group = self.args['light_group']
        self.light_subset = self.args['light_subset']
        self.brightness = self.args['brightness']
        self.block_restart = False
        self.state = 0

        self.listen_state(self.no_button, self.actuator, new='0')
        self.listen_state(self.switch_on, self.actuator, new='1')
        self.listen_state(self.switch_on, self.actuator, new='2')
        self.listen_state(self.switch_off, self.actuator, new='4')
        self.listen_state(self.brighter, self.actuator, new='8')
        self.listen_state(self.dimmer, self.actuator, new='16')

    def switch_on(self, entity, attribute, old, new, kwargs):

        self.state = new

        # get the current state of the light
        state = self.get_state(
            self.light_group,
            attribute='state'
        )

        if new == '1':
            # top button turns the light on with full brightness
            self.turn_on(self.light_group, brightness_pct='100')
        else:
            # favorite button turns on a subset of lights
            self.turn_on(self.light_subset, brightness_pct='100')

    def switch_off(self, entity, attribute, old, new, kwargs):

        self.state = new
        # turn off the light
        self.turn_off(self.light_group)

    def change_brightness(self, change, button):

        # get the current state of the light
        state = self.get_state(
            self.light_group,
            attribute='state'
        )

        # do nothing if the light is off
        if state == 'off':
            return

        # get a list of lights in the group
        group_entity = self.get_state(self.light_group, attribute='all')
        lights = group_entity['attributes']['entity_id']

        while self.state != '0':
            for light in lights:
                # get the current state of the light
                light_state = self.get_state(light, attribute='all')
                if light_state['state'] == 'on':
                    brightness = light_state['attributes']['brightness']
                    brightness_pct = round(
                        (float(brightness / 255) * 100), 0
                    )
                    # change the brightness level
                    new_brightness = brightness_pct + change
                    new_brightness = max(min(100, new_brightness), 5)

                    self.turn_on(
                        light,
                        brightness_pct=str(new_brightness)
                    )
            time.sleep(.10)

        self.call_service(
            'logbook/log',
            entity_id=self.actuator,
            domain='automation',
            name='pico_light: ',
            message=('{} brightness changed from {} to {}'.format(
                self.light_group,
                brightness_pct,
                new_brightness)
            )
        )

    def brighter(self, entity, attribute, old, new, kwargs):

        self.state = new

        # increase the brightness by 4%
        self.change_brightness(4, new)

    def dimmer(self, entity, attribute, old, new, kwargs):

        self.state = new

        # decrease the brightness by 4%
        self.change_brightness(-4, new)

    def no_button(self, entity, attribute, old, new, kwargs):

        self.state = new