from odoo.http import request, route

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from odoo.exceptions import ValidationError

from odoo.addons.sale.controllers.product_configurator import SaleProductConfiguratorController

from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleStockVariantController(WebsiteSaleVariantController, WebsiteSale):

    @route('/cidmo_curtain/validate_dimensions', type='json', auth='public', methods=['POST'], website=True)
    def validate_dimensions(self, height, width, mesure):
        if height:
            try:
                height = float(height)
            except ValueError:
                raise ValidationError('Height must be a number')

            if mesure == 'cm' and height < 60:
                raise ValidationError('Height est hors limites !')
            elif mesure == 'm' and height < 0.6:
                raise ValidationError('Height est hors limites !')
            elif mesure == 'mm' and height < 600:
                raise ValidationError('Height est hors limites !')

        if width:
            try:
                width = float(width)
            except ValueError:
                raise ValidationError('Width must be a number')

            if mesure == 'cm' and width < 100:
                raise ValidationError('Width est hors limites !')
            elif mesure == 'm' and width < 1:
                raise ValidationError('Width est hors limites !')
            elif mesure == 'mm' and width < 1000:
                raise ValidationError('Width est hors limites !')

    @route('/cidmo_curtain/get_place_holder', type='json', auth='public', methods=['POST'], website=True)
    def cidmo_get_place_holder(self, product_id, mesure):
        product = request.env['product.product'].browse(product_id and int(product_id))
        min_height = 0
        min_width = 0
        extra = 0
        extra_width = 0


        c_maximum_load = 0
        max_width = 0
        weight = 0
        layers = 1
        if product.sudo().bom_ids:
            mechanism = product.sudo().bom_ids[0].bom_line_ids.filtered(lambda x: 'Mechanism' in x.product_id.name)
            orientation = product.sudo().bom_ids[0].bom_line_ids.filtered(lambda x: x.product_id.orientation)
            if mechanism:
                c_maximum_load = mechanism[0].product_id.c_maximum_load
            if orientation:
                if orientation[0].product_id.categ_id.name == 'Day & Night':
                    layers = 2
                weight = orientation[0].product_id.c_weights
                max = 0
                for lot in product.sudo().env['stock.lot'].search([('product_id', '=', orientation[0].product_id.id), ('product_qty', '>', 0)]):
                    if lot.width > max:
                        max = lot.width
                max_width = max

        extra_height = 0

        if mesure == 'm':
            min_width = 0.6
            min_height = 0.9
            extra_width = 0.03
            extra_height = 1000
        elif mesure == 'cm':
            min_width = 60
            min_height = 90
            extra_width = 3
            extra_height = 10000000
            max_width = max_width * 100
        elif mesure == 'mm':
            min_width = 600
            min_height = 900
            extra_width = 30
            extra_height = 1000000000
            max_width = max_width * 1000

        m_width = max_width - extra_width
        new_max_width = int(round(m_width, 2)) if round(m_width, 2) - int(round(m_width, 2)) == 0 else round(m_width, 2)
        width = f"min: {str(min_width)} {str(mesure)} / max: {new_max_width} {str(mesure)}"

        sd = float(weight) * max_width
        sd = sd * layers
        max_height = ((c_maximum_load / sd) * 0.9) if sd > 0 else 0
        new_max_height = int(round(max_height*extra_height, 2)) if round(max_height*extra_height, 2) - int(round(max_height*extra_height, 2)) == 0 else round(max_height*extra_height, 2)
        height = f"min: {str(min_height)} {str(mesure)} / max: {new_max_height} {str(mesure)}"


        return {'width': width, 'height': height}




    @route()
    def get_combination_info_website(self, *args, **kwargs):
        if kwargs.get('add') and kwargs.get('mesure'):
            # Check height
            if not kwargs.get('height'):
                raise ValidationError('Height is required')
            try:
                float(kwargs.get('height'))
            except:
                raise ValidationError('Height must be a number')

            if kwargs.get('mesure') == 'cm' and  float(kwargs.get('height')) < 60:
                raise ValidationError('Les mesures sont hors limites !')
            elif kwargs.get('mesure') == 'm' and  float(kwargs.get('height')) < 0.6:
                raise ValidationError('Les mesures sont hors limites !')
            elif kwargs.get('mesure') == 'mm' and  float(kwargs.get('height')) < 600:
                raise ValidationError('Les mesures sont hors limites !')
            # Check width
            if not kwargs.get('width'):
                raise ValidationError('Width is required')

            try:
                float(kwargs.get('width'))
            except:
                raise ValidationError('Width must be a number')

            if kwargs.get('mesure') == 'cm' and  float(kwargs.get('width')) < 100:
                raise ValidationError('Les mesures sont hors limites !')
            elif kwargs.get('mesure') == 'm' and  float(kwargs.get('width')) < 1:
                raise ValidationError('Les mesures sont hors limites !')
            elif kwargs.get('mesure') == 'mm' and  float(kwargs.get('width')) < 1000:
                raise ValidationError('Les mesures sont hors limites !')
        res = super().get_combination_info_website(*args, **kwargs)
        product = request.env['product.product'].browse(res['product_id'])
        # if product:
        #     price = product.cidmo_get_price()
        #     if price and price > 0:
        #         res['list_price'] = price
        #         res['price'] = price
        #         res['base_unit_price'] = price

        if product and kwargs.get('add') and kwargs.get('mesure'):
            problem = False

            if not product.c_widths:
                problem = True
            else:
                exist = False
                for i in product.c_widths.split('-'):
                    if float(kwargs.get('width')) <= float(i):
                        exist = True
                        break
                if not exist:
                    problem = True

            if not product.c_weights:
                problem = True
            else:
                if (float(kwargs.get('height')) * float(kwargs.get('width')) * float(product.c_weights))> product.c_maximum_load:
                    problem = True


            ct = 2 if product.day_night else 1
            sd = float(product.c_weights) * float(kwargs.get('width')) * ct
            if sd > 0 and ((product.c_maximum_load / sd) * 0.95) < float(kwargs.get('height')):
                problem = True

            # if problem:
            #     raise ValidationError('Les mesures sont hors limites !')

        return res

    @route()
    def cart_update_json(self, *args, set_qty=None,start_date=None, end_date=None, **kwargs):
        """ Override to parse to datetime optional pickup and return dates.
        """
        if set_qty != 0 and kwargs.get('height', 0) and kwargs.get('width', 0):
            request.update_context(height=kwargs.get('height', 0), width=kwargs.get('width', 0))
            request.website = request.website.with_context(height=kwargs.get('height', 0), width=kwargs.get('width', 0))

        return super().cart_update_json(
            *args, start_date=start_date, end_date=end_date, **kwargs
        )


class WebsiteSaleProductConfiguratorController(SaleProductConfiguratorController, WebsiteSale):


    def _get_product_information(
        self,
        product_template,
        combination,
        currency,
        pricelist,
        so_date,
        quantity=1,
        product_uom_id=None,
        parent_combination=None,
        **kwargs,
    ):
        """ Return complete information about a product.

        :param product.template product_template: The product for which to seek information.
        :param product.template.attribute.value combination: The combination of the product.
        :param res.currency currency: The currency of the transaction.
        :param product.pricelist pricelist: The pricelist to use.
        :param datetime so_date: The date of the `sale.order`, to compute the price at the right
            rate.
        :param int quantity: The quantity of the product.
        :param int|None product_uom_id: The unit of measure of the product, as a `uom.uom` id.
        :param product.template.attribute.value|None parent_combination: The combination of the
            parent product.
        :param dict kwargs: Locally unused data passed to `_get_basic_product_information`.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'product_tmpl_id': int,
                'id': int,
                'description_sale': str|False,
                'display_name': str,
                'price': float,
                'quantity': int
                'attribute_line': [{
                    'id': int
                    'attribute': {
                        'id': int
                        'name': str
                        'display_type': str
                    },
                    'attribute_value': [{
                        'id': int,
                        'name': str,
                        'price_extra': float,
                        'html_color': str|False,
                        'image': str|False,
                        'is_custom': bool
                    }],
                    'selected_attribute_id': int,
                }],
                'exclusions': dict,
                'archived_combination': dict,
                'parent_exclusions': dict,
            }
        """
        product_uom = request.env['uom.uom'].browse(product_uom_id)
        product = product_template._get_variant_for_combination(combination)
        attribute_exclusions = product_template._get_attribute_exclusions(
            parent_combination=parent_combination,
            combination_ids=combination.ids,
        )
        product_or_template = product or product_template

        values = dict(
            product_tmpl_id=product_template.id,
            **self._get_basic_product_information(
                product_or_template,
                pricelist,
                combination,
                quantity=quantity,
                uom=product_uom,
                currency=currency,
                date=so_date,
                **kwargs,
            ),
            quantity=quantity,
            attribute_lines=[dict(
                id=ptal.id,
                attribute=dict(**ptal.attribute_id.read(['id', 'name', 'display_type'])[0]),
                attribute_values=[
                    dict(
                        **ptav.read(['name', 'html_color', 'image', 'is_custom'])[0],
                        price_extra=self._get_ptav_price_extra(
                            ptav, currency, so_date, product_or_template
                        ),
                    ) for ptav in ptal.product_template_value_ids
                    if ptav.ptav_active or combination and ptav.id in combination.ids
                ],
                selected_attribute_value_ids=combination.filtered(
                    lambda c: ptal in c.attribute_line_id
                ).ids,
                create_variant=ptal.attribute_id.create_variant,
            ) for ptal in product_template.attribute_line_ids],
            exclusions=attribute_exclusions['exclusions'],
            archived_combinations=attribute_exclusions['archived_combinations'],
            parent_exclusions=attribute_exclusions['parent_exclusions'],
            height=kwargs.get('height', 0),
            width=kwargs.get('width', 0),
        )
        # Shouldn't be sent client-side
        values.pop('pricelist_rule_id', None)
        return values