from odoo import _, models
from odoo.exceptions import UserError


class PartnerApproveButton(models.TransientModel):
    _name = 'partner.approve.button'
    _description = 'Approve Partners'

    def approve_multi_partners(self):
        partner_ids = self.env.context.get('active_ids')
        if not partner_ids:
            raise UserError(_('Please select the partners to approve.'))
        for partner in self.env['res.partner'].browse(partner_ids):
            if partner.state != 'approved':
                partner.button_approve_partner()
        return {'type': 'ir.actions.act_window_close'}
