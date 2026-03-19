from odoo import fields, models, api


class CidmoWizardInstall(models.Model):
    _name = 'cidmo.wizard.install'
    _description = 'Wizard Install'

    def _default_uom_id(self):
        product = self.env.ref("cidmo_curtain.cidmo_product_install_paid")
        return product.uom_id.id

    quantity = fields.Integer(string='Qty', required=True, default=1.0)
    installation = fields.Selection(string='Installation', selection=[('free', 'Free'), ('paid', 'Paid')],
                                default="free", required=True)
    price_unit = fields.Float(string='Price')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=_default_uom_id)

    @api.onchange('installation')
    def onchange_installation(self):
        if self.installation == 'paid':
            self.price_unit = 180
        else:
            self.price_unit = 0

    def action_add_installation(self):
        for rec in self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids')):
            if self.installation == 'paid':
                rec.commitment_date = fields.Datetime.today().replace(hour=22, minute=00)
                qty = self.quantity
                if rec.order_line.filtered(lambda x: x.is_install):
                    rec.order_line.filtered(lambda x: x.is_install)[0].write({'product_uom_qty': qty})
                else:
                    product = self.env.ref("cidmo_curtain.cidmo_product_install_paid")
                    product = product.product_variant_ids[0]
                    rec.write({'order_line': [(0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom_qty': qty,
                        'price_unit': self.price_unit,
                        'is_install': True,
                        'product_uom': product.uom_id.id
                    })]})

