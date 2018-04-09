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
        ct_group = self.get_state('group.ct_bulbs', 'all')
        ct_bulbs = ct_group['attributes']['entity_id']

        self.log(ct_bulbs)
        #self.call_service('homeassistant/turn_on', entity_id='light.living_room_1', kelvin=target_temp)
        #self.call_service('homeassistant/turn_on', entity_id='light.living_room_2', kelvin=target_temp)




        



