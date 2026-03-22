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
        lines = json.loads(self.lines_data or '[]')
        if not lines:
            return False

        report_xmlids = []
        if self.production_sheet:
            report_xmlids.append('cidmo_curtain.report_production_sheet')
        if self.delivery_note:
            report_xmlids.append('cidmo_curtain.report_delivery_note')
        if self.product_label:
            report_xmlids.append('cidmo_curtain.report_product_label')

        if not report_xmlids:
            return False

        report_urls = []
        for xmlid in report_xmlids:
            report = self.env.ref(xmlid)
            url = '/report/pdf/%s/%s' % (report.report_name, self.id)
            report_urls.append(url)

        return {
            'type': 'ir.actions.client',
            'tag': 'cidmo_multi_print',
            'params': {
                'report_urls': report_urls,
            },
        }
