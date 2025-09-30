# -*- coding: utf-8 -*-
{
    "name": "OpenApp Core Tweaks",
    "version": "18.0.1.0",
    "summary": "UI tweaks & small views for Sale and Repair",
    "author": "OpenApp",
    "depends": [
        "base",         # nền tảng
        "web",          # để nạp assets
        "mail",       
        "product",      # nút Quick Sale trên product.template
        "sale",         # các view sale.order/*
        "stock",        
        "mrp",
        "sale_stock",
        "calendar",
    ],
    "data": [
        "security/groups.xml",
        "views/res_sale_order_views.xml",
        "views/res_product_template_views.xml",
        "views/res_sale_order_line_image_views.xml",
        "views/repair_order_lock_views.xml",
        "views/res_partner_inherit.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "openapp_erp_core/static/src/css/custom_theme.css",
            "openapp_erp_core/static/src/css/header_icons.css",
            "openapp_erp_core/static/src/css/menu_icons.css",
        ],
         'web.assets_frontend': [
            'openapp_erp_core/static/src/css/custom_footer.css',
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
