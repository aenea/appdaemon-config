import appdaemon.plugins.hass.hassapi as hass
import time
#
# switchLight App
#
# Args: asdf
# asf


class PicoLight(hass.Hass):

    class Bulb:
        def __init__(
            self,
            entity_name,
            brightness0
        ):
            pass

    def initialize(self):
        self.actuator = self.args['actuator_entity']
        self.light_group = self.args['light_group']
        self.light_subset = self.args['light_subset']
        self.brightness = self.args['brightness']
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

        if self.state == '1':
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

        # get the current state of the light group
        light_state = self.get_state(
            self.light_group,
            attribute='state'
        ).casefold()

        # If the light group is off, start at 5% if brightening
        # or 95% if dimming
        if light_state == 'off':
            if change > 0:
                # brightening the light - start at 5%
                brightness_pct = '5'
                new_brightness = brightness_pct
                self.turn_on(
                    self.light_group,
                    brightness_pct=brightness_pct,
                    transition='0.1'
                )
            else:
                # dimming the light - start at 95%
                brightness_pct = '95'
                new_brightness = brightness_pct
                self.turn_on(
                    self.light_group,
                    brightness_pct=brightness_pct,
                    transition='0.1'
                )

        # get a list of lights in the group
        group_entity = self.get_state(self.light_group, attribute='all')
        lights = group_entity['attributes']['entity_id']

        # construct the array of bulb objects
        bulbs = []
        for light in lights:
            # get the current brightness
            brightness = light_state['attributes']['brightness']
            brightness_pct = round(
                (float(brightness / 255) * 100), 0
            )

            t = Bulb(
                entity_id=light,
                brightness=brightness_pct
            )
            bulbs.append(t)

        # loop while the button is held down
        while self.state != '0':
            for bulb in bulbs:
                # change the desired brightness
                bulb.brightness += change

                # cap the brightness at 100% and 5%
                bulb.brightness = max(min(100, bulb.brightness), 5)

                # apply the new brightness level
                self.turn_on(
                    light,
                    brightness_pct=str(new_brightness)
                )

            time.sleep(.15)

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

        # increase the brightness by 5%
        self.change_brightness(5, new)

    def dimmer(self, entity, attribute, old, new, kwargs):

        self.state = new

        # decrease the brightness by 5%
        self.change_brightness(-5, new)

    def no_button(self, entity, attribute, old, new, kwargs):

        self.state = new
