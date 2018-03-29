import appdaemon.plugins.hass.hassapi as hass


class TrackBrightness(hass.Hass):

    def initialize(self):

        self.listen_state(
            self.sun_event,
            'sun.sun'
        )

    def sun_event(self, entity, attribute, old, new, kwargs):

        self.log(new, level='INFO')
