# -*- coding: utf-8 -*-

from odoo import fields, models

class User(models.Model):

    _inherit = 'res.users'

    google_calendar_extra_cal_id = fields.Char('Secondary Calendar ID', copy=False, help='Last Calendar ID who has been synchronized. If it is changed, we remove all links between GoogleID and Odoo Google Internal ID')
