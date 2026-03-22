import json
import logging
from datetime import timedelta

from odoo import fields, models, api

_logger = logging.getLogger(__name__)

MRP_STATUS_MAP = {
    'draft': 'Not Started',
    'confirmed': 'Not Started',
    'progress': 'In Works',
    'done': 'Complete',
    'cancel': 'Cancelled',
}

ORIENTATION_MAP = {
    'w': 'Width-wise',
    'wh': 'Width & Height',
}


class ProductionDaillyDetails(models.TransientModel):
    _name = 'production.dailly.details'
    _description = 'Dqilly Production'

    name = fields.Char('Name', default="Production Dailly Details")
    date = fields.Date(string='Date', default=(fields.Date.today() - timedelta(days=1)))

    is_form = fields.Boolean()
    select_all = fields.Boolean('Select All', default=False)
    sale_line_ids = fields.One2many('production.dailly.details.line', 'sale_parent_id', string='Orders')
    production_line_ids = fields.One2many('production.dailly.details.line', 'mrp_parent_id', string='Order Details')

    @api.onchange('select_all')
    def _onchange_select_all(self):
        for line in self.production_line_ids:
            line.is_selected = self.select_all

    def action_select_all(self):
        self.ensure_one()
        self.production_line_ids.write({'is_selected': True})
        return False

    def action_deselect_all(self):
        self.ensure_one()
        self.production_line_ids.write({'is_selected': False})
        return False

    def action_print_selected(self):
        self.ensure_one()
        _logger.info("production_line_ids count: %s", len(self.production_line_ids))

        # Try to use selected lines via mrp_id
        selected_lines = self.production_line_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.production_line_ids

        _logger.info("selected lines count: %s, mrp_id_int values: %s",
                     len(selected_lines),
                     [l.mrp_id_int for l in selected_lines])

        # Use mrp_id_int (Integer field survives round-trip, Many2one does not)
        lines_with_mrp = selected_lines.filtered(lambda l: l.mrp_id_int)

        if lines_with_mrp:
            _logger.info("Using selected lines with mrp_id_int (%s lines)", len(lines_with_mrp))
            mrp_ids = [l.mrp_id_int for l in lines_with_mrp if l.mrp_id_int]
            mrp_productions = self.env['mrp.production'].browse(mrp_ids)
        else:
            _logger.info("mrp_id empty on transient lines, falling back to direct DB search")
            mrp_productions = self.env['mrp.production'].search([
                ('create_date', '>=', self.date)
            ])

        _logger.info("Found %s MRP productions", len(mrp_productions))

        lines_data = []
        for mrp in mrp_productions:
            lines_data.append({
                'product_name': mrp.product_id.display_name or '',
                'width': mrp.width,
                'height': mrp.height,
                'quantity': mrp.product_qty,
                'priority': mrp.sale_line_id.order_id.priority if mrp.sale_line_id else 'standard',
                'mrp_name': mrp.name or '',
                'sale_name': mrp.sale_line_id.order_id.name if mrp.sale_line_id else '',
            })

        _logger.info("lines_data: %s", lines_data)

        if not lines_data:
            _logger.warning("No MRP productions found for date >= %s", self.date)
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Print Options',
            'res_model': 'production.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lines_data': json.dumps(lines_data)
            }
        }

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

        data['sale_line_ids'] = sale_line_ids

        # Get ALL MRP productions created on or after the selected date
        all_mrp = self.env['mrp.production'].search([('create_date', '>=', self.date)])
        i = 0
        for mrp in all_mrp:
            mrp_status = MRP_STATUS_MAP.get(mrp.state, mrp.state or '')
            if mrp.state == 'done' and mrp.sale_line_id:
                done_pickings = mrp.sale_line_id.order_id.picking_ids.filtered(
                    lambda p: p.state == 'done'
                )
                if done_pickings:
                    mrp_status = 'Delivered'

            orientation_label = ORIENTATION_MAP.get(mrp.product_id.orientation or '', '')

            production_line_ids.append((0, 0, {
                'line_no': i,
                'product_name': mrp.product_id.display_name or '',
                'width': mrp.width,
                'height': mrp.height,
                'quantity': mrp.product_qty,
                'roll_width': mrp.roll_width,
                'orientation': orientation_label,
                'priority': mrp.sale_line_id.order_id.priority if mrp.sale_line_id else 'standard',
                'mrp_status': mrp_status,
                'state': mrp.sale_line_id.order_id.state if mrp.sale_line_id else '',
                'sale_id': mrp.sale_line_id.order_id.id if mrp.sale_line_id else False,
                'mrp_id': mrp.id,
                'mrp_id_int': mrp.id,
            }))
            i += 1
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
    orientation = fields.Char('Orientation')
    priority = fields.Char('Priority')
    mrp_status = fields.Char('Status')
    state = fields.Char('SO State')
    mrp_id = fields.Many2one('mrp.production', string="Manufacturing Order")
    mrp_id_int = fields.Integer('MRP ID')
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    sale_parent_id = fields.Many2one('production.dailly.details', string="Details Dailly")
    mrp_parent_id = fields.Many2one('production.dailly.details', string="Details Dailly")
    is_selected = fields.Boolean('Select', default=False)
