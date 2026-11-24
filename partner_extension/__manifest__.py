{
    'name': 'Partner Approval & Contact Codes',
    'version': '19.0.1.0.1',
    'category': 'Sales/Sales',
    'summary': (
        'Partner approval workflow for Odoo contacts: approve customers and vendors, '
        'auto customer/vendor codes, lock approved master data, extra contact fields.'
    ),
    'description': """
Partner Approval & Contact Codes for Odoo 19
============================================

Control who can turn a new contact into a usable customer or vendor.

Key features
------------
* Draft / Approved status bar on every contact
* Configurable partner approvers per company (Settings > General Settings)
* Ask for Partner Approval: e-mail template + To-Do activity for each approver
* Approve Partner: data-quality gate, approver tracking, chatter notification
* Server-side lock: protected fields of approved partners cannot be changed,
  not even through import or RPC
* Set to Draft for approvers or the "Allow Partner Set to Draft" access right
* Is Customer / Is Vendor / Is Employee flags with unique codes
* Customer and Vendor codes drawn automatically from configurable sequences
* Partner / Contact ribbons, contact titles (re-added for Odoo 19), regions
* Extra fields: birth & anniversary date, department, fax, company revenue,
  total employees, purchase terms (freight, insurance, warranty, T&C, ...)
* SWIFT code on bank accounts
""",
    'author': 'Alligator Infosoft',
    'website': 'https://alligatorinfosoft.com/',
    'maintainer': 'Alligator Infosoft',
    'support': 'sales@alligatorinfosoft.com',
    'license': 'OPL-1',
    'price': 0.0,
    'currency': 'USD',
    'depends': [
        'base',
        'mail',
        'contacts',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/res_partner_title_data.xml',
        'data/mail_template_data.xml',
        'views/contact_region_views.xml',
        'views/res_partner_title_views.xml',
        'views/res_partner_views.xml',
        'views/partner_approve_wizard_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/main_screenshot.png',
        'static/description/icon.png',
        'static/description/feature_overview.png',
        'static/description/feature_workflow.png',
        'static/description/screenshots/partner_draft_customer.png',
        'static/description/screenshots/partner_vendor_customer_codes.png',
        'static/description/screenshots/customer_vendor_flags.png',
        'static/description/screenshots/access_rights_partner_approval.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
