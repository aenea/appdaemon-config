import appdaemon.plugins.hass.hassapi as hass
#
# Provides multi tap support for the Homeseer dimmer
# switches
#


class HomeseerSwitch(hass.Hass):

    def initialize(self):

        self.actuator = self.args['actuator_entity']
        self.scene_id = self.args['scene_id']
        self.zwave_entity = self.args['zwave_entity']

        self.listen_event(
            self.scene_on, event='zwave.scene_activated',
            entity_id=self.zwave_entity,
            scene_id=1, scene_data=self.scene_id
        )
        self.listen_event(
            self.scene_off, event='zwave.scene_activated',
            entity_id=self.zwave_entity,
            scene_id=2, scene_data=self.scene_id
        )

    def scene_on(self, event_name, data, kwargs):

        if self.scene_id == 3 or self.scene_id == 7860:
            # Turn brightness to 100% when top double tapped.
            self.turn_on(self.actuator, brightness_pct=100)
            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='homeseer_switch: ',
                message=('{} double tapped on'.format(
                    self.actuator)
                )
            )

    def scene_off(self, event_name, data, kwargs):

        if self.scene_id == 3 or self.scene_id == 7860:
            # Turn brightness to 2% when bottom is double tapped.
            self.turn_on(self.actuator, brightness_pct=2)
            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='homeseer_switch: ',
                message=('{} double tapped off'.format(
                    self.actuator)
                )
            )
        elif self.scene_id == 4 or self.scene_id == 7920:
            # Trigger bed time routine when bottom is triple tapped.
            self.turn_on('input_boolean.bed_time')
            self.call_service(
                'logbook/log',
                entity_id=self.actuator,
                domain='automation',
                name='homeseer_switch: ',
                message=('{} triple tapped off'.format(
                    self.actuator)
                )
            )
