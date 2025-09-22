# -*- coding: utf-8 -*-
{
    "name": "OpenApp Project Management",
    "version": "18.0.1.0",
    "summary": "Quản lý Xây dựng & thi công, thiết kế nội ngoại thất chọn gói cho các công trình",
    "author": "OpenApp",
    "depends": [
        "base",         # nền tảng
        "web",          # để nạp assets
        "mail",
        "mass_mailing",      
        "product",      # nút Quick Sale trên product.template
        "sale",         # các view sale.order/*
        "stock",        
        "sale_stock",
        "project",
        "mrp",
        "hr_expense",
        "purchase",
        "calendar",
    ],
    "data": [
        "views/res_sale_order_views.xml",
        "views/stock_picking_view_inherit.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "openapp_erp_men/static/src/css/custom_theme.css",
            #"openapp_erp_men/static/src/css/header_icons.css",
            "openapp_erp_men/static/src/css/menu_icons.css",
        ],
         'web.assets_frontend': [
            'openapp_erp_men/static/src/css/custom_footer.css',
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
