# -*- encoding: utf-8 -*-
import logging
from odoo.addons.base_rest import restapi  # type: ignore
from odoo.addons.base_rest.components.service import skip_secure_response, skip_secure_params  # type: ignore
from odoo.addons.component.core import Component  # type: ignore

from ..services.zalo_payment_service import zalo_payment_callback  # type: ignore
from ..services.zalo_product_service import get_banners, get_albums, get_companies, get_categories, get_products
from ..services.zalo_order_service import create_order, save_shipping_address, get_orders, get_shipping_address
from ..services.zalo_user_service import get_or_create_user
from ..services.zalo_loyalty_service import add_points, get_points, redeem_points
from ..utils.auth_utils import verify_app_key, unauthorized_response  # ✅ Sử dụng từ utils


class ProductService(Component):
    _inherit = "base.rest.service"
    _name = "api.zalo.service"
    _usage = "v1"
    _collection = "api.zalo.services"
    _description = """Zalo Product API"""

    def _guard(self, params):
        if not verify_app_key(self.env, params):
            return unauthorized_response()
        return None

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/companies"], ["GET"])], auth="public")
    def get_companies(self, **params):
        err = self._guard(params)
        if err: return err
        return get_companies(params)


    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/banners"], ["GET"])], auth="public")
    def get_banners(self, **params):
        err = self._guard(params)
        if err: return err
        return get_banners(params)
    
    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/albums"], ["GET"])], auth="public")
    def get_albums(self, **params):
        err = self._guard(params)
        if err: return err
        return get_albums(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/categories"], ["GET"])], auth="public")
    def get_categories(self, **params):
        err = self._guard(params)
        if err: return err
        return get_categories(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/products"], ["GET"])], auth="public")
    def get_products(self, **params):
        err = self._guard(params)
        if err: return err
        return get_products(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/user"], ["POST"])], auth="public")
    def get_user(self, **params):
        err = self._guard(params)
        if err: return err
        return get_or_create_user(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/points"], ["GET"])], auth="public")
    def get_points(self, **params):
        err = self._guard(params)
        if err: return err
        return get_points(params)
    
    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/add_points"], ["POST"])], auth="public")
    def add_points(self, **params):
        err = self._guard(params)
        if err: return err
        return add_points(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/redeem_points"], ["POST"])], auth="public")
    def redeem_points(self, **params):
        err = self._guard(params)
        if err: return err
        return redeem_points(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/create-order"], ["POST"])], auth="public")
    def create_sale_order(self, **params):
        err = self._guard(params)
        if err: return err
        return create_order(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/get-orders"], ["POST"])], auth="public")
    def get_sale_orders(self, **params):
        err = self._guard(params)
        if err: return err
        return get_orders(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/zalo-payment-callback"], ["POST"])], auth="public")
    def zalo_payment_callback(self, **params):
        err = self._guard(params)
        if err: return err
        return zalo_payment_callback(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/save-shipping-address"], ["POST"])], auth="public")
    def create_shipping_address(self, **params):
        err = self._guard(params)
        if err: return err
        return save_shipping_address(params)

    @skip_secure_params
    @skip_secure_response
    @restapi.method([(["/get-shipping-address"], ["POST"])], auth="public")
    def get_shipping_address(self, **params):
        err = self._guard(params)
        if err: return err
        return get_shipping_address(params)
