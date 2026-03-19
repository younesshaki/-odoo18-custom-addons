from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
import math
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _default_date_delivery(self):
        return fields.Datetime.today() + relativedelta(days=7)


    customer_type = fields.Selection(string='Sales Group', related="partner_id.customer_type")
    priority = fields.Selection(string='Priority', selection=[('standard', 'Standard'),('express', 'Express')], default="standard", require=True)
    commitment_date = fields.Datetime(string="Delivery Date", default=_default_date_delivery)

    check_measure = fields.Many2one('cidmo.udc.values', string='Check Measure', domain="[('field_name', '=', 'check_measure')]")
    remove_product = fields.Many2one('cidmo.udc.values', string='Remove Product', domain="[('field_name', '=', 'remove_product')]")
    split_shipping = fields.Many2one('cidmo.udc.values', string='Split Shipping', domain="[('field_name', '=', 'split_shipping')]")


    @api.onchange('priority')
    def onchange_priority(self):
        if self.priority == 'express':
            self.commitment_date = self.date_order.replace(hour=22, minute=00)
        else:
            self.commitment_date = self.date_order  + relativedelta(days=7)

    def action_add_priority(self):
        self.ensure_one()
        qty = 0
        for i in self.order_line:
            if not i.is_delivery and not i.is_express:
                qty += i.product_uom_qty
        return {
            'name': _('Add a priority method'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cidmo.wizard.priority',
            'target': 'new',
            'context': {
                'active_model': 'sale.order',
                'active_ids': self.ids,
                'default_quantity': qty,
            },
        }


    def action_add_installation(self):
        self.ensure_one()
        qty = 0
        for i in self.order_line:
            if not i.is_delivery and not i.is_express and not i.is_install:
                qty += i.product_uom_qty
        product = self.env.ref("cidmo_curtain.cidmo_product_install_paid")
        price_unit = product.product_variant_ids[0].list_price

        return {
            'name': _('Add an Installation method'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cidmo.wizard.install',
            'target': 'new',
            'context': {
                'active_model': 'sale.order',
                'active_ids': self.ids,
                'default_quantity': qty,
                'default_price_unit': price_unit,
            },
        }

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            rec.order_line.filtered(lambda x: x.product_id).action_create_mo_so()
        return res






class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    width = fields.Float(string='Width')
    height = fields.Float(string='Height')
    dimension_z = fields.Float(string='Dimension Z')
    size = fields.Float(string='Size', compute="_compute_size")
    is_express = fields.Boolean("Is Express")
    is_install = fields.Boolean("Is Installation")


    @api.depends('width', 'height', 'dimension_z')
    def _compute_size(self):
        for rec in self:
            if rec.dimension_z > 0:
                rec.size = rec.width * rec.height * rec.dimension_z
            else:
                rec.size = rec.width * rec.height

    @api.onchange('width', 'height', 'dimension_z', 'line_width', 'line_length', 'line_depth', 'product_uom_qty', 'price_unit', 'discount', 'tax_id')
    def _onchange_dimensions(self):
        for rec in self:
            rec._compute_size()
            if hasattr(rec, '_compute_area'):
                rec._compute_area()
            if hasattr(rec, '_compute_amount'):
                rec._compute_amount()

    @api.model
    def create(self, values):
        if self._context.get('height') and self._context.get('width'):
            values['height'] = self._context.get('height')
            values['width'] = self._context.get('width')
        # Add code here
        return super(SaleOrderLine, self).create(values)

    def write(self, values):
        if self._context.get('height') and self._context.get('width'):
            values['height'] = self._context.get('height')
            values['width'] = self._context.get('width')
        return super(SaleOrderLine, self).write(values)


    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        qty = self.product_uom_qty
        if self.width > 0 and self.height > 0:
            qty = qty * self.width * self.height
            if self.dimension_z > 0:
                qty = qty * self.dimension_z
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **{
                'tax_ids': self.tax_id,
                'quantity': qty,
                'partner_id': self.order_id.partner_id,
                'currency_id': self.order_id.currency_id or self.order_id.company_id.currency_id,
                'rate': self.order_id.currency_rate,
                **kwargs,
            },
        )

    def action_create_mo_so(self):
        for rec in self:
            width = rec.width
            height = rec.height
            order = rec.order_id
            stock_picking_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', order.warehouse_id.id), ('code', '=', 'mrp_operation'),
                 ('company_id', 'in', [False, order.company_id.id])], limit=1)
            bom_check = self.sudo().env['mrp.bom'].search(['|', ('product_id', '=', rec.product_id.id), ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)], limit=1)
            if bom_check:
                for i in range(1, int(rec.product_uom_qty)+1):
                    production_name = order.name.replace('S', 'WH/MO/')
                    if int(rec.product_uom_qty) > 1:
                        production_name += '.' + str(i)
                    date_planned = order.date_order
                    production_vals = {
                        'name': production_name,
                        'product_id': rec.product_id.id,
                        'product_qty': 1,
                        'product_uom_id': rec.product_id.uom_id.id,
                        'picking_type_id': stock_picking_type.id,
                        'location_src_id': stock_picking_type.default_location_src_id.id,
                        'location_dest_id': stock_picking_type.default_location_dest_id.id,
                        'bom_id': bom_check.id,
                        'date_deadline': date_planned,
                        'date_start': date_planned,
                        'sale_line_id': rec.id,
                    }
                    move_raw_ids = []
                    for line in bom_check.bom_line_ids:
                        component_product = line.product_id
                        qty = 0
                        if component_product.is_formul_1:
                            qty = math.floor(((width - 0.3) / 0.95) + 2)
                        elif component_product.calculate_format == 'm2':
                            qty = width * height * line.product_qty
                        elif component_product.calculate_format == 'm':
                            qty = width * line.product_qty
                        else:
                            qty = line.product_qty



                        data = {
                            'product_id': component_product.id,
                            'name': component_product.name,
                            'product_uom': component_product.uom_id.id,
                            'product_uom_qty': qty,
                            'price_unit': rec.get_price_unit_mo(line),
                            'location_id': order.warehouse_id.lot_stock_id.id,
                            'location_dest_id': self.env['stock.location'].search(
                                [('usage', '=', 'production'), ('company_id', '=', order.company_id.id)], limit=1).id,
                        }

                        if component_product.orientation:
                            treas_id = self.env['stock.treas'].get_product_treas(component_product, width, height)
                            if treas_id:
                                data['treas_id'] = treas_id
                                data['location_id'] = self.env.company.treas_location_id.id
                                data['width'] = width
                            else:
                                width_t, height_t, lot_id = component_product.get_treasure_width_height(width, height, False)
                                if lot_id:
                                    data['lot_id'] = lot_id.id
                                    data['width'] = width_t
                                    # data['product_uom_qty'] = height
                                    data['lot_width'] = lot_id.width



                        move_raw_ids.append((0, 0, data))
                    production_vals['move_raw_ids'] = move_raw_ids


                    self.env['mrp.production'].create(production_vals)

    # @api.depends('product_id', 'product_uom', 'product_uom_qty', 'width', 'height', 'order_id', 'order_id.partner_id')
    # def _compute_price_unit(self):
    #     for line in self:
    #         # Don't compute the price for deleted lines.
    #         if not line.order_id:
    #             continue
    #         # check if the price has been manually set or there is already invoiced amount.
    #         # if so, the price shouldn't change as it might have been manually edited.
    #         if (
    #                 (line.technical_price_unit != line.price_unit and not line.env.context.get(
    #                     'force_price_recomputation'))
    #                 or line.qty_invoiced > 0
    #                 or (line.product_id.expense_policy == 'cost' and line.is_expense)
    #         ):
    #             continue
    #         line = line.with_context(sale_write_from_compute=True)
    #         if not line.product_uom or not line.product_id:
    #             line.price_unit = 0.0
    #             line.technical_price_unit = 0.0
    #         else:
    #             line = line.with_company(line.company_id)
    #             price = line._get_display_price()
    #             bom_check = self.sudo().env['mrp.bom'].search(['|', ('product_id', '=', line.product_id.id),
    #                                                     ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)],
    #                                                    limit=1)
    #             if bom_check:
    #                 price = 0
    #                 for b_line in bom_check.bom_line_ids:
    #                     # GET COST PRICE
    #                     b_price = line.get_price_unit_mo(b_line)
    #                     extra = b_line.product_id.novelty + b_line.product_id.waste
    #                     if extra > 0:
    #                         b_price = b_price * extra
    #
    #                     # GET SELL PRICE (Vendor = 150%, Consumer = 200%)
    #                     if line.order_id.customer_type == 'vendor':
    #                         b_price = b_price * 1.5
    #                     else:
    #                         b_price = b_price * 2
    #                     price += b_price
    #
    #
    #                 price = math.ceil(price / 1)
    #                 price = math.ceil(price / 10) * 10
    #                 line.price_unit = price
    #             else:
    #                 line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
    #                     price,
    #                     product_taxes=line.product_id.taxes_id.filtered(
    #                         lambda tax: tax.company_id == line.env.company
    #                     ),
    #                     fiscal_position=line.order_id.fiscal_position_id,
    #                 )
    #             line.technical_price_unit = line.price_unit


    def get_price_unit_mo(self, b_line):
        product_price = b_line.product_id.standard_price
        b_price = product_price * b_line.product_qty
        return b_price



class cidmo_udc_values(models.Model):
    _name = 'cidmo.udc.values'
    _description = 'Cidmo Udc Values'

    name = fields.Char('Name')
    field_name = fields.Char(string='Field')

