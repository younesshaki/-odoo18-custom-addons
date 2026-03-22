import json
import logging

from odoo import models

_logger = logging.getLogger(__name__)


def _load_lines(env, docids, data):
    """Get lines from data dict, or fall back to reading lines_data from the wizard record."""
    lines = (data or {}).get('lines', [])
    if not lines and docids:
        wizard = env['production.print.wizard'].browse(docids)
        if wizard:
            lines = json.loads(wizard[0].lines_data or '[]')
    return lines


class ReportProductionSheet(models.AbstractModel):
    _name = 'report.cidmo_curtain.production_sheet_template'
    _description = 'Production Sheet Report'

    def _get_report_values(self, docids, data=None):
        lines = _load_lines(self.env, docids, data)
        _logger.info('ProductionSheet lines count: %s', len(lines))
        return {
            'doc_ids': docids,
            'docs': self.env['production.print.wizard'].browse(docids),
            'data': {'lines': lines},
        }


class ReportDeliveryNote(models.AbstractModel):
    _name = 'report.cidmo_curtain.delivery_note_template'
    _description = 'Delivery Note Report'

    def _get_report_values(self, docids, data=None):
        lines = _load_lines(self.env, docids, data)
        _logger.info('DeliveryNote lines count: %s', len(lines))
        return {
            'doc_ids': docids,
            'docs': self.env['production.print.wizard'].browse(docids),
            'data': {'lines': lines},
        }


class ReportProductLabel(models.AbstractModel):
    _name = 'report.cidmo_curtain.product_label_template'
    _description = 'Product Label Report'

    def _get_report_values(self, docids, data=None):
        lines = _load_lines(self.env, docids, data)
        _logger.info('ProductLabel lines count: %s', len(lines))
        return {
            'doc_ids': docids,
            'docs': self.env['production.print.wizard'].browse(docids),
            'data': {'lines': lines},
        }
