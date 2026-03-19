# -*- coding: utf-8 -*-
{
    'name': "cidmo_curtain",
    'summary': "Custom Module for curtains sales",
    'description': """Custom Module for curtains sales
    + sale order
    + webbsite
    + manufacturing
    """,
    'author': "zaimjawhar@gmail.com",
    'website': "https://cidmo.odoo.com/",
    'version': '0.1',
    'category': 'Sales/CRM',
    'depends': ['base', 'website_sale', 'mrp', 'project_mrp_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/product.xml',
        'views/sale_order.xml',
        'views/mrp_production.xml',
        'views/templates.xml',
        'views/stock.xml',
        'wizards/wizard_priority.xml',
        'wizards/wizard_install.xml',
        'wizards/production_dailly_details.xml',
        'wizards/production_print_wizard.xml',
        'reports/production_print_reports.xml',
        'data/product.xml',
        'report/mrp_production_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cidmo_curtain/static/src/xml/product.xml',
            'cidmo_curtain/static/src/js/product_configurator_tour_utils.js',
        ],
        'web.assets_frontend': [
            'cidmo_curtain/static/src/js/variant_mixin_extend.js',
            'cidmo_curtain/static/src/css/custom_styles.css',
        ],
    },
}

