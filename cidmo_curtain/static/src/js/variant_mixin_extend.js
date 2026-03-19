import { WebsiteSale } from '@website_sale/js/website_sale';
import { KeepLast } from "@web/core/utils/concurrency";
import { memoize, uniqueId } from "@web/core/utils/functions";
import { throttleForAnimation } from "@web/core/utils/timing";
import { insertThousandsSep } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";
import { localization } from "@web/core/l10n/localization";
import { rpc } from "@web/core/network/rpc";
import wSaleUtils from "@website_sale/js/website_sale_utils";



WebsiteSale.include({
    events: Object.assign({}, WebsiteSale.prototype.events, {
        'click .js_cidmo_change': '_getCombinationInfo',
        'click .cidmo_update_palceholder': '_setWidthHeightPlaceholder',
        'click .js_cidmo_change_wh': '_OnchangeCidmoChangeWH',
    }),


    start() {
        const def = this._super(...arguments);

        this._setWidthHeightPlaceholder(this);
        return def;
    },

     _setWidthHeightPlaceholder(ev) {
        const product = document.querySelector('.product_id');
        if (document.getElementById('width')) {
            const mesureValue = document.querySelector('input[name="measurementType"]:checked');
            rpc('/cidmo_curtain/get_place_holder', {
                'product_id': product['value'],
                'mesure': mesureValue['value']
            }).then((combinationData) => {
                const widthInput = document.getElementById('width');
                const heightInput = document.getElementById('height');
                widthInput.setAttribute('placeholder', combinationData['width']);
                heightInput.setAttribute('placeholder', combinationData['height']);
            });



        }
    },


    _onClickAdd: function (ev) {
        ev.preventDefault();
        var def = () => {
            this.getCartHandlerOptions(ev);
            return this._handleAdd($(ev.currentTarget).closest('form'));
        };
        if ($('.js_add_cart_variants').children().length) {
            return this._getCombinationInfoCidmo(ev).then(() => {
                return !$(ev.target).closest('.js_product').hasClass("css_not_available") ? def() : Promise.resolve();
            });
        }
        return def();
    },

    _getCombinationInfoCidmo: function (ev) {
        if ($(ev.target).hasClass('variant_custom_value')) {
            return Promise.resolve();
        }

        const $parent = $(ev.target).closest('.js_product');
        if(!$parent.length){
            return Promise.resolve();
        }
        const combination = this.getSelectedVariantValues($parent);
        const selectedInput = $parent.find('input[name="measurementType"]:checked')[0];
        return rpc('/website_sale/get_combination_info', {
            'product_template_id': parseInt($parent.find('.product_template_id').val()),
            'product_id': this._getProductId($parent),
            'combination': combination,
            'add_qty': parseInt($parent.find('input[name="add_qty"]').val()),
            'height': $parent.find('input[name="cidmo_height"]').val(),
            'width': $parent.find('input[name="cidmo_width"]').val(),
            'mesure': selectedInput.value,
            'add': true,
            'parent_combination': [],
            'context': this.context,
            ...this._getOptionalCombinationInfoParam($parent),
        }).then((combinationData) => {
            if (this._shouldIgnoreRpcResult()) {
                return;
            }
            this._onChangeCombination(ev, $parent, combinationData);
            this._checkExclusions($parent, combination, combinationData.parent_exclusions);
        });
    },



    _OnchangeCidmoChangeWH: function (ev) {
        const $parent = $(ev.target).closest('.js_product');
        const height = $parent.find('input[name="cidmo_height"]').val();
        const width = $parent.find('input[name="cidmo_width"]').val();
        const mesure = $parent.find('input[name="measurementType"]:checked').val();

       rpc('/cidmo_curtain/validate_dimensions', {
            height: height,
            width: width,
            mesure: mesure,
        });
    },

    async _addToCartInPage(params) {
        var product = $('.js_product');
        var height = 0
        var width = 0
        if (product.length) {
            var height = product.find('input[name="cidmo_height"]').val()
            var width = product.find('input[name="cidmo_width"]').val()
        }
        const data = await rpc("/shop/cart/update_json", {
            ...params,
            height: height,
            width: width,
            display: false,
            force_create: true,
        });
        if (data.cart_quantity && (data.cart_quantity !== parseInt($(".my_cart_quantity").text()))) {
            wSaleUtils.updateCartNavBar(data);
        };
        wSaleUtils.showCartNotification(this.call.bind(this), data.notification_info);
        return data;
    },

//    _getCombinationInfo: function (ev) {
//        if ($(ev.target).hasClass('variant_custom_value')) {
//            return Promise.resolve();
//        }
//
//        const $parent = $(ev.target).closest('.js_product');
//        if(!$parent.length){
//            return Promise.resolve();
//        }
//        const combination = this.getSelectedVariantValues($parent);
//        const selectedInput = $parent.find('input[name="measurementType"]:checked')[0];
//        return rpc('/website_sale/get_combination_info', {
//            'product_template_id': parseInt($parent.find('.product_template_id').val()),
//            'product_id': this._getProductId($parent),
//            'combination': combination,
//            'add_qty': parseInt($parent.find('input[name="add_qty"]').val()),
//            'height': $parent.find('input[name="cidmo_height"]').val(),
//            'width': $parent.find('input[name="cidmo_width"]').val(),
//            'mesure': selectedInput.value,
//            'parent_combination': [],
//            'context': this.context,
//            ...this._getOptionalCombinationInfoParam($parent),
//        }).then((combinationData) => {
//            if (this._shouldIgnoreRpcResult()) {
//                return;
//            }
//            this._onChangeCombination(ev, $parent, combinationData);
//            this._checkExclusions($parent, combination, combinationData.parent_exclusions);
//        });
//    },

});
