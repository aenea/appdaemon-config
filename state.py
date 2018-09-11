import appdaemon.plugins.hass.hassapi as hass
from astral import *
import datetime
import pytz

# Track global states, including desired bulb color temperature,
# home occupancy, day/night, and quiet mode


class State(hass.Hass):

    def initialize(self):

        # run the color temperature calculation every 5 minutes
        self.register_constraint("is_daylight")
        self.periodic = self.run_every(
            self.calc_temp,
            datetime.datetime.now(),
            5 * 60,
            is_daylight=1
        )

        # track the sleeping binary sensor
        self.listen_state(
            self.quiet_mode,
            'binary_sensor.sleeping'
        )

        # track day time
        self.run_at_sunrise(self.start_day_mode)

        # track night time
        self.run_at_sunset(self.start_night_mode)

        # track presence
        self.listen_state(
            self.occupancy_mode,
            'group.presence.all'
        )

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

    def is_daylight(self, value):
        if self.sun_up():
            return True
        else:
            return False

    def calc_temp(self, kwargs):

        # get the hass config
        config = self.get_hass_config()

        # get the sun event information
        a = Astral()
        home = location = Location(info=(
            'Marsyville',
            'Ohio',
            config['latitude'],
            config['longitude'],
            config['time_zone'],
            config['elevation'])
        )
        sun = home.sun()
        sunrise = sun['sunrise']
        solar_noon = sun['noon']
        sunset = sun['sunset']

        now = datetime.datetime.now(pytz.timezone(config['time_zone']))

        if now < sunrise or now > sunset:
            # use the sunset ct if the time is after sunset
            target_temp = int(float(self.get_state(
                'input_number.ct_sunset',
                attribute='state'
            )))
        elif now < solar_noon:
            # how much time has elapsed from sunset to now?
            before_noon = solar_noon - sunrise
            elapsed_time = now - sunrise
            elapsed_pct = elapsed_time / before_noon

            # get the sunrise and noon color temperatures
            sunrise_temp = int(float(self.get_state(
                'input_number.ct_sunrise',
                attribute='state'
            )))
            noon_temp = int(float(self.get_state(
                'input_number.ct_noon',
                attribute='state'
            )))
            temp_change = noon_temp - sunrise_temp

            target_temp = int(sunrise_temp + (temp_change * elapsed_pct))
        else:
            # how much time has elapsed from solar noon to now?
            after_noon = sunset - solar_noon
            elapsed_time = now - solar_noon
            elapsed_pct = elapsed_time / after_noon

            # get the noon and sunset color temperatures
            sunset_temp = int(float(self.get_state(
                'input_number.ct_sunset',
                attribute='state'
            )))
            noon_temp = int(float(self.get_state(
                'input_number.ct_noon',
                attribute='state'
            )))
            temp_change = sunset_temp - noon_temp

            target_temp = int(noon_temp + (temp_change * elapsed_pct))

        self.call_service(
            'input_number/set_value',
            entity_id='input_number.ct_target',
            value=target_temp
        )

    def occupancy_mode(self, entity, attribute, old, new, kwargs):

        # set the quiet mode boolean to the appropriate state
        if new == 'home':
            self.turn_on('input_boolean.home_occupancy')
            self.log('home occupancy turned on ' + self.current_state)
        else if new == 'not_home':
            self.turn_off('input_boolean.home_occupancy')
            self.log('home occupancy turned off ' + self.current_state)

    def quiet_mode(self, entity, attribute, old, new, kwargs):

        # set the quiet mode boolean to the appropriate state
        if new == 'on':
            self.turn_on('input_boolean.quiet_mode')
            self.log('quiet mode turned on ' + self.current_state)
        else if new == 'off':
            self.turn_off('input_boolean.quiet_mode')
            self.log('quiet mode turned off ' + self.current_state)

    def start_day_mode():

        self.turn_off('input_boolean.night_mode')
        self.log('night mode turned off ' + self.current_state)

    def start_night_mode():

        self.turn_on('input_boolean.night_mode')
        self.log('night mode turned on ' + self.current_state)