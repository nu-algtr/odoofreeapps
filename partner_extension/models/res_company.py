from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    partner_approver_ids = fields.Many2many(
        'res.users', 'rel_partner_approver_ids', 'company_id', 'user_id',
        string='Partner Approvers',
        domain=[('share', '=', False)])
