from datetime import timedelta

from odoo import fields, models, api


class ProductionDaillyDetails(models.TransientModel):
    _name = 'production.dailly.details'
    _description = 'Dqilly Production'

    name = fields.Char('Name', default="Production Dailly Details")
    date = fields.Date(string='Date', default=(fields.Date.today() - timedelta(days=1)))

    is_form = fields.Boolean()
    sale_line_ids = fields.One2many('production.dailly.details.line', 'sale_parent_id', string='Orders')
    production_line_ids = fields.One2many('production.dailly.details.line', 'mrp_parent_id', string='Order Details')


    def action_get_sale_orders(self):
        self.ensure_one()
        sale_orders = self.env['sale.order'].search([('date_order', '>=', self.date)])
        data = {
            'is_form': True
        }
        sale_line_ids = [(5, 0, 0)]
        production_line_ids = [(5, 0, 0)]
        for so in sale_orders:
            i = 0
            for line in so.order_line:
                sale_line_ids.append((0, 0, {
                    'line_no': i,
                    'quantity': line.product_uom_qty,
                    'product_name': line.product_id.name,
                    'width': line.width,
                    'height': line.height,
                    'priority': so.priority,
                    'state': so.state,
                    'sale_id': so.id
                }))
                i += 1


            i = 0
            for mrp in so.mrp_production_ids:
                production_line_ids.append((0, 0, {
                    'line_no': i,
                    'product_name': mrp.product_id.name,
                    'width': mrp.width,
                    'height': mrp.height,
                    'roll_width': mrp.roll_width,
                    'priority': mrp.sale_line_id.order_id.priority if mrp.sale_line_id else 'standard',
                    'state': so.state,
                    'sale_id': so.id,
                    'mrp_id': mrp.id
                }))
                i += 1
        data['sale_line_ids'] = sale_line_ids
        data['production_line_ids'] = production_line_ids


        self.write(data)




class ProductionDaillyDetailsLine(models.TransientModel):
    _name = 'production.dailly.details.line'
    _description = 'Dqilly Production Line'


    line_no = fields.Integer('Line No')
    product_name = fields.Char('Item')
    width = fields.Float('Width')
    height = fields.Float('Height')
    quantity = fields.Float('Quantity')
    roll_width = fields.Float('Roll Width')
    priority = fields.Char('Priority')
    state = fields.Char('Status')
    mrp_id = fields.Many2one('mrp.production', string="Manufacturing Order")
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    sale_parent_id = fields.Many2one('production.dailly.details', string="Details Dailly")
    mrp_parent_id = fields.Many2one('production.dailly.details', string="Details Dailly")