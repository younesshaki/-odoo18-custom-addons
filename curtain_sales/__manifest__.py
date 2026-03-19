{
    'name': 'Curtain Sales',
    "version": "18.0.1.1.0",
    'summary': 'Ensure products selected in sales quotations with curtain-specific attributes',
    'description': 'Custom module for curtain sales',
    'author': 'zaimjawhar@gmail.com',
    'depends': [ 'web' ,'website_sale', 'sale','base','sale_management', 'sale_product_configurator','mrp'],

   'data': [
            'views/product_template_views.xml',
            'views/sale_order_line_views.xml',
            'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': True,
}
