from odoo import api, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    @api.depends('name', 'code')
    def _compute_display_name(self):
        super()._compute_display_name()
        for state in self:
            if state.code:
                state.display_name = f'{state.name}-{state.code}'
