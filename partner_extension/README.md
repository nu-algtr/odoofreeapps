# partner_extension (Odoo 19)

Migration of the EcoClean **Contacts** customisation from Odoo 14
(`odoo14/ecoclean-addons`) to Odoo 19.

In Odoo 14 the Contacts surface was customised from seven addons, each
inheriting `res.partner` and each xpath-ing into `base.view_partner_form`.
This module consolidates all of it:

| Odoo 14 addon | What came across |
| --- | --- |
| `partner_extension` | approval workflow, approvers, ribbons, filters, mass-approve wizard |
| `sale_extension` | `is_customer`, `customer_code`, `customers_vendor_code`, `master_ratio`, `region_id` + `contact.region`, `department_id`, `duns_id`, `sic_id`, `fax_no` |
| `purchase_extension` | `is_vendor`, `vendor_code` |
| `l10n_in_extension` | GSTIN duplicate control, TDS, IFSC/SWIFT, Indian address format, `en_IN` default |
| `crm_extension` | `company_revenue`, `total_employee`, industry placement |
| `hr_extension` | `is_employee`, `employee_code` |
| `accounting_extension` | the read-only-when-approved rule on the accounting properties |

## Framework changes applied

| Odoo 14 | Odoo 19 |
| --- | --- |
| `attrs="{'readonly': [('state','=','approved')]}"` | `readonly="state == 'approved'"` |
| `<tree>`, `view_mode="tree,form"` | `<list>`, `view_mode="list,form"` |
| `<div class="oe_chatter">` | `<chatter/>` |
| `res.users.groups_id` | `res.users.group_ids` |
| `res.groups.users` | `res.groups.user_ids` (via `user.has_group()`) |
| `res.groups.category_id` (`ir.module.category`) | `res.groups.privilege_id` (`res.groups.privilege`) |
| `name_get()` | `_compute_display_name()` |
| `res.partner._get_name()` | folded into `_compute_display_name()` |
| `@api.model def create(self, vals)` | `@api.model_create_multi def create(self, vals_list)` |
| `_sql_constraints = [...]` | `models.Constraint(...)` |
| `track_visibility='onchange'`, `tracking=3` | `tracking=True` |
| `bg_color="bg-info"` | `bg_color="text-bg-info"` |
| settings `div[@data-key]` + `o_setting_box` | `<app>` / `<block>` / `<setting>` |
| `_display_address()` copy | `_prepare_display_address()` override |
| `res.partner.title` in `base` | removed in Odoo 19 - model and field re-created here |

## View anchors that had to move

Odoo 19 rebuilt the partner form, so several Odoo 14 anchors no longer exist:

* `div.oe_title` - gone. The **Vendor Code / Customer Code / Employee ID** now
  sit in a row under the contact name inside `div.mb8`.
* `mobile` - the field no longer exists on `res.partner`. `birth_date`,
  `anniversary_date`, `department_id`, `fax_no` and `region_id` now sit in
  their own groups in the Contacts sub-form.
* `title` - Odoo 19 removed `res.partner.title` from base entirely, the
  **model as well as the field**. Both are re-created here
  (`models/res_partner_title.py`, same shape base used to ship, so Odoo 14
  title data maps across unchanged) with a **Titles** menu under
  Contacts > Configuration and five default titles in
  `data/res_partner_title_data.xml`.
* `base.res_partner_view_form_private` - the view no longer exists; the
  `hr_extension` override of it was dropped.
* `div[hasclass('alert')]` - Odoo 19's duplicate warning also covers the
  company registry, so it is no longer removed.
* The base contact **list** view in this Odoo build shows `complete_name`, not
  `display_name`; the list inheritance anchors on `complete_name`.

Anchors that still hold and are used as-is: `page[@name='sales_purchases']`,
`group[@name='sale']`, `page[@name='internal_notes']`,
`page[@name='accounting']`, `contacts.action_contacts`,
`contacts.res_partner_menu_config`, `account.res_partner_action_customer`,
`account.res_partner_action_supplier`.

## Deliberate design changes

**Read-only when approved is enforced on the server.** Odoo 14 expressed the
rule as ~40 per-field `attrs` spread over five addons, which any RPC write
bypassed. The rule now lives in `res.partner._approved_locked_fields()` and is
checked in `write()`; the form keeps `readonly` attributes on the fields users
actually touch, but they are cosmetic. To lock more fields from another addon,
extend `_approved_locked_fields()` - do not add `readonly` attributes.
Automated flows that must bypass it use
`partner.with_context(skip_approved_lock=True)`.

`child_ids` and `bank_ids` are deliberately **not** in that list even though
the form keeps them read-only: core writes those x2many fields from flows far
away from the partner form (payment registration, bank statement import,
adding a contact from the parent form), and refusing them there produces a
crash instead of a greyed-out widget.

**PAN adopted from core.** Odoo 19's `l10n_in` ships `l10n_in_pan_entity_id`
(a `l10n_in.pan.entity` record) and `l10n_in_tan`, with a built-in PAN/GSTIN
mismatch warning. The custom `pan_no` Char and its regex constraint were
dropped in favour of core; the PAN format check now runs against
`l10n_in_pan_entity_id.name` at approval time.

**TDS renamed to match core naming.** `tds_tax` -> `l10n_in_tds_tax_id` and
`tds_applicable` -> `l10n_in_tds_applicable`, with the domain
`[('l10n_in_tax_type', '=', 'tds_purchase')]`. The Odoo 14 domain
`[('type_tax_use', '=', 'tds')]` matches nothing in Odoo 19 - `type_tax_use`
has no `tds` value any more. The field names match
`precitech/custom_addons/contact_extension`, so the two clients stay portable.

**`is_employee` / `employee_code` have one owner.** Odoo 14 declared them
twice - plain stored fields in `partner_extension`, computed from
`hr.employee.address_home_id` in `hr_extension` - so behaviour depended on
module load order. They are plain stored fields here.
`hr.employee.address_home_id` no longer exists in Odoo 19 (the private address
moved to `hr.version`, and the partner link is `work_contact_id`), so there was
nothing to port; if the flag should follow an employee record again, add that
in an `hr`-dependent addon.

**`is_child` recomputes, and no longer hides the classification flags.** It was
declared `compute=..., store=True` but decorated `@api.constrains('parent_id')`,
so it never recomputed after creation - which meant Odoo 14's "hide Is Customer
/ Is Vendor / Is Employee for a contact" rule never actually fired in the form.
With the decorator corrected to `@api.depends('parent_id')` that dormant rule
started firing, so it was removed: the three flags, and the codes beside the
name, stay available on a contact that belongs to a company. `is_child` still
drives the Contact/Partner ribbons and the Partner/Contact search filters.

**Partner codes are editable.** Odoo 14 declared `customer_code` and
`vendor_code` `readonly=True` on the model, so they could only ever be filled
by the sequence. They are plain editable fields now, locked on approval;
`_assign_partner_codes()` still only draws from the sequence when the code is
empty at approval time.

**One `display_name` rule for `show_vat`.** Odoo 14 had two competing
`_get_name` overrides for the same context key - `purchase_extension` prefixed
the vendor code, `crm_extension` the customer code - and load order decided
which won. The consolidated `_compute_display_name` prefixes the **vendor**
code for `show_vat`, and the customer code plus city for `show_code_city`.

**The set-to-draft group has a privilege.** Odoo 19 grants groups on the user
form through `res.groups.privilege`; a group without one is reachable only from
Settings > Technical > Groups. The module ships a **Partner Approval**
privilege so *Allow Partner Set to Draft* appears with the other access rights.

**`en_IN` default is gated on the company country.** Odoo 14 forced
`lang = en_IN` on every new contact. It now applies only when the active
company's country is India, so the module can be installed on a non-Indian
database without changing every contact's language.

**GSTIN label not forced.** Odoo 19 labels `vat` from the company country
(`format.vat.label.mixin`), which gives *GSTIN* for India and *RFC* for
Mexico, so the hard-coded `string="GSTIN"` was dropped.

**IFSC / SWIFT are no longer required.** Odoo 14 declared both `required=True`
on `res.partner.bank`; a hard requirement on an inherited model blocks core
bank flows (the account setup wizard, statement imports, data import). The
approval gate is the place to enforce it.

**Unarchive checks reduced.** `customer_code`, `vendor_code` and
`employee_code` carry SQL unique constraints, which apply to archived rows too,
so only the GSTIN check remains in `action_unarchive()`.

**Approval e-mail is a template.** `button_ask_partner_approval` used to build
`mail.mail` records with inline HTML; it now renders
`mail_template_partner_approval_request`.

## Deliberately not migrated

* **Purchase order default terms** (`payment_term_id`, `packaging_id`,
  `freight_id`, `insurance_id`, `term_id`, `guarantee_id`, `warranty_id`,
  `purchase_terms`, `transport_mode`, `excise_duty_id`, `other_terms`,
  `remarks`) - these are Many2one fields pointing at master-data models owned
  by `purchase_extension` (`purchase.order.packaging`, `order.term`,
  `purchase.terms`, ...). They belong to that module's own migration.
* **`tds_section_id`, `tds_type`, `service_tax`, `excise_duty_id`** - already
  commented out of the Odoo 14 form; confirm with the client before
  reintroducing them.
* **MSME** (`is_msme`, `msme_no`, `msme_type` and the `msme.type` master
  model) - dropped at the client's request. Odoo 19's `l10n_in.pan.entity`
  carries `msme_type` and `msme_number` natively if it is ever needed again.
* **`purchase_extension.vendor_partner_tree_view` /
  `sale_extension.customer_partner_tree_view`** - two standalone contact list
  views. Odoo 14's `crm_extension` referenced the customer one through a
  `tree_view_ref` context, so whoever migrates `crm_extension` must re-point
  that reference, or these two views need adding here.
* **`account.setup_bank_account_wizard`** - Odoo 14 added the IFSC field to
  that wizard as well; only the `res.partner.bank` form carries it here.
* **`partner_dyanmic_api`** - the Microsoft Dynamics integration declares its
  own `state` selection on `res.partner`, which would collide with the
  approval workflow. Separate decision.

## Configuration

*Settings > General Settings > Partner*

* **Partner Approvers** - users who may approve (per company; stored on
  `res.company.partner_approver_ids`). **Until at least one approver is set
  nothing can be approved**: every user sees only *Ask for Partner Approval*,
  and pressing it reports that no approvers are configured.
* **Partner Codes** - the sequences drawn on approval. Defaults to the
  `partner.vendor.code` and `partner.customer.code` sequences shipped in
  `data/ir_sequence_data.xml`.
* **Allow Duplicate GSTIN** - `partner_extension.duplicate_vat_allowed`
  (renamed from `l10n_in_extension.duplicate_vat_allowed`).

Users granted **Partner Approval > Allow Partner Set to Draft** may reset an
approved partner even if they are not approvers.

## Data migration notes

* Carry over `state`, `is_approved`, `approver_user_id` - approval history is
  business data.
* Materialise `employee_code` values that the Odoo 14 `hr_extension` compute
  produced into the stored column.
* Map `pan_no` to `l10n_in.pan.entity` records and link
  `l10n_in_pan_entity_id`.
* `res_partner_bank.isfc_code` -> **`ifsc_code`**. Odoo 14 misspelled the field
  on `res.partner.bank` (`isfc_code`) while spelling it correctly on
  `res.partner`; this module uses `ifsc_code` on both, so the bank column has
  to be mapped and import templates carrying the old spelling updated.
* Re-create the partner titles used in Odoo 14 (they lived under
  `base.res_partner_title_*`, which no longer exists) and re-point
  `res_partner.title`. Five common titles ship with this module as
  `partner_extension.res_partner_title_*`.
* Rename `l10n_in_extension.duplicate_vat_allowed` to
  `partner_extension.duplicate_vat_allowed`.
* Re-point the code sequences and set each `number_next` past the highest
  existing code.
* `bank_name`, `account_no` and `ifsc_code` on the partner remain import-only
  helpers: on an import (`import_file` / `install_mode` context) they create
  the `res.partner.bank` record. They are not on the form.
* If the module was installed before MSME was dropped, the columns and table
  linger - Odoo never removes columns for fields that no longer exist:
  `ALTER TABLE res_partner DROP COLUMN is_msme, DROP COLUMN msme_no, DROP COLUMN msme_type;`
  and `DROP TABLE msme_type;`

## Localisation caveat

Everything under "Indian localisation" above - GSTIN duplicate control, TDS
with the `tds_purchase` tax type, IFSC/SWIFT, the Indian TIN in the address
format, the `en_IN` default - came from Odoo 14 `l10n_in_extension`, and the
module depends on `l10n_in`. If the target deployment is not Indian, that half
should be reworked against the relevant localisation rather than ported as-is.
The `en_IN` default and the TDS group are already gated on the company /
partner country being `IN`, so they stay dormant elsewhere.

## Verification status

Static checks that were run:

* every Python module compiles; every XML file parses;
* every view inheritance spec applied to the real Odoo 19 arch offline -
  `base.view_partner_form`, `view_partner_tree`, `view_res_partner_filter`,
  `view_partner_bank_form`, the two industry views and
  `res_config_settings_view_form`, merged with `base`, `mail`, `account`,
  `contacts`, `l10n_in` and `base_setup`: all specs resolve, each new field
  appears exactly once;
* every `<field name="...">` in the views checked against the field
  declarations of those modules - 70/70 resolve.

Runtime checks still to do:

* approval round trip: create > *Ask for Partner Approval* (mail + chatter) >
  approve as approver > fields lock > *Set to Draft*;
* approve as a non-approver, and with no approver configured - both must raise;
* code sequences on approval, and duplicate rejection on create / write /
  unarchive;
* the search filters, and Contacts still opening filtered to parents;
* ribbons following `parent_id` changes;
* an RPC write to a protected field on an approved partner must be refused;
* partner reports still rendering the Indian address format with the TIN.
