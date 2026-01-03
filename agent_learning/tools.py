# tools.py
import json

def get_current_weather(city: str) -> str:
    """查询指定城市的当前天气（我们用当前天气模拟明天）"""
    fake_data = {
        "北京": {"temp": 5, "condition": "晴"},
        "上海": {"temp": 12, "condition": "小雨"},
        "广州": {"temp": 22, "condition": "多云"},
        "苏州": {"temp": 10, "condition": "中雨"},   # 改成中雨，看看带伞建议
        "杭州": {"temp": 8, "condition": "阵雨"},
    }
    data = fake_data.get(city, {"temp": 18, "condition": "未知"})
    return json.dumps({
        "city": city,
        "temperature": data["temp"],
        "condition": data["condition"]
    }, ensure_ascii=False)

def send_email(to: str, subject: str, body: str) -> str:
    """模拟发送邮件"""
    print(f"\n【模拟发送邮件】")
    print(f"收件人: {to}")
    print(f"主题: {subject}")
    print(f"内容: {body}")
    return f"邮件已成功发送给 {to}（模拟）"