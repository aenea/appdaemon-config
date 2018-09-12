import appdaemon.plugins.hass.hassapi as hass
import time


class Bulb:
    def __init__(
        self,
        entity_id,
        brightness
    ):
        self.entity_id = entity_id
        self.brightness = brightness


class PicoLight(hass.Hass):

    def initialize(self):
        self.actuator = self.args['actuator_entity']
        self.light_group = self.args['light_group']
        self.light_subset = self.args['light_subset']
        self.brightness = self.args['brightness']
        self.state = 0
        self.single_bulb = 0

        self.listen_state(self.no_button, self.actuator, new='0')
        self.listen_state(self.switch_on, self.actuator, new='1')
        self.listen_state(self.switch_on, self.actuator, new='2')
        self.listen_state(self.switch_off, self.actuator, new='4')
        self.listen_state(self.brighter, self.actuator, new='8')
        self.listen_state(self.dimmer, self.actuator, new='16')

    def switch_on(self, entity, attribute, old, new, kwargs):

        # capture button press
        self.state = new

        if self.state == '1':
            # top button turns the light on to full brightness
            self.turn_on(self.light_group, brightness_pct='100')
        else:
            # favorite button turns on one light
            group_entity = self.get_state(self.light_group, attribute='all')
            lights = group_entity['attributes']['entity_id']
            count = len(lights)

            # each press should turn on the next light in the light
            # group and turn off all the other lights
            i = 0
            for light in lights:
                if i == self.single_bulb:
                    self.turn_on(light)
                else:
                    self.turn_off(light)

                i += 1

            self.single_bulb += 1
            if self.single_bulb >= count:
                self.single_bulb = 0

    def switch_off(self, entity, attribute, old, new, kwargs):

        # capture button press
        self.state = new

        # turn off the light
        self.turn_off(self.light_group)

    def brighter(self, entity, attribute, old, new, kwargs):

        # capture button press
        self.state = new

        # increase the brightness by 5%
        self.change_brightness(5, new)

    def dimmer(self, entity, attribute, old, new, kwargs):

        # capture button press
        self.state = new

        # decrease the brightness by 5%
        self.change_brightness(-5, new)

    def no_button(self, entity, attribute, old, new, kwargs):

        # capture button press
        self.state = new

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
            light_state = self.get_state(light, attribute='all')
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
                    entity_id=bulb.entity_id,
                    brightness_pct=bulb.brightness
                )
            time.sleep(.1)
