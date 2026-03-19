from odoo import fields, models, api
from odoo.exceptions import ValidationError
import math


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    width = fields.Float(related="sale_line_id.width", string='Width')
    height = fields.Float(related="sale_line_id.height", string='Height')
    sale_priority = fields.Selection(related="sale_line_id.order_id.priority", string='Sale Order Priority')
    roll_width = fields.Float(string='Roll Width', compute='_compute_roll_width', store=True)
    fitting_method = fields.Many2one('cidmo.udc.values', string='Fitting Method',
                                     domain="[('field_name', '=', 'fitting_method')]")
    control_side = fields.Many2one('cidmo.udc.values', string='Control Side',
                                   domain="[('field_name', '=', 'control_side')]")
    roll_direction = fields.Many2one('cidmo.udc.values', string='Roll Direction',
                                     domain="[('field_name', '=', 'roll_direction')]")
    treas_id = fields.Many2one('stock.treas', string='Remnant')


    @api.depends('move_raw_ids', 'move_raw_ids.lot_id')
    def _compute_roll_width(self):
        for rec in self:
            fabric = rec.move_raw_ids.filtered(lambda x: x.lot_id)
            rec.roll_width  = fabric and fabric.width or 0


    def action_print_layout_report(self):
        return self.env.ref('cidmo_curtain.report_mrp_layout').report_action(self)

    def action_assign_treas(self):
        line = self.move_raw_ids.filtered(lambda x: x.lot_id)
        if line:
            context = {
                'default_product_id': line.product_id.id,
                'default_product_uom_id': line.product_uom.id,
                'default_location_id': line.location_id.id,
                'default_location_dest_id': line.company_id.treas_location_id.id,
                'default_lot_id': line.lot_id.id,
                'default_production_id': self.id,
            }
            return {
                'name': 'Remnants',
                'view_mode': 'form',
                'res_model': 'stock.treas',
                'target': 'new',
                'type': 'ir.actions.act_window',
                'context': context
            }
        else:
            raise ValidationError("There is no products have LOT")


    def action_view_treas(self):
        action = self.env.ref('cidmo_curtain.action_stock_treas').read()[0]
        action['domain'] = [('production_id', '=', self.id)]
        return action


    def button_mark_done(self):
        res = super().button_mark_done()
        for rec in self:
            if rec.treas_id:
                rec.treas_id.action_validate()

        return res

class MrpBom(models.Model):
    _inherit = 'mrp.bom'



    @api.model_create_multi
    def create(self, values):
        res = super(MrpBom, self).create(values)
        for rec in res:
            if rec.product_tmpl_id:
                rec.product_tmpl_id.write({'list_price': rec.cidmo_get_price()})
                for product in rec.product_tmpl_id.product_variant_ids:
                    product.write({'list_price': rec.cidmo_get_price()})

            elif rec.product_id:
                rec.product_id.write({'list_price': rec.cidmo_get_price()})
        return res

    def write(self, values):
        res = super(MrpBom, self).write(values)
        for rec in self:
            if rec.product_tmpl_id:
                rec.product_tmpl_id.write({'list_price': rec.cidmo_get_price()})
                for product in rec.product_tmpl_id.product_variant_ids:
                    product.write({'list_price': rec.cidmo_get_price()})

            elif rec.product_id:
                rec.product_id.write({'list_price': rec.cidmo_get_price()})
        return res





    def cidmo_get_price(self):
        price = 0
        for b_line in self.bom_line_ids:
            # GET COST PRICE
            product_price = b_line.product_id.standard_price
            b_price = product_price * b_line.product_qty
            extra = b_line.product_id.novelty + b_line.product_id.waste
            if extra > 0:
                b_price = b_price * extra

            # GET SELL PRICE (Vendor = 150%, Consumer = 200%)
            # if line.order_id.customer_type == 'vendor':
            #     b_price = b_price * 1.5
            # else:
            # b_price = b_price * 2
            price += b_price

        price = math.ceil(price / 1)
        price = math.ceil(price / 10) * 10
        return price
