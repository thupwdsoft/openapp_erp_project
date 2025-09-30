import random
import string
from odoo.addons.base_rest.controllers import main # type: ignore


class ZaloApiController(main.RestController):
    _root_path = "/zalo/shop/api/"
    _collection_name = "api.zalo.services"
    _default_auth = "jwt"
    _default_cors = "*"