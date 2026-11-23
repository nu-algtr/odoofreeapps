from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ------------------------------------------------------------------
    # Approval workflow
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
        ],
        string='Status', default='draft', tracking=True,
        readonly=True, copy=False, index=True, required=True,
    )
    is_approved = fields.Boolean(
        string='Approved Partner', default=False, tracking=True, copy=False)
    approver_user_id = fields.Many2one(
        'res.users', string='Approved by', readonly=True, tracking=True, copy=False)
    is_button_visible = fields.Boolean(
        string='Current User Is Approver', compute='_compute_approval_buttons')
    button_visible_draft = fields.Boolean(
        string='Current User May Reset', compute='_compute_approval_buttons')

    # ------------------------------------------------------------------
    # Classification and codes
    # ------------------------------------------------------------------
    is_child = fields.Boolean(
        string='Is Contact For Partner', compute='_compute_is_child', store=True)
    is_customer = fields.Boolean(string='Is Customer')
    is_vendor = fields.Boolean(string='Is Vendor')
    is_employee = fields.Boolean(string='Is Employee')
    customer_code = fields.Char(string='Customer Code', copy=False, index=True)
    vendor_code = fields.Char(string='Vendor Code', copy=False, index=True)
    employee_code = fields.Char(string='Employee ID', copy=False, index=True)
    customers_vendor_code = fields.Char(
        string="Customer's Vendor Code", index=True)

    # ------------------------------------------------------------------
    # Contact details
    # ------------------------------------------------------------------
    title = fields.Many2one('res.partner.title', string='Title')
    birth_date = fields.Date(string='Birth Date')
    anniversary_date = fields.Date(string='Anniversary Date')
    fax_no = fields.Char(string='Fax No')
    department_id = fields.Char(string='Department')
    region_id = fields.Many2one('contact.region', string='Region')
    company_revenue = fields.Char(string='Company Revenue')
    total_employee = fields.Char(string='Total Employees')

    # ------------------------------------------------------------------
    # Purchase terms fields
    # ------------------------------------------------------------------
    purchase_freight = fields.Char(string='Freight')
    purchase_insurance = fields.Char(string='Insurance')
    purchase_other_terms = fields.Char(string='Other')
    purchase_term = fields.Char(string='Term')
    purchase_guarantee = fields.Char(string='Guarantee')
    purchase_warranty = fields.Char(string='Warranty')
    purchase_remarks = fields.Text(string='Remarks')
    purchase_terms_conditions = fields.Text(string='Terms and Conditions')
    purchase_transport_mode = fields.Char(string='Transport Mode')

    # ------------------------------------------------------------------
    # Banking import helpers
    # ------------------------------------------------------------------
    bank_name = fields.Char(string='Bank Name')
    account_no = fields.Char(string='Account Number')

    _employee_code_unique = models.Constraint(
        'unique(employee_code)',
        'Another Partner exists in the system with the same Employee ID.'
        ' Employee ID should be unique.',
    )
    _customer_code_unique = models.Constraint(
        'unique(customer_code)',
        'Another Partner exists in the system with the same Customer Code.'
        ' Customer Code should be unique.',
    )
    _vendor_code_unique = models.Constraint(
        'unique(vendor_code)',
        'Another Partner exists in the system with the same Vendor Code.'
        ' Vendor Code should be unique.',
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('parent_id')
    def _compute_is_child(self):
        for partner in self:
            partner.is_child = bool(partner.parent_id)

    @api.depends('state')
    @api.depends_context('uid', 'company')
    def _compute_approval_buttons(self):
        is_approver = self._current_user_is_approver()
        may_reset = is_approver or self.env.user.has_group(
            'partner_extension.group_partner_set_to_draft')
        for partner in self:
            partner.is_button_visible = is_approver
            partner.button_visible_draft = may_reset

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id',
                 'commercial_company_name', 'customer_code', 'vendor_code', 'city')
    @api.depends_context(
        'show_address', 'partner_show_db_id', 'show_email', 'show_vat', 'lang',
        'formatted_display_name', 'show_code_city',
    )
    def _compute_display_name(self):
        super()._compute_display_name()
        context = self.env.context
        if context.get('formatted_display_name'):
            return
        for partner in self:
            if context.get('show_vat') and partner.vendor_code:
                partner.display_name = f'[{partner.vendor_code}] {partner.display_name}'
            elif context.get('show_code_city'):
                name = partner.display_name
                location = partner.city or partner.state_id.name
                if partner.customer_code:
                    name = f'[{partner.customer_code}] {name}'
                if location:
                    name = f'{name} ({location})'
                partner.display_name = name

    # ------------------------------------------------------------------
    # Approved lock
    # ------------------------------------------------------------------
    def _approved_locked_fields(self):
        """Fields that may not change while the partner is approved."""
        return [
            # identity
            'name', 'company_type', 'is_company', 'parent_id', 'company_name',
            'function', 'title', 'type', 'lang', 'ref', 'industry_id',
            'category_id',
            'user_id', 'website',
            # address and contact
            'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
            'phone', 'email', 'fax_no',
            # codes and classification
            'is_customer', 'is_vendor', 'is_employee', 'customer_code',
            'vendor_code', 'employee_code', 'customers_vendor_code',
            # fiscal
            'vat', 'company_registry',
            # banking
            'bank_name', 'account_no',
            # accounting properties
            'property_account_position_id', 'property_account_receivable_id',
            'property_account_payable_id', 'property_payment_term_id',
            'property_supplier_payment_term_id', 'property_product_pricelist',
            'property_stock_customer', 'property_stock_supplier',
            # commercial
            'team_id', 'region_id',
            'company_revenue', 'total_employee',
            # purchase terms
            'purchase_freight', 'purchase_insurance', 'purchase_other_terms',
            'purchase_term', 'purchase_guarantee', 'purchase_warranty',
            'purchase_remarks', 'purchase_terms_conditions', 'purchase_transport_mode',
        ]

    def _check_approved_lock(self, vals):
        if self.env.context.get('skip_approved_lock'):
            return
        locked_fields = set(self._approved_locked_fields())
        modifying_fields = set(vals.keys()) & locked_fields
        if not modifying_fields:
            return
        approved = self.filtered(lambda partner: partner.state == 'approved')
        if approved:
            raise UserError(_(
                'Partner "%(partner)s" is approved and cannot be edited or saved.'
                ' Click "Set to Draft" to make changes.',
                partner=approved[0].display_name,
            ))

    def write(self, vals):
        self._check_approved_lock(vals)
        return super().write(vals)

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        search_mode = self.env.context.get('res_partner_search_mode')
        if search_mode == 'customer' and 'is_customer' in fields_list:
            res['is_customer'] = True
        elif search_mode == 'supplier' and 'is_vendor' in fields_list:
            res['is_vendor'] = True
        return res

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if self.env.context.get('import_file') or self.env.context.get('install_mode'):
            for partner, vals in zip(partners, vals_list):
                partner._import_bank_details(vals)
                if vals.get('is_approved') or vals.get('state') == 'approved':
                    partner.with_context(force_approve=True).button_approve_partner()
        return partners

    def _import_bank_details(self, vals):
        self.ensure_one()
        account_number = vals.get('account_no')
        if not account_number:
            return
        bank = self.env['res.bank']
        bank_name = vals.get('bank_name')
        if bank_name:
            bank = bank.search([('name', '=', bank_name)], limit=1)
            if not bank:
                bank = bank.sudo().create({'name': bank_name})
        self.env['res.partner.bank'].sudo().create({
            'acc_number': account_number,
            'partner_id': self.id,
            'bank_id': bank.id or False,
        })

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def button_approve_partner(self):
        self.ensure_one()
        self._check_approval_rights()
        self._check_mandatory_before_approval()

        self.with_context(skip_approved_lock=True).write({
            'state': 'approved',
            'is_approved': True,
            'approver_user_id': self.env.user.id,
        })
        self._assign_partner_codes()
        self._clear_partner_approval_activities()

        recipients = (self.create_uid.partner_id | self.write_uid.partner_id)
        self.message_post(
            body=_('Partner %s has been approved.', self.display_name),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
            author_id=self.env.user.partner_id.id,
            partner_ids=recipients.ids,
        )
        return True

    def _clear_partner_approval_activities(self):
        for partner in self:
            activities = self.env['mail.activity'].search([
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', partner.id),
                ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ])
            activities.action_feedback(feedback=_("Handled via approval action."))

    def button_ask_partner_approval(self):
        self.ensure_one()
        approvers = self._approver_partners()
        if not approvers:
            raise UserError(_(
                'Partner Approvers are not configured, please contact your'
                ' Administrator to configure Partner Approvers.'))

        template = self.env.ref(
            'partner_extension.mail_template_partner_approval_request',
            raise_if_not_found=False)
        for approver in approvers.filtered('email'):
            if template:
                template.send_mail(
                    self.id, force_send=True,
                    email_values={'email_to': approver.email})

        for approver_user in self.env.company.partner_approver_ids:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=approver_user.id,
                summary=_('Partner Approval Required'),
                note=_('Please review and approve partner: %s') % self.display_name,
            )

        self.message_post(
            body=_('Approval requested from %s.',
                   ', '.join(approvers.mapped('display_name'))),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
            author_id=self.env.user.partner_id.id,
            partner_ids=approvers.ids,
        )
        return True

    def button_draft(self):
        self.ensure_one()
        if not (self._current_user_is_approver() or self.env.user.has_group(
                'partner_extension.group_partner_set_to_draft')):
            raise UserError(_(
                'You can not set this Partner to draft state. Only Partner'
                ' Approvers can set it to draft for editing purpose.'))
        self.with_context(skip_approved_lock=True).write({
            'state': 'draft',
            'is_approved': False,
            'approver_user_id': False,
        })
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _approver_partners(self):
        return self.env.company.partner_approver_ids.partner_id

    def _current_user_is_approver(self):
        return self.env.user.partner_id in self._approver_partners()

    def _check_approval_rights(self):
        if self.env.context.get('force_approve'):
            return
        approvers = self._approver_partners()
        if not approvers:
            raise UserError(_(
                'No Partner Approver is configured in the system. Please contact'
                ' the administrator to configure a Partner Approver.'))
        if not self._current_user_is_approver():
            raise UserError(_(
                "You can not approve this Partner. Please click 'Ask for Partner"
                " Approval' to get this Partner approved by an approver"
                " configured in the system."))

    def _check_mandatory_before_approval(self):
        """Data quality gate."""
        for partner in self:
            if not (partner.is_customer or partner.is_vendor):
                continue
            missing = [
                label for label, value in (
                    (_('Country'), partner.country_id),
                ) if not value
            ]
            if missing:
                raise ValidationError(_(
                    '%(fields)s are mandatory and not set on partner %(partner)s.',
                    fields=', '.join(missing), partner=partner.display_name))

    def _assign_partner_codes(self):
        """Draw the vendor / customer code from its sequence on approval."""
        for partner in self:
            values = {}
            if partner.is_vendor and not partner.vendor_code:
                values['vendor_code'] = partner._next_code(
                    'partner_extension.vendor_sequence',
                    'partner_extension.seq_vendor_code', _('Vendor'))
            if partner.is_customer and not partner.customer_code:
                values['customer_code'] = partner._next_code(
                    'partner_extension.customer_sequence',
                    'partner_extension.seq_customer_code', _('Customer'))
            if values:
                partner.with_context(skip_approved_lock=True).write(values)

    def _next_code(self, parameter, fallback_xmlid, label):
        sequence_id = self.env['ir.config_parameter'].sudo().get_param(parameter)
        sequence = self.env['ir.sequence']
        if sequence_id and str(sequence_id).isdigit():
            sequence = sequence.browse(int(sequence_id)).exists()
        if not sequence:
            sequence = self.env.ref(fallback_xmlid, raise_if_not_found=False)
        if not sequence:
            raise ValidationError(_(
                'Please configure the %s sequence in Settings.', label))
        return sequence.sudo().next_by_id()
