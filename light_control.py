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
        self.active_modes = [x.casefold() for x in self.args['active_modes']]
        self.ct_group = self.args['ct_group_entity']
        self.target_temp = self.args['target_temp_entity']

        # get the list of lights in the ct_group
        ct_group = self.get_state(self.ct_group, attribute='all')
        ct_lights = ct_group['attributes']['entity_id']

        # monitor the turn on event for the color temperature lights
        for ct_light in ct_lights:
            self.listen_state(self.light_on, ct_light, new='on', old='off')

        # monitor the turn off event for the color temperature lights
        for ct_light in ct_lights:
            self.listen_state(self.light_off, ct_light, new='off', old='on')

        # monitor changes in the target color temperature
        self.listen_state(self.target_temp_change, self.target_temp)

    @property
    def guest_mode(self):
        return self.get_state('input_boolean.guest_mode')

    @property
    def moonlight(self):
        return self.get_state('input_boolean.moonlight')

    @property
    def night_mode(self):
        return self.get_state('input_boolean.night_mode')

    @property
    def quiet_mode(self):
        return self.get_state('input_boolean.quiet_mode')

    @property
    def allowed_mode(self):

        # is the automation mode in an allowed state?
        if 'away' in self.disabled_modes:
            if self.home_occupancy == 'off':
                self.log(
                    'automation declined for occupancy - ' +
                    self.current_state
                )
                return False
        if 'guest' in self.disabled_modes:
            if self.guest_mode == 'on':
                self.log(
                    'automation declined for guest mode - ' +
                    self.current_state
                )
                return False
        if 'quiet' in self.disabled_modes:
            if self.quiet_mode == 'on':
                self.log(
                    'automation declined for quiet mode - ' +
                    self.current_state
                )
                return False

        return True

    @property
    def current_state(self):

        return (
            'current_state('
            'guest_mode=%s, '
            'moonlight=%s, '
            'night_mode=%s, '
            'quiet_mode=%s, '
            ')'
            %
            (
                self.guest_mode,
                self.moonlight,
                self.night_mode,
                self.quiet_mode,
            )
        )

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
            kelvin=target_temp
        )

    def light_off(self, entity, attribute, old, new, kwargs):

        # get the light tags
        ct_controlled = self.get_state(entity, attribute='ct_controlled')

        if ct_controlled == 'true':
            # untag the light
            self.set_state(
                ct_light,
                attributes={'ct_controlled': 'false'}
            )

    def target_temp_change(self, entity, attribute, old, new, kwargs):

        # is the automation in an allowed state?
        self.disabled_modes = set(['guest'])
        if self.allowed_mode is False:
            self.log(
                'light kelvin tracking declined - ' +
                self.current_state
            )
            return

        # get the list of color temperature enabled bulbs
        ct_group = self.get_state(self.ct_group, attribute='all')
        ct_lights = ct_group['attributes']['entity_id']
        new = int(float(new))

        # set the lights that are on to the current color temperature
        for ct_light in ct_lights:
            # get the light state
            light_state = self.get_state(ct_light, attribute='state')
            if light_state == 'on':
                self.call_service(
                    'homeassistant/turn_on',
                    entity_id=ct_light,
                    kelvin=new
                )
                # tag the light
                self.set_state(
                    ct_light,
                    attributes={'ct_controlled': 'true'}
                )
