from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    width = fields.Float(string="Width (m)", digits=(2, 2))
    height = fields.Float(string="Height (m)", digits=(2, 2))
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    # Existing fields
    control_side = fields.Selection([
        ('left', 'Left'),
        ('right', 'Right')
    ], string='Control Side', default='left')

    roll_direction = fields.Selection([
        ('standard', 'Standard'),
        ('reverse', 'Reverse')
    ], string='Roll Direction', default='standard')

    check_measure = fields.Selection([
        ('not_required', 'Not Required'),
        ('required', 'Required')
    ], string='Check Measure', default='not_required')

    remove_product = fields.Selection([
        ('no_removal', 'No Removal'),
        ('removal_disposal', 'Removal & Disposal')
    ], string='Remove Product', default='no_removal')

    split_shipping = fields.Selection([
        ('not_permitted', 'Not Permitted'),
        ('permitted', 'Permitted')
    ], string='Split Shipping', default='not_permitted')

    location_other_1 = fields.Selection([
        ('basement', 'Basement'),
        ('ground_floor', 'Ground Floor'),
        ('first_floor', 'First Floor'),
        ('second_floor', 'Second Floor'),
        ('third_floor', 'Third Floor'),
        ('other', 'Other')
    ], string='Location Other (1)', default='ground_floor')

    location_other_2 = fields.Selection([
        ('apartment', 'Apartment'),
        ('loft', 'Loft'),
        ('house', 'House'),
        ('bank', 'Bank'),
        ('coffee_shop', 'Coffee Shop'),
        ('hotel', 'Hotel'),
        ('other', 'Other')
    ], string='Location Other (2)', default='house')

    # New Location Field
    location = fields.Selection([
        ('living_room', 'Living Room'),
        ('lounge', 'Lounge'),
        ('bedroom_1', 'Bedroom 1'),
        ('bedroom_2', 'Bedroom 2'),
        ('bedroom_3', 'Bedroom 3'),
        ('terrasse', 'Terrasse'),
        ('balcony', 'Balcony'),
        ('kitchen', 'Kitchen'),
        ('bathroom', 'Bathroom'),
        ('other', 'Other')
    ], string='Location', default='living_room')
