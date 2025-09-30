import datetime
import requests
import json
import logging
from odoo import _ # type: ignore
from odoo.http import request # type: ignore

_logger = logging.getLogger(__name__)  # Định nghĩa logger

def push_chat_history(post):
    platform = post.get('platform')
    social_user_id = post.get('user_id')
    message = post.get('message')
    intent = post.get('intent')
    tags = post.get('interest_tags')
    pronoun = post.get('pronoun')
    timestamp = post.get('timestamp') or datetime.now().isoformat()

    if not platform or not social_user_id or not message:
        return {"error": "Thiếu dữ liệu bắt buộc: platform, user_id, message."}

    # Tìm hoặc tạo partner
    Partner = request.env['res.partner'].sudo()
    partner = Partner.search([('social_user_id', '=', social_user_id), ('platform', '=', platform)], limit=1)
    if not partner:
        partner = Partner.create({
            'platform': platform,
            'social_user_id': social_user_id,
            'name': f'{platform.title()} User {social_user_id}',
            'is_social_lead': True,
            'interest_tags': tags or '',
            'pronoun': pronoun or '',
        })
    else:
        # cập nhật tags và pronoun nếu chưa có
        update_vals = {}
        if tags and not partner.interest_tags:
            update_vals['interest_tags'] = tags
        if pronoun and not partner.pronoun:
            update_vals['pronoun'] = pronoun
        if update_vals:
            partner.write(update_vals)

    # Ghi lịch sử chat
    request.env['n8n.chat.history'].sudo().create({
        'partner_id': partner.id,
        'platform': platform,
        'message': message,
        'intent': intent,
        'tags': tags,
        'timestamp': timestamp,
    })

    return {"status": "success", "partner_id": partner.id}
