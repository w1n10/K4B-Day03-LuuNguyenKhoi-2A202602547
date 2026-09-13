"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Chủ đề: Trợ lý Báo cáo Tình trạng Pin & Lốp xe VinFast GreenSM.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu tình trạng Pin & Lốp xe theo biển số
    {
        "name": "vehicle_status_query",
        "description": "Tra cứu tình trạng pin (dung lượng, sức khỏe pin) và tình trạng lốp (áp suất, độ mòn) của xe VinFast GreenSM bằng biển số xe.",
        "parameters": {
            "type": "object",
            "properties": {
                "license_plate": {
                    "type": "string",
                    "description": "Biển số xe VinFast GreenSM cần tra cứu (ví dụ: '51K-88888')"
                }
            },
            "required": ["license_plate"]
        }
    },

    # Tool 2: Tạo yêu cầu bảo dưỡng/báo cáo sự cố Pin hoặc Lốp
    {
        "name": "create_maintenance_request",
        "description": "Tạo yêu cầu bảo dưỡng hoặc báo cáo sự cố về Pin/Lốp cho xe VinFast GreenSM tại trạm dịch vụ.",
        "parameters": {
            "type": "object",
            "properties": {
                "license_plate": {
                    "type": "string",
                    "description": "Biển số xe cần đặt lịch bảo dưỡng (ví dụ: '51K-88888')"
                },
                "issue_type": {
                    "type": "string",
                    "description": "Loại sự cố cần xử lý: 'battery' (pin) hoặc 'tire' (lốp)",
                    "enum": ["battery", "tire"]
                },
                "preferred_datetime": {
                    "type": "string",
                    "description": "Thời gian mong muốn đến trạm dịch vụ (ví dụ: '09:00 20/09/2026')"
                }
            },
            "required": ["license_plate", "issue_type", "preferred_datetime"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "51K-88888": {
        "model": "VinFast VF e34",
        "battery_percent": 42,
        "battery_health": "Tốt (98% dung lượng thiết kế)",
        "estimated_range_km": 132,
        "tire_pressure_psi": {"truoc_trai": 32, "truoc_phai": 32, "sau_trai": 30, "sau_phai": 30},
        "tire_wear_percent": 65,
        "status": "Đang hoạt động bình thường"
    },
    "30G-12345": {
        "model": "VinFast VF 8",
        "battery_percent": 15,
        "battery_health": "Cần kiểm tra (dung lượng sụt nhanh)",
        "estimated_range_km": 38,
        "tire_pressure_psi": {"truoc_trai": 28, "truoc_phai": 27, "sau_trai": 29, "sau_phai": 29},
        "tire_wear_percent": 88,
        "status": "Cảnh báo: Pin yếu & Lốp mòn nhiều"
    }
}


def execute_vehicle_status_query(license_plate: str) -> str:
    """Thực thi tra cứu tình trạng Pin & Lốp theo biển số xe"""
    plate = license_plate.strip().upper()
    vehicle = MOCK_DATABASE.get(plate)
    if vehicle:
        return json.dumps({
            "status": "SUCCESS",
            "license_plate": plate,
            "data": vehicle
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu xe có biển số '{license_plate}' trong hệ thống GreenSM."
        }, ensure_ascii=False)


def execute_create_maintenance_request(license_plate: str, issue_type: str, preferred_datetime: str) -> str:
    """Thực thi tạo yêu cầu bảo dưỡng/báo cáo sự cố Pin hoặc Lốp"""
    plate = license_plate.strip().upper()
    issue_label = "Pin" if issue_type == "battery" else "Lốp"
    return json.dumps({
        "status": "SUCCESS",
        "request_id": f"REQ-{plate}-{issue_type.upper()}",
        "license_plate": plate,
        "issue_type": issue_type,
        "datetime": preferred_datetime,
        "message": f"Đã tạo yêu cầu bảo dưỡng {issue_label} cho xe {plate} vào lúc {preferred_datetime}. Vui lòng đến trạm dịch vụ GreenSM gần nhất đúng giờ hẹn."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "vehicle_status_query": execute_vehicle_status_query,
    "create_maintenance_request": execute_create_maintenance_request
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
