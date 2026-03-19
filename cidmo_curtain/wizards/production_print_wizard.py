import json
from odoo import models, fields

class ProductionPrintWizard(models.TransientModel):
    _name = 'production.print.wizard'
    _description = 'Production Print Wizard'

    production_sheet = fields.Boolean("Production Sheet")
    delivery_note = fields.Boolean("Delivery Note")
    product_label = fields.Boolean("Product Label")
    lines_data = fields.Text("Lines Data")

    def action_validate(self):
        self.ensure_one()
        if not any([self.production_sheet, self.delivery_note, self.product_label]):
            return
        lines = json.loads(self.lines_data or '[]')
        data = {'lines': lines}
        if self.production_sheet:
            return self.env.ref(
                'cidmo_curtain.report_production_sheet'
            ).report_action(self, data=data)
        if self.delivery_note:
            return self.env.ref(
                'cidmo_curtain.report_delivery_note'
            ).report_action(self, data=data)
        if self.product_label:
            return self.env.ref(
                'cidmo_curtain.report_product_label'
            ).report_action(self, data=data)
