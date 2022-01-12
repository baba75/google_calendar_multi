# -*- coding: utf-8 -*-
from odoo import http

# class /mnt/moduliEcobeton/googleCalendarMulti(http.Controller):
#     @http.route('//mnt/moduli_ecobeton/google_calendar_multi//mnt/moduli_ecobeton/google_calendar_multi/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//mnt/moduli_ecobeton/google_calendar_multi//mnt/moduli_ecobeton/google_calendar_multi/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('/mnt/moduli_ecobeton/google_calendar_multi.listing', {
#             'root': '//mnt/moduli_ecobeton/google_calendar_multi//mnt/moduli_ecobeton/google_calendar_multi',
#             'objects': http.request.env['/mnt/moduli_ecobeton/google_calendar_multi./mnt/moduli_ecobeton/google_calendar_multi'].search([]),
#         })

#     @http.route('//mnt/moduli_ecobeton/google_calendar_multi//mnt/moduli_ecobeton/google_calendar_multi/objects/<model("/mnt/moduli_ecobeton/google_calendar_multi./mnt/moduli_ecobeton/google_calendar_multi"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/mnt/moduli_ecobeton/google_calendar_multi.object', {
#             'object': obj
#         })