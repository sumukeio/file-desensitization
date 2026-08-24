import re
from typing import Tuple, Optional

# 正则表达式定义
RE_PHONE = re.compile(r"^1[3-9]\d{9}$")
RE_ID_CARD = re.compile(r"^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$")
RE_BANK_CARD = re.compile(r"^[1-9]\d{15,18}$")
RE_EMAIL = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
RE_IPV4 = re.compile(r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")


def mask_text_middle(text: str) -> str:
    """
    用户指定核心规则：凡是文本列，将中间一部分替换为 '*'，每个字符换一次。
    例如 'NERQWEQ' (长7) -> 'NE***EQ'
    """
    if not isinstance(text, str) or len(text) <= 1:
        return text
    
    length = len(text)
    if length == 2:
        return text[0] + "*"
    if length == 3:
        return text[0] + "*" + text[2]
    elif length <= 5:
        keep_len = 1
    elif length <= 9:
        keep_len = 2
    else:
        keep_len = max(2, int(length * 0.25))
    
    # 防御边界
    if keep_len * 2 >= length:
        keep_len = max(1, (length - 1) // 2)
        
    mask_len = length - (keep_len * 2)
    return text[:keep_len] + ("*" * mask_len) + text[-keep_len:]


def detect_and_mask_pii(value_str: str) -> Tuple[bool, str, str]:
    """
    检测字符串是否为高危 PII 数据，若匹配则执行合规掩码
    :return: (is_matched, masked_value, pii_type)
    """
    s = value_str.strip()
    
    # 手机号 (11位)
    if RE_PHONE.match(s):
        return True, s[:3] + "****" + s[7:], "PHONE"
        
    # 身份证号 (18位)
    if RE_ID_CARD.match(s):
        return True, s[:6] + "********" + s[14:], "ID_CARD"
        
    # 银行卡号 (16-19位)
    if RE_BANK_CARD.match(s):
        return True, s[:6] + ("*" * (len(s) - 10)) + s[-4:], "BANK_CARD"
        
    # 电子邮箱
    if RE_EMAIL.match(s):
        parts = s.split("@", 1)
        name, domain = parts[0], parts[1]
        masked_name = mask_text_middle(name)
        return True, f"{masked_name}@{domain}", "EMAIL"
        
    # IPv4 地址
    if RE_IPV4.match(s):
        parts = s.split(".")
        return True, f"{parts[0]}.{parts[1]}.*.*", "IP"
        
    return False, value_str, "NONE"
