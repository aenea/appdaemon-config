import appdaemon.plugins.hass.hassapi as hass
from astral import *
import datetime
import pytz

class ColorTemperature(hass.Hass):

    def initialize(self):

        # run the color temperature calculation every 5 minutes
        self.periodic = self.run_every(
            self.calc_temp,
            datetime.datetime.now(),
            5 * 60
        )

        # get the list of color temperature enabled lights
        ct_group = self.get_state('group.ct_lights', attribute='all')
        ct_lights = ct_group['attributes']['entity_id']

        # hook the turn on event for the color temperature lights
        for ct_light in ct_lights:            
            self.listen_state(self.light_on, ct_light, new='on', old='off')
            self.log(ct_light)
            self.call_service(
                'logbook/log',
                entity_id=ct_light,
                domain='automation',
                name='ct_light: ',
                message=(
                    'monitoring {} for turn on events'.format(ct_light)
                )
            )

    def light_on(self, entity, attribute, old, new, kwargs):

        # get the current target color temperature
        target_temp = int(float(self.get_state(
            'input_number.kelvin_sunset',
            attribute='state'
        )))

        # set the light to the target color temperature
        self.call_service(
            'homeassistant/turn_on',
            entity_id=entity,
            kelvin=target_temp
        )
        
    def calc_temp(self, kwargs):

        # get the sun event information
        a = Astral()
        home = location = Location(info=(
            'Marsyville',
            'Ohio',
            40.334872,
            -83.312793,
            'America/New_York',
            965)
        )
        sun = home.sun()
        sunrise = sun['sunrise']
        solar_noon = sun['noon']
        sunset = sun['sunset']

        now = datetime.datetime.now(pytz.timezone('America/New_York'))

        if now < sunrise or now > sunset:
            # get the target color temperatures
            target_temp = int(float(self.get_state(
                'input_number.kelvin_sunset',
                attribute='state'
            )))
        elif now < solar_noon:
            # how much time has elapsed from sunset to now?
            before_noon = solar_noon - sunrise
            elapsed_time = now - sunrise
            elapsed_pct = elapsed_time / before_noon

            # get the target color temperatures
            sunrise_temp = int(float(self.get_state(
                'input_number.kelvin_sunrise',
                attribute='state'
            )))
            noon_temp = int(float(self.get_state(
                'input_number.kelvin_noon',
                attribute='state'
            )))
            temp_change = noon_temp - sunrise_temp

            target_temp = int(sunrise_temp + (temp_change * elapsed_pct))
        else:
            # how much time has elapsed from solar noon to now?
            after_noon = sunset - solar_noon
            elapsed_time = now - solar_noon
            elapsed_pct = elapsed_time / after_noon

            # get the target color temperatures
            sunset_temp = int(float(self.get_state(
                'input_number.kelvin_sunset',
                attribute='state'
            )))
            noon_temp = int(float(self.get_state(
                'input_number.kelvin_noon',
                attribute='state'
            )))
            temp_change = sunset_temp - noon_temp

            target_temp = int(noon_temp + (temp_change * elapsed_pct))

        self.log(target_temp)
        self.set_value('input_number.kelvin_current', target_temp)

        # get the list of color temperature enabled bulbs
        ct_group = self.get_state('group.ct_lights', attribute='all')
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

