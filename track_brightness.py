import appdaemon.plugins.hass.hassapi as hass


class TrackBrightness(hass.Hass):
    
    def initialize(self):

        self.listen_state(
            self.sun_event,
            entity_id='sun.sun'
        )

    def sun_event(self, event_name, data, kwargs):

        self.log(self.actuator + " sun event", level='INFO')