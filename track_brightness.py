import appdaemon.plugins.hass.hassapi as hass


class TrackBrightness(hass.Hass):

    def initialize(self):

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

        self.log(sun_elevation, level='INFO')
