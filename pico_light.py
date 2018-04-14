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

    def change_brightness(self, change):

        # get the current brightness level
        old_brightness = self.get_state(
            self.light_group,
            attribute='brightness'
        )

        # convert the brightness to a percentage
        new_brightness = round((float(old_brightness / 255) * 100), 0)

        # change the brightness level
        new_brightness += change

        # round the new brightness to the nearest 10
        new_brightness = round((new_brightness / 10), 0) * 10

        # maximum brightness is 100%
        if new_brightness > 100:
            new_brightness = 100

        # minimum brightness is 5%
        if new_brightness < 5:
            new_brightness = 5

        # change the light to the new brightness
        self.turn_on(self.light_group, brightness_pct=new_brightness)
        self.call_service(
            'logbook/log',
            entity_id=self.actuator,
            domain='automation',
            name='pico_light: ',
            message=('{} brightness changed from {} to {}'.format(
                self.light_group,
                old_brightness,
                new_brightness)
            )
        )

    def brighter(self, entity, attribute, old, new, kwargs):

        # increase the brightness by 10%
        self.change_brightness(10)

    def dimmer(self, entity, attribute, old, new, kwargs):

        # decrease the brightness by 10%
        self.change_brightness(-10)
