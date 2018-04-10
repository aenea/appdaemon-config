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
