import pygame
import csv
import os
import datetime

class MLPlay:
    def __init__(self, ai_name, *args, **kwargs):
        self.side = ai_name
        self.data_log = []
        
        # ★ 修改 1: 只針對 1P 設定存檔路徑 (2P 不錄)
        if self.side == "1P":
            # 檔名加上 rule_based 方便識別
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_data_rule_based_{self.side}_{timestamp}.csv"
            
            # 指定存到 training_data 子資料夾
            base_dir = os.path.dirname(__file__)
            target_dir = os.path.join(base_dir, "training_data")
            
            # 自動建立資料夾
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            self.file_path = os.path.join(target_dir, filename)
            print(f"[{self.side}] 規則演算法啟動！資料將存至: {self.file_path}")
        else:
            print(f"[{self.side}] 規則演算法啟動！(擔任陪練員，不錄製資料)")

    def update(self, scene_info, keyboard=[], *args, **kwargs):
        # 如果遊戲結束，回傳重置訊號
        if scene_info["status"] != "GAME_ALIVE":
            return "RESET"

        # 1. 取得球與場地資訊
        ball_x = scene_info["ball"][0]
        ball_y = scene_info["ball"][1]
        ball_vx = scene_info["ball_speed"][0]
        ball_vy = scene_info["ball_speed"][1]
        
        # 根據你是 1P 還是 2P，決定目標高度與板子資訊
        if self.side == "1P":
            platform_x = scene_info["platform_1P"][0]
            target_y = 420  # 1P 板子高度 (球往下掉時接)
            incoming = ball_vy > 0 # 球往下飛才是朝向我
        else:
            platform_x = scene_info["platform_2P"][0]
            target_y = 80   # 2P 板子高度 (球往上飛時接)
            incoming = ball_vy < 0 # 球往上飛才是朝向我

        command = "NONE"

        # =========================================================
        # ★ 物理運算核心 (兩邊都要算，這樣 2P 才能陪打)
        # =========================================================
        if incoming:
            # 時間 = 距離 / 速度
            steps = (target_y - ball_y) / ball_vy
            
            # 預測落點 X
            pred_x = ball_x + (ball_vx * steps)
            
            # 處理牆壁反彈
            bound_left = 0
            bound_right = 200
            
            while pred_x < bound_left or pred_x > bound_right:
                if pred_x > bound_right:
                    pred_x = bound_right - (pred_x - bound_right)
                elif pred_x < bound_left:
                    pred_x = -pred_x
            
            # 決定動作
            platform_center = platform_x + 20
            tolerance = 2 # 維持之前的靈敏度
            
            if platform_center < pred_x - tolerance:
                command = "MOVE_RIGHT"
            elif platform_center > pred_x + tolerance:
                command = "MOVE_LEFT"
            else:
                command = "NONE"
        else:
            command = "NONE"

        # =========================================================
        # ★ 資料錄製 (只錄 1P)
        # =========================================================
        
        # ★ 修改 2: 只有 1P 才執行記錄動作
        if self.side == "1P":
            # 寫入暫存清單 (只在球有速度時記錄)
            if ball_vx != 0 or ball_vy != 0:
                self.data_log.append({
                    "ball_x": ball_x,
                    "ball_y": ball_y,         # 直接紀錄，不需翻轉
                    "ball_vx": ball_vx,
                    "ball_vy": ball_vy,       # 直接紀錄，不需翻轉
                    "platform_x": platform_x, # 1P 位置
                    "command": command
                })

        return command

    def reset(self):
        # ★ 修改 3: 只有 1P 才執行存檔
        if self.side == "1P" and self.data_log:
            file_exists = os.path.isfile(self.file_path)
            with open(self.file_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.data_log[0].keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerows(self.data_log)
            print(f"[{self.side}] 已儲存 {len(self.data_log)} 筆完美教學數據！")
            self.data_log = []