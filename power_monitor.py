import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime
import time

class PowerMonitor(hass.Hass):

    def initialize(self):

        self.max_idle_seconds = self.args['max_idle_seconds']
        self.notify = self.args['notify']
        self.notify_message = self.args['notify_message']
        self.notify_target = self.args['notify_target']
        self.notify_title = self.args['notify_title']
        self.off_load = self.args['off_load']
        self.on_load = self.args['on_load']
        self.sensor_entity = self.args['sensor_entity']
        self.start_time = None
        self.stop_time = None
        self.tracking_entity = self.args['tracking_entity']
        self.idle_timer = None

        self.listen_state(self.sensor_report, self.sensor_entity)

    def sensor_report(self, entity, attribute, old, new, kwargs):

        # get the current state of the entity
        entity_state = self.get_state(self.tracking_entity, attribute='state')
        
        if float(new) <= self.off_load and entity_state == 'Running':
            # start an idle timer if one is not already running
            if self.idle_timer is None:
                self.idle_timer = self.run_in(self.entity_idle, self.max_idle_seconds)
        
        elif float(new) >= self.on_load and entity_state == 'Idle':
            # mark the entity as running
            self.select_option(self.tracking_entity, 'Running')

            # track the start time
            self.start_time = datetime.now()

            # cancel any running idle timers
            if self.idle_timer is not None:
                self.cancel_timer(self.idle_timer)

            self.log("{} is running.".format(self.sensor_entity), level='INFO')

    def entity_idle(self, kwargs):

        # get the current state of the entity
        entity_state = self.get_state(self.tracking_entity, attribute='state')

        if entity_state is not 'Idle':
            # mark the entity as idle
            self.select_option(self.tracking_entity, 'Idle')

            # track the stop time
            self.stop_time = datetime.now()

            if self.notify is True:
                tdelta = self.stop_time - self.start_time
                elapsed_time = time.strftime('%H:S', tdelta)

                self.notify_message += ("Elapsed time {}".format(elapsed_time))
                
                # send out the notification
                self.call_service(self.notify_target, title=self.notify_title,
                  message=self.notify_message)                

            self.log("{} is off.".format(self.sensor_entity), level='INFO')

                