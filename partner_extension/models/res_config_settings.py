from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partner_approver_ids = fields.Many2many(
        'res.users', related='company_id.partner_approver_ids',
        string='Partner Approvers', readonly=False)
    partner_vendor_sequence_id = fields.Many2one(
        'ir.sequence', string='Vendor Code Sequence',
        config_parameter='partner_extension.vendor_sequence')
    partner_customer_sequence_id = fields.Many2one(
        'ir.sequence', string='Customer Code Sequence',
        config_parameter='partner_extension.customer_sequence')
