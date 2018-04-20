import appdaemon.plugins.hass.hassapi as hass

#
# switchLight App
#
# Args: asdf
# asf


class PicoLight(hass.Hass):

    def initialize(self):
        self.actuator = self.args['actuator_entity']
        self.light_group = self.args['light_group']
        self.brightness = self.args['brightness']
        self.block_restart = False

        self.listen_state(self.switch_on, self.actuator, new='1')
        self.listen_state(self.switch_on, self.actuator, new='2')
        self.listen_state(self.switch_off, self.actuator, new='4')
        self.listen_state(self.brighter, self.actuator, new='8')
        self.listen_state(self.dimmer, self.actuator, new='16')        

    def switch_on(self, entity, attribute, old, new, kwargs):

        # get the current state of the light
        state = self.get_state(
            self.light_group,
            attribute='state'
        )

        if new == '1':
            # top button turns the light on with full brightness
            self.turn_on(self.light_group, brightness_pct='100')
        else:
            # favorite button turns on the previous brightness
            self.turn_on(self.light_group)

    def switch_off(self, entity, attribute, old, new, kwargs):

        # turn off the light
        self.turn_off(self.light_group)

    def change_brightness(self, change):

        # get the current state of the light
        state = self.get_state(
            self.light_group,
            attribute='state'
        )

        # do nothing if the light is off
        if state == 'off':
            return

        # get the current brightness level
        old_brightness = self.get_state(
            self.light_group,
            attribute='brightness'
        )

        # convert the brightness to a percentage
        brightness_pct = round((float(old_brightness / 255) * 100), 0)

        # change the brightness level
        new_brightness = brightness_pct + change

        # round the new brightness to the nearest 10
        new_brightness = int(round((new_brightness / 10), 0) * 10)

        # maximum brightness is 100%
        if new_brightness > 100:
            new_brightness = 100

        # minimum brightness is 5%
        if new_brightness < 5:
            new_brightness = 5

        # change the light to the new brightness
        self.turn_on(
            self.light_group,
            brightness_pct=str(new_brightness),
            transition=0
        )
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

        # increase the brightness by 10%
        self.change_brightness(10)

    def dimmer(self, entity, attribute, old, new, kwargs):

        # decrease the brightness by 10%
        self.change_brightness(-10)
