import appdaemon.plugins.hass.hassapi as hass


class TrackBrightness(hass.Hass):

    def initialize(self):

        # set default values
        self.brightness = 100

        self.listen_state(
            self.sun_event,
            'sun.sun'
        )

    def sun_event(self, entity, attribute, old, new, kwargs):

        # check for guest mode
        sun_elevation = self.get_state(
            'sun.sun',
            attribute='elevation'
        )

        # calculate the default turn on brightness based on
        # sun elevation and cloud cover
        if sun_elevation < 5:
            self.brightness = 100
        elif sun_elevation < 20:
            self.brightness = 


        self.log(sun_elevation, level='INFO')
