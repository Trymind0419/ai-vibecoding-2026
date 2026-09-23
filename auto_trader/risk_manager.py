# -*- coding: utf-8 -*-
"""리스크 관리 모듈"""
class RiskManager:
    def __init__(self, max_loss_pct=0.02):
        self.max_loss_pct = max_loss_pct

    def calculate_position_size(self, capital, current_price):
        # 자산의 일정 비율만 투자
        return capital // current_price
