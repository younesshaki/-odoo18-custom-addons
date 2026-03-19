from odoo import fields, models, api


class CidmoWizardPriority(models.Model):
    _name = 'cidmo.wizard.priority'
    _description = 'Wizard Priority'

    def _default_uom_id(self):
        product = self.env.ref("cidmo_curtain.cidmo_product_priority_express")
        return product.uom_id.id

    quantity = fields.Integer(string='Qty', required=True, default=1.0)
    priority = fields.Selection(string='Priority', selection=[('standard', 'Standard'), ('express', 'Express')],
                                default="express", required=True)
    price_unit = fields.Float(string='Price')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=_default_uom_id)

    @api.onchange('priority')
    def onchange_priority(self):
        if self.priority == 'express':
            self.price_unit = 50
        else:
            self.price_unit = 0

    def action_add_priority(self):
        for rec in self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids')):
            if self.priority == 'express':
                rec.priority = 'express'
                rec.commitment_date = fields.Datetime.today().replace(hour=22, minute=00)
                qty = self.quantity
                if rec.order_line.filtered(lambda x: x.is_express):
                    rec.order_line.filtered(lambda x: x.is_express)[0].write({'product_uom_qty': qty})
                else:
                    product = self.env.ref("cidmo_curtain.cidmo_product_priority_express")
                    product = product.product_variant_ids[0]
                    rec.write({'order_line': [(0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom_qty': qty,
                        'price_unit': self.price_unit,
                        'is_express': True,
                        'product_uom': product.uom_id.id
                    })]})

