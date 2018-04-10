import appdaemon.plugins.hass.hassapi as hass

# LightControl
#
# light_on - provides predicatable results for color temperature
#  lights as they turn on.
#
# target_temp_change - changes the color temperature of the ct lights as
#  the target color temperature changes throughout the day.
#
# Args:
#
# ct_group_entity - A group containing the color temperature lights to manage
# target_temp_entity - An input_number that tracks the target
#  color temperature
#


class LightControl(hass.Hass):

    def initialize(self):
        self.ct_group = self.args['ct_group_entity']
        self.target_temp = self.args['target_temp_entity']

        # get the list of lights in the ct_group
        ct_group = self.get_state(self.ct_group, attribute='all')
        ct_lights = ct_group['attributes']['entity_id']

        # monitor the turn on event for the color temperature lights
        for ct_light in ct_lights:
            self.listen_state(self.light_on, ct_light, new='on', old='off')
            self.call_service(
                'logbook/log',
                entity_id=ct_light,
                domain='automation',
                name='ct_light: ',
                message=(
                    'monitoring {} for turn on events'.format(ct_light)
                )
            )

        # monitor changes in the target color temperature
        self.listen_state(self.target_temp_change, self.target_temp)

    def light_on(self, entity, attribute, old, new, kwargs):

        # get the current target color temperature
        target_temp = int(float(self.get_state(
            self.target_temp,
            attribute='state'
        )))

        # set the light to the target color temperature
        self.call_service(
            'homeassistant/turn_on',
            entity_id=entity,
            brightness_pct=100,
            kelvin=target_temp
        )

    def target_temp_change(self, entity, attribute, old, new, kwargs):

        # get the list of color temperature enabled bulbs
        ct_group = self.get_state(self.ct_group, attribute='all')
        ct_lights = ct_group['attributes']['entity_id']

        # set the lights that are on to the current color temperature
        for ct_light in ct_lights:
            light_state = self.get_state(ct_light, attribute='state')
            if light_state == 'on':
                self.call_service(
                    'homeassistant/turn_on',
                    entity_id=ct_light,
                    kelvin=target_temp
                )