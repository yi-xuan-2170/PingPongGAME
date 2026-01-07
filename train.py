import pandas as pd
from sklearn.ensemble import RandomForestClassifier  # 1. 改用隨機森林
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import pickle
import os

# 1. 讀取數據
data_path = os.path.join(os.path.dirname(__file__), "training_data", "game_data_cleaned.csv")

if not os.path.exists(data_path):
    print(f"錯誤：找不到 {data_path}")
    print("請先執行 python ml/clean_data.py")
    exit()

df = pd.read_csv(data_path)

# 2. 特徵工程 (Feature Engineering)
df['diff_x'] = df['platform_x'] - df['ball_x']

# ★ 修改重點：只保留真正影響判斷的特徵
# 根據 clean_data.py 的邏輯，只有「水平距離」和「水平速度」決定了要不要動。
# ball_y 和 ball_vy 在這個簡單規則下是雜訊，移除有助於模型聚焦。
x = df[['diff_x', 'ball_vx']]
y = df['command']

# 3. 切分資料集
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# 4. 訓練模型
# 使用 RandomForestClassifier
# n_estimators=20: 決策樹的數量，20 棵樹對這個簡單問題已經很足夠且速度快
# max_depth=10: 限制樹的深度，避免模型檔案過大
print("正在訓練 Random Forest 模型...")
model = RandomForestClassifier(n_estimators=20, max_depth=10, random_state=42)

model.fit(x_train, y_train)

# 5. 驗收與評估 (Evaluation)
y_pred = model.predict(x_test)

# 計算各項指標
acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)

print("=" * 30)
print(f"模型準確率 (Accuracy) : {acc * 100:.2f}%")
print(f"模型精確率 (Precision): {prec * 100:.2f}%")
print(f"模型召回率 (Recall)   : {rec * 100:.2f}%")
print(f"模型 F1-Score        : {f1 * 100:.2f}%")
print("=" * 30)

# 印出詳細報表
print("\n詳細分類報告 (Classification Report):")
print(classification_report(y_test, y_pred, zero_division=0))

# 6. 存檔
model_path = os.path.join(os.path.dirname(__file__), "model.pickle")
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
print(f"模型已更新: {model_path}")