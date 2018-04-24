import appdaemon.plugins.hass.hassapi as hass


class KitchenLights(hass.Hass):

    def initialize(self):

        self.listen_state(self.stage_lights, 'sun.sun')

    def stage_lights(self, entity, attribute, old, new, kwargs):

        # turn on the kitchen lights at low level at night if
        # the kitchen is unoccupied
        sun_elevation = float(self.get_state(
            'sun.sun',
            attribute='elevation'
        ))

        bed_time = self.get_state(
            'input_boolean.bed_time',
            attribute='state'
        )

        light_status = self.get_state(
            'light.kitchen_lights',
            attribute='state'
        )

        self.log(sun_elevation)

        if sun_elevation < 0 and bed_time is False and light_status == 'off':
            self.turn_on(
                'light.kitchen_sink_light_switch_level',
                brightness_pct=5
            )
            self.turn_on(
                'light.kitchen_table_pendants',
                brightness_pct=5
            )

