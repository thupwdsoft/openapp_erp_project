# -*- encoding: utf-8 -*-

import logging
from odoo.http import request  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
from odoo.tools import html2plaintext  # type: ignore
from odoo.addons.component.core import Component  # type: ignore
from .zalo_utils import get_company_by_mini_app_id, get_media_from_description

_logger = logging.getLogger(__name__)


def _get_company_from_request():
    mini_app_id = (
        request.httprequest.args.get("mini_app_id")
        or request.httprequest.headers.get("X-Mini-App-Id")
    )
    if not mini_app_id or not mini_app_id.isdigit():
        raise ValidationError("Invalid Mini App ID")

    return get_company_by_mini_app_id(mini_app_id)

def get_companies(params):
    try:
        parent_company = _get_company_from_request()
        companies = request.env['res.company'].sudo().search([
            '|',
            ('parent_id', '=', parent_company.id),
            ('id', '=', parent_company.id),
        ])

        def map_company(company):
            return {
                "id": company.id,
                "parent_id": company.parent_id.id if company.parent_id else None,
                "name": company.name,
                "phone": company.phone,
                "mobile": company.mobile,
                "social_facebook": company.social_facebook,
                "social_youtube": company.social_youtube,
                "social_tiktok": company.social_tiktok,
                "latitude": company.latitude,
                "longitude": company.longitude,
                "logo_url": f"/web/image/res.company/{company.id}/logo" if company.logo else None,
                "logo_web": f"/web/image/res.company/{company.id}/logo_web" if company.logo_web else None,
                "address": ", ".join(filter(None, [company.partner_id.street, company.partner_id.city]))
            }

        return {
            "error": 0,
            "message": "Success",
            "data": [map_company(c) for c in companies],
        }

    except Exception as e:
        return {"error": 1, "message": str(e), "data": []}

def get_banners(params):
    company = _get_company_from_request()
    banners = request.env["banner.slide"].sudo().search([
        ("company_id", "=", company.id),
        ("type", "=", "banner"),
        ("is_active", "=", True),
    ], order="create_date DESC")

    if not banners:
        return {"error": "No banners found for the given Mini App ID"}

    return [
        {
            "id": b.id,
            "name": b.name,
            "image_url": f"/web/image/banner.slide/{b.id}/image_1920" if b.image_1920 else None,
            "url": b.url or "",
        } for b in banners
    ]

def get_albums(params):
    company = _get_company_from_request()
    albums = request.env["banner.slide"].sudo().search([
        ("company_id", "=", company.id),
        ("type", "=", "album"),
        ("is_active", "=", True),
    ], order="create_date DESC")

    if not albums:
        return {"error": "No albums found for the given Mini App ID"}

    return [
        {
            "id": a.id,
            "name": a.name,
            "image_url": f"/web/image/banner.slide/{a.id}/image_1920" if a.image_1920 else None,
            "url": a.url or "",
        } for a in albums
    ]

def get_categories(kw):
    company = _get_company_from_request()
    categories = request.env["product.category"].sudo().search([
        ("company_id", "=", company.id),
        ("category_type", "=", "hang_hoa"),
        ("name", "not ilike", "all"),
        ("name", "not ilike", "saleable"),
        ("name", "not ilike", "services"),
        ("name", "not ilike", "expenses"),
        ("name", "not ilike", "deliveries"),
        ("name", "not ilike", "pos")
    ], order="create_date ASC", limit=100)

    if not categories:
        return {"error": "No categories found for the given Mini App ID"}

    return [
        {
            "id": cate.id,
            "name": cate.name,
            "image_url": f"/web/image/product.category/{cate.id}/image_1920" if cate.image_1920 else None,
        } for cate in categories
    ]

def get_products(params):
    try:
        company = _get_company_from_request()
        # Tìm tất cả danh mục là "Hàng hóa"
        hang_hoa_categ_ids = request.env["product.category"].sudo().search([
            ("company_id", "=", company.id),
            ("category_type", "=", "hang_hoa")
        ]).ids

        products = request.env["product.template"].sudo().search([
            ("company_id", "=", company.id),
            ("sale_ok", "=", True),
            ("categ_id", "in", hang_hoa_categ_ids),  # Chỉ lấy sản phẩm thuộc danh mục hàng hóa
        ], order="create_date DESC")

        if not products:
            _logger.warning("⚠️ No products found for company ID: %s", company.id)
            return []

        product_list = []

        for pro in products:
            _logger.info("  Processing product: %s (ID: %s)", pro.name, pro.id)

            variants = []
            active_variants = pro.product_variant_ids.filtered(lambda v: v.active)

            for variant in active_variants:
                attribute_values = [
                    {
                        "attribute": attr.attribute_id.name or "N/A",
                        "value": attr.product_attribute_value_id.name or "N/A",
                        "hex": attr.product_attribute_value_id.html_color or "#000000"
                        if attr.attribute_id.name.lower() in ["color", "màu sắc", "couleur"] else None,
                    }
                    for attr in variant.product_template_attribute_value_ids
                ]

                variants.append({
                    "id": variant.id,
                    "name": variant.display_name,
                    "price": variant.lst_price,
                    "attribute_values": attribute_values,
                    "image_media_url": f"/web/image/product.product/{variant.id}/image_1920" if variant.image_1920 else None,
                })

            media_content = get_media_from_description(pro.description_ecommerce or "")

            product_data = {
                "id": pro.id,
                "name": pro.name,
                "price": pro.list_price,
                "originalPrice": pro.product_variant_id.standard_price,
                "description_sale": pro.description_sale or "",
                "description_ecommerce": getattr(pro, 'description_ecommerce', "") or "",
                "categoryId": pro.categ_id.id if pro.categ_id else None,
                "image_url": f"/web/image/product.template/{pro.id}/image_1920",
                "variants": variants,
                "media": media_content,
            }

            product_list.append(product_data)

        return product_list

    except Exception as e:
        _logger.error("Error fetching products: %s", str(e))
        return []

