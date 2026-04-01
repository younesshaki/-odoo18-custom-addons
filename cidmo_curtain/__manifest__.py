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
    'license': 'LGPL-3',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'depends': [
        'base',
        'web',
        'website_sale',
        'sale_management',
        'mrp',
        'stock',
        'project_mrp_sale',
    ],
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
            'cidmo_curtain/static/src/xml/production_list.xml',
            'cidmo_curtain/static/src/js/product_configurator_tour_utils.js',
            'cidmo_curtain/static/src/js/select_all_header.js',
            'cidmo_curtain/static/src/css/production_monitor.css',
            'cidmo_curtain/static/src/js/multi_print.js',
        ],
        'web.assets_frontend': [
            'cidmo_curtain/static/src/js/variant_mixin_extend.js',
            'cidmo_curtain/static/src/css/custom_styles.css',
        ],
    },
}
