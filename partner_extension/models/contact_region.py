from odoo import fields, models


class ContactRegion(models.Model):
    _name = 'contact.region'
    _description = 'Contact Region'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Region', required=True, tracking=True)
    active = fields.Boolean(default=True)

    _name_unique = models.Constraint('unique(name)', 'Region already exists.')
