import pytest
from backend.app.engine.rules.maskers import mask_text_middle, detect_and_mask_pii


class TestMaskers:
    def test_text_middle_mask_samples(self):
        # 1. 验证用户指定标准样例 (NERQWEQ -> NE***EQ)
        assert mask_text_middle("NERQWEQ") == "NE***EQ"
        
        # 2. 短文本测试
        assert mask_text_middle("AB") == "A*"
        assert mask_text_middle("ABC") == "A*C"
        assert mask_text_middle("ABCD") == "A**D"
        assert mask_text_middle("ABCDE") == "A***E"
        
        # 3. 6-9 字符测试 (保留首尾各2字符)
        assert mask_text_middle("ABCDEF") == "AB**EF"
        assert mask_text_middle("ABCDEFGH") == "AB****GH"
        assert mask_text_middle("ABCDEFGHI") == "AB*****HI"
        
        # 4. 长文本测试
        long_str = "123456789012"
        masked_long = mask_text_middle(long_str)
        assert masked_long.startswith("123")
        assert masked_long.endswith("012")
        assert "*" in masked_long

    def test_phone_masking(self):
        matched, val, pii_type = detect_and_mask_pii("13800138000")
        assert matched is True
        assert val == "138****8000"
        assert pii_type == "PHONE"

    def test_id_card_masking(self):
        matched, val, pii_type = detect_and_mask_pii("110101199003072345")
        assert matched is True
        assert val == "110101********2345"
        assert pii_type == "ID_CARD"

    def test_email_masking(self):
        matched, val, pii_type = detect_and_mask_pii("alex_smith@company.com")
        assert matched is True
        assert val.endswith("@company.com")
        assert "*" in val
        assert pii_type == "EMAIL"

    def test_non_pii(self):
        matched, val, pii_type = detect_and_mask_pii("普通正常文本")
        assert matched is False
        assert val == "普通正常文本"
