import re
from datetime import datetime, timedelta
import zxcvbn

class PasswordValidator:
    def __init__(self):
        self.min_length = 12
        self.max_length = 128
        self.min_score = 3  # zxcvbn 評分最低要求（0-4）
        
    def validate(self, password, user_inputs=None):
        """
        驗證密碼強度
        
        Args:
            password: 要驗證的密碼
            user_inputs: 用於檢查密碼中是否包含用戶相關信息的列表
            
        Returns:
            (bool, str): (是否通過驗證, 錯誤信息)
        """
        if user_inputs is None:
            user_inputs = []
            
        # 檢查密碼長度
        if len(password) < self.min_length:
            return False, f"密碼長度不能少於 {self.min_length} 個字符"
        if len(password) > self.max_length:
            return False, f"密碼長度不能超過 {self.max_length} 個字符"
            
        # 使用 zxcvbn 檢查密碼強度
        result = zxcvbn.zxcvbn(password, user_inputs)
        if result['score'] < self.min_score:
            suggestions = result['feedback']['suggestions']
            warning = result['feedback']['warning']
            error_msg = "密碼強度不足。"
            if warning:
                error_msg += f" {warning}"
            if suggestions:
                error_msg += f" 建議：{' '.join(suggestions)}"
            return False, error_msg
            
        # 檢查基本要求
        if not re.search(r'[A-Z]', password):
            return False, "密碼必須包含至少一個大寫字母"
        if not re.search(r'[a-z]', password):
            return False, "密碼必須包含至少一個小寫字母"
        if not re.search(r'\d', password):
            return False, "密碼必須包含至少一個數字"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密碼必須包含至少一個特殊字符"
            
        return True, ""

class PasswordPolicy:
    def __init__(self):
        self.max_age_days = 90  # 密碼最大有效期（天）
        self.history_size = 5   # 記住最近幾個密碼，防止重複使用
        
    def is_password_expired(self, last_password_change):
        """檢查密碼是否過期"""
        if not last_password_change:
            return True
        max_age = timedelta(days=self.max_age_days)
        return datetime.utcnow() - last_password_change > max_age
        
    def can_reuse_password(self, new_password_hash, password_history):
        """檢查是否可以重複使用密碼"""
        return new_password_hash not in password_history
