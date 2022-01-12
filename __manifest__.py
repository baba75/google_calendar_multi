# -*- coding: utf-8 -*-
{
    'name': "Google Calendar Multi",

    'summary': """
        Allows to use Google secondary calendars.""",

    'description': """
        The Odoo module google_calendar use the 'primary' calendar
        by default. This module allow to use other google (secondary) calendars.
    """,

    'author': "Alberto Carollo",
    'website': "https://github.com/baba75/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['google_calendar'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/templates.xml',
    ],

}