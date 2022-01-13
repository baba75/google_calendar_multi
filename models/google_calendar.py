# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import requests
from dateutil import parser
import json
import logging
import operator
import pytz
from werkzeug import urls

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import exception_to_unicode

_logger = logging.getLogger(__name__)

def status_response(status):
    return int(str(status)[0]) == 2

class GoogleCalendar(models.AbstractModel):
    STR_SERVICE = 'calendar'
    _inherit = 'google.%s' % STR_SERVICE

    def get_calendar_id(self):
        """ If exists, return the secondary calendar id"""
        res = "primary"
        # magic here
        # self.env['product.template'].search([("name", "like", "Toner Microbond")])[0]
        ecid = self.env.user.google_calendar_extra_cal_id
        if ecid:
            if len(ecid) > 0:
                res = ecid
        return res

    def create_an_event(self, event):
        """ Create a new event in google calendar from the given event in Odoo.
            :param event : record of calendar.event to export to google calendar
        """
        data = self.generate_data(event, isCreating=True)

        url = "/calendar/v3/calendars/%s/events?fields=%s&access_token=%s" % (
        self.get_calendar_id(), urls.url_quote('id,updated'), self.get_token())
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data_json = json.dumps(data)
        try:
            return self.env['google.service']._do_request(url, data_json, headers, type='POST')
        except requests.HTTPError as e:
            try:
                response = e.response.json()
                error = response.get('error', {}).get('message')
            except Exception:
                error = None
            if not error:
                raise e
            message = _('The event "%s", %s (ID: %s) cannot be synchronized because of the following error: %s') % (
                event.name, event.start, event.id, error
            )
            raise UserError(message)

    def delete_an_event(self, event_id):
        """ Delete the given event in chosen calendar of google cal.
            :param event_id : google cal identifier of the event to delete
        """
        params = {
            'access_token': self.get_token()
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        url = "/calendar/v3/calendars/%s/events/%s" % (self.get_calendar_id(), event_id)

        return self.env['google.service']._do_request(url, params, headers, type='DELETE')

    def get_calendar_primary_id(self):
        """ In google calendar, you can have multiple calendar. But only one is
            the 'primary' one. This Calendar identifier is 'primary'.
            This function is modified to allow custom id calendar
        """
        params = {
            'fields': 'id',
            'access_token': self.get_token()
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/calendar/v3/calendars/%s" % self.get_calendar_id()

        try:
            status, content, ask_time = self.env['google.service']._do_request(url, params, headers, type='GET')
        except requests.HTTPError as e:
            if e.response.status_code == 401:  # Token invalid / Acces unauthorized
                error_msg = _("Your token is invalid or has been revoked !")

                self.env.user.write({'google_calendar_token': False, 'google_calendar_token_validity': False})
                self.env.cr.commit()

                raise self.env['res.config.settings'].get_config_warning(error_msg)
            raise

        return (status_response(status), content['id'] or False, ask_time)

    def get_event_synchro_dict(self, lastSync=False, token=False, nextPageToken=False):
        """ Returns events on the chosen calendar from google cal.
            :returns dict where the key is the google_cal event id, and the value the details of the event,
                    defined at https://developers.google.com/google-apps/calendar/v3/reference/events/list
        """
        if not token:
            token = self.get_token()

        params = {
            'fields': 'items,nextPageToken',
            'access_token': token,
            'maxResults': 1000,
        }

        if lastSync:
            params['updatedMin'] = lastSync.strftime("%Y-%m-%dT%H:%M:%S.%fz")
            params['showDeleted'] = True
        else:
            params['timeMin'] = self.get_minTime().strftime("%Y-%m-%dT%H:%M:%S.%fz")

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/calendar/v3/calendars/%s/events" % self.get_calendar_id()
        if nextPageToken:
            params['pageToken'] = nextPageToken

        status, content, ask_time = self.env['google.service']._do_request(url, params, headers, type='GET')

        google_events_dict = {}
        for google_event in content['items']:
            google_events_dict[google_event['id']] = google_event

        if content.get('nextPageToken'):
            google_events_dict.update(
                self.get_event_synchro_dict(lastSync=lastSync, token=token, nextPageToken=content['nextPageToken'])
            )

        return google_events_dict

    def get_one_event_synchro(self, google_id):
        token = self.get_token()

        params = {
            'access_token': token,
            'maxResults': 1000,
            'showDeleted': True,
        }

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/calendar/v3/calendars/%s/events/%s" % (self.get_calendar_id(), google_id)
        try:
            status, content, ask_time = self.env['google.service']._do_request(url, params, headers, type='GET')
        except Exception as e:
            _logger.info("Calendar Synchro - In except of get_one_event_synchro")
            _logger.info(exception_to_unicode(e))
            return False

        return status_response(status) and content or False

    def update_an_event(self, event):
        data = self.generate_data(event)
        url = "/calendar/v3/calendars/%s/events/%s" % (self.get_calendar_id(), event.google_internal_event_id)
        headers = {}
        data['access_token'] = self.get_token()

        status, response, ask_time = self.env['google.service']._do_request(url, data, headers, type='GET')
        # TO_CHECK : , if http fail, no event, do DELETE ?
        return response

    def update_recurrent_event_exclu(self, instance_id, event_ori_google_id, event_new):
        """ Update event on google calendar
            :param instance_id : new google cal identifier
            :param event_ori_google_id : origin google cal identifier
            :param event_new : record of calendar.event to modify
        """
        data = self.generate_data(event_new)
        url = "/calendar/v3/calendars/%s/events/%s?access_token=%s" % (self.get_calendar_id(), instance_id, self.get_token())
        headers = {'Content-type': 'application/json'}

        _originalStartTime = dict()
        if event_new.allday:
            _originalStartTime['date'] = event_new.recurrent_id_date.strftime("%Y-%m-%d")
        else:
            _originalStartTime['dateTime'] = event_new.recurrent_id_date.strftime("%Y-%m-%dT%H:%M:%S.%fz")

        data.update(
            recurringEventId=event_ori_google_id,
            originalStartTime=_originalStartTime,
            sequence=self.get_sequence(instance_id)
        )
        data_json = json.dumps(data)
        return self.env['google.service']._do_request(url, data_json, headers, type='PUT')

    def get_sequence(self, instance_id):
        params = {
            'fields': 'sequence',
            'access_token': self.get_token()
        }
        headers = {'Content-type': 'application/json'}
        url = "/calendar/v3/calendars/%s/events/%s" % (self.get_calendar_id(), instance_id)
        status, content, ask_time = self.env['google.service']._do_request(url, params, headers, type='GET')
        return content.get('sequence', 0)