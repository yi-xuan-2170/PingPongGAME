import pandas as pd
import os
import glob

# =============================================================================
# 1. 環境設定與讀取資料
# =============================================================================
base_dir = os.path.dirname(__file__)
source_dir = os.path.join(base_dir, "training_data")

if not os.path.exists(source_dir):
    print(f"錯誤：找不到資料夾 {source_dir}")
    exit()

all_files = glob.glob(os.path.join(source_dir, "game_data*.csv"))
# 過濾掉已經清洗過的檔案
all_files = [f for f in all_files if "cleaned" not in f]

if not all_files:
    print("找不到原始資料檔！")
    exit()

print(f"發現 {len(all_files)} 個資料檔，合併中...")

# 讀取資料 (容錯機制)
try:
    df_list = [pd.read_csv(filename, on_bad_lines='skip') for filename in all_files]
except TypeError:
    df_list = [pd.read_csv(filename, error_bad_lines=False) for filename in all_files]

df = pd.concat(df_list, ignore_index=True)
print(f"原始資料總筆數: {len(df)}")

# =============================================================================
# 2. 強力修復：轉數字 & 清除標題
# =============================================================================
cols_to_numeric = ['ball_x', 'ball_y', 'ball_vx', 'ball_vy', 'platform_x']
for col in cols_to_numeric:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna()

# =============================================================================
# 3. 核心邏輯：預判標註 (維持高準度的關鍵)
# =============================================================================
# 計算板子中心
platform_center = df['platform_x'] + 20
ball_x = df['ball_x']
ball_vx = df['ball_vx']

# ★ 瞄準未來位置 (現在位置 + 速度)
# 這段預判邏輯是讓準確率達到 99% 的核心，必須保留
target_x = ball_x + ball_vx 
diff = target_x - platform_center

# 定義動作 (誤差 > 1 就移動)
df['command'] = 'NONE' 
df.loc[diff > 1, 'command'] = 'MOVE_RIGHT'
df.loc[diff < -1, 'command'] = 'MOVE_LEFT'

# =============================================================================
# 4. 過濾：只保留球往下的資料
# =============================================================================
print(f"過濾前筆數: {len(df)}")

# 只保留 ball_vy > 0 (球往下掉)
df = df[df['ball_vy'] > 0]

print(f"過濾後 (只留往下): {len(df)}")

# =============================================================================
# 5. ★ 資料平衡：不動(NONE) vs 有動(MOVE) 1:1 ★
# =============================================================================
# 將資料分成兩群：不動 vs 有動
drop_filter = df['command'] == 'NONE'
df_none = df[drop_filter]
df_move = df[~drop_filter]

print(f"原始分佈 -> 不動(NONE): {len(df_none)}, 有動(MOVE): {len(df_move)}")

# 策略：如果 NONE 太多，就砍到跟 MOVE 一樣多 (1:1)
# 但如果 MOVE 比較多，我們「全數保留」，不進行刪減 (因為移動的資料越豐富越好)
if len(df_none) > len(df_move):
    print("偵測到 NONE 過多，正在削減以達成 1:1 平衡...")
    df_none_sampled = df_none.sample(n=len(df_move), random_state=42)
else:
    print("NONE 數量未超過 MOVE，保留原始資料 (不刪減移動數據)")
    df_none_sampled = df_none

# 合併資料
df_cleaned = pd.concat([df_none_sampled, df_move])

# =============================================================================
# 6. 存檔
# =============================================================================
cleaned_path = os.path.join(source_dir, "game_data_cleaned.csv")
df_cleaned.to_csv(cleaned_path, index=False)

print(f"--------------------------------------------------")
print(f"清洗完成！最終資料筆數: {len(df_cleaned)}")
print(f"  - MOVE (Left+Right): {len(df_move)}")
print(f"  - NONE             : {len(df_none_sampled)}")
print(f"資料平衡策略：不動 vs 有動 (1:1)，且保留了所有移動資料！")
print(f"請重新執行 train.py！")