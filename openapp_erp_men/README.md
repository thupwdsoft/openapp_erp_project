odoo_project/
│
├── addons/                      # (nếu dùng Odoo source)
│
├── custom-addons/               # Nơi chứa module tuỳ biến
│   │
│   ├── core/                    # Các module tính năng cốt lõi
│   │   ├── openapp_helpdesk_core/      # Ticket CSKH, SLA cơ bản
│   │   │   ├── __init__.py
│   │   │   ├── __manifest__.py
│   │   │   ├── models/
│   │   │   ├── views/
│   │   │   └── security/
│   │   │
│   │   ├── openapp_warranty/      # Tự tạo bảo hành từ SO, kích hoạt khi giao hàng
│   │   │   ├── __init__.py
│   │   │   ├── __manifest__.py
│   │   │   ├── models/
│   │   │   ├── views/
│   │   │   └── security/
│   │   │
│   │   ├── openapp_field_service/      # Lịch kỹ thuật ngoài hiện trường
│   │   ├── openapp_portal_extend/      # Mở rộng portal (tra cứu bảo hành, gửi yêu cầu)
│   │   ├── openapp_notification_zalo/  # Tích hợp Zalo OA (API Notify)
│   │   ├── openapp_service_analytics/  # Dashboard KPI, MTBF, MTTR
│   │   ├── openapp_maintenance_lite/   # Quản lý bảo trì cơ bản (Community)
│   │   ├── openapp_repair_bridge/      # (Optional) Liên kết với module Repair
│   │   └── openapp_iot_connector/      # (Optional) MQTT/REST cho IoT cảnh báo
│   │
│   ├── packages/                # Meta-module gom gói tính năng
│   │   ├── openapp_pkg_basic/
│   │   │   ├── __init__.py
│   │   │   └── __manifest__.py  # Depends: sale_management, account, stock, hr, helpdesk_core, warranty_core
│   │   │
│   │   ├── openapp_pkg_standard/
│   │   │   ├── __init__.py
│   │   │   └── __manifest__.py  # Depends: openapp_pkg_basic + portal_extend, notification_zalo, field_service, documents
│   │   │
│   │   └── openapp_pkg_advanced/
│   │       ├── __init__.py
│   │       └── __manifest__.py  # Depends: openapp_pkg_standard + service_analytics, maintenance_lite (hoặc maintenance), repair_bridge, iot_connector
│   │
│   └── common/                  # Tiện ích dùng chung
│       └── utils.py
│
├── docker-compose.yml           # (Nếu deploy bằng Docker)
├── requirements.txt             # Python deps
├── README.md
└── odoo.conf                    # Config file (addons_path = addons,custom-addons)


# Helpdesk
Ghi chú tích hợp & vận hành

Khai báo Kho sửa chữa
Vào Cài đặt → “Helpdesk – Bảo hành & Sửa chữa” → chọn Kho sửa chữa (location nội bộ/production/transit).
Nếu chưa chọn, khi bấm Tạo chuyển kho (linh kiện) sẽ báo lỗi để bạn cấu hình.

Luồng bảo hành

Với sản phẩm có warranty_months (đến từ openapp_warranty), khi gắn Hóa đơn bán (invoice_id) sẽ tự tính hết hạn bảo hành.

Còn BH → không sinh báo giá.

Hết BH → dùng Tạo báo giá (hết BH) để sinh sale.order từ các dòng linh kiện/sửa chữa.

Tiêu hao linh kiện

Dùng Wizard linh kiện hoặc thêm trực tiếp vào tab Sửa chữa/Linh kiện, sau đó bấm Tạo chuyển kho (linh kiện).

Hệ thống tạo picking nội bộ: từ Stock → Repair Location đã cấu hình. Mỗi dòng ghi lại stock.move và stock.picking liên quan.

Thông báo

Khi đổi giai đoạn (stage), hệ thống:

Gửi Email (nếu bật) đến partner_id.email qua template mail_tmpl_ticket_stage_change.

Gửi Zalo (nếu bật) qua hàm _notify_zalo_stage_change() (hiện đặt placeholder để bạn nối API n8n/Zalo OA của bạn).

API tạo Ticket từ Zalo

Endpoint: POST /zalo/helpdesk/api/v1/tickets (auth="user"; bạn có thể đổi thành token-based tùy hạ tầng).

Tối thiểu cần description. Có thể truyền partner_id, zalo_id, product_id, serial_lot_id, invoice_id, ticket_type.