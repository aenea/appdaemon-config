import appdaemon.plugins.hass.hassapi as hass
#
# Provides multi tap support for the Homeseer dimmer
# switches
#
# Requires the following to be add to the zwave configuration
# for each device:
#			<CommandClass id="91" name="COMMAND_CLASS_CENTRAL_SCENE" version="1" request_flags="4" innif="true" scenecount="0">
#				<Instance index="1" />
#				<Value type="int" genre="system" instance="1" index="0" label="Scene Count" units="" read_only="true" write_only="false" verify_changes="false" poll_intensity="0" min="-2147483648" max="2147483647" value="2" />
#				<Value type="int" genre="user" instance="1" index="1" label="Top Button Scene" units="" read_only="false" write_only="false" verify_changes="false" poll_intensity="0" min="-2147483648" max="2147483647" value="3" />
#				<Value type="int" genre="user" instance="1" index="2" label="Bottom Button Scene" units="" read_only="false" write_only="false" verify_changes="false" poll_intensity="0" min="-2147483648" max="2147483647" value="1" />
#			</CommandClass>
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
            self.log(self.actuator + " double tapped on", level='INFO')
        
    def scene_off(self, event_name, data, kwargs):
        
        if self.scene_id == 3 or self.scene_id == 7860:
            # Turn brightness to 2% when bottom is double tapped.
            self.turn_on(self.actuator, brightness_pct=2)
            self.log(self.actuator + " double tapped off", level='INFO')

        elif self.scene_id == 4 or self.scene_id == 7920: 
            # Trigger bed time routine when bottom is triple tapped.
            self.turn_on('input_boolean.bed_time')
            self.log("{} triple tapped off".format(
                self.actuator), level='INFO'
            )

        