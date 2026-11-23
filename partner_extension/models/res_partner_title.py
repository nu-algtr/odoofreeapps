from odoo import fields, models


class ResPartnerTitle(models.Model):
    """Re-created here: Odoo 19 removed res.partner.title from base.

    Same shape as the model base used to ship, so Odoo 14 title data maps
    across unchanged.
    """
    _name = 'res.partner.title'
    _description = 'Partner Title'
    _order = 'name'

    name = fields.Char(string='Title', required=True, translate=True)
    shortcut = fields.Char(string='Abbreviation', translate=True)
    active = fields.Boolean(default=True)
