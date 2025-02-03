import streamlit as st
st.markdown("## 📉 ASME BPVC Material Data Sheet")
st.write("---")  # 横線を追加してセクションっぽくする
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
st.write("Current Directory:", os.getcwd())  # 実行ディレクトリを表示

# --- Matplotlib 日本語対応 ---
plt.rcParams['font.family'] = 'MS Gothic'  # Windows向け（macOS/Linuxなら適宜変更）

# --- 1. エクセルデータの読み込み ---
file_path = "data.xlsx"  # エクセルファイルのパス
df = pd.read_excel(file_path, sheet_name=0)  # メインデータ
notes_df = pd.read_excel(file_path, sheet_name="Notes")  # Notesデータ

# --- Notes データの読み込み ---
notes_file = "notes.xlsx"
notes_df = pd.read_excel(notes_file, sheet_name=0)  # 1つ目のシートを読み込む

# --- 2. サイドバーでデータをフィルタリング（選択肢を絞る） ---
st.sidebar.title("データ選択")
columns_to_filter = ["Composition", "Product", "Spec No", "Type/Grade", "Class", "Size/Tck"]
filter_values = {}
filtered_df = df.copy()

for i, col in enumerate(columns_to_filter):
    if i == 0:
        options = ["(選択してください)"] + sorted(df[col].dropna().unique().tolist())
    else:
        prev_col = columns_to_filter[i - 1]
        prev_value = filter_values.get(prev_col, "(選択してください)")
        if prev_value == "(選択してください)":
            options = ["(選択してください)"] + sorted(df[col].dropna().unique().tolist())
        else:
            filtered_df = filtered_df[filtered_df[prev_col] == prev_value]
            options = ["(選択してください)"] + sorted(filtered_df[col].dropna().unique().tolist())
    filter_values[col] = st.sidebar.selectbox(col, options)

# --- Type/Grade, Class, Size/Tck が1つしかない場合、自動で決定 ---
for col in ["Type/Grade", "Class", "Size/Tck"]:
    unique_values = filtered_df[col].dropna().unique()
    if len(unique_values) == 1:
        filter_values[col] = unique_values[0]

# --- 3. すべての選択が完了したらデータを表示 ---
if not filtered_df.empty:
    st.subheader("選択されたデータの詳細")
    
    # 追加情報を表形式で表示
    detail_data = {
        "項目": [
            "Composition", "Product", "P-No.", "Group No.", "Min. Tensile Strength, MPa", 
            "Min. Yield Strength, MPa", "VIII-1—Applic. and Max. Temp. Limit (°C)", 
            "External Pressure Chart No.", "Notes"
        ],
        "値": [
            filtered_df["Composition"].iloc[0], filtered_df["Product"].iloc[0], 
            filtered_df.iloc[0, 6], filtered_df.iloc[0, 7], filtered_df.iloc[0, 8], 
            filtered_df.iloc[0, 9], filtered_df.iloc[0, 10], filtered_df.iloc[0, 11], 
            filtered_df.iloc[0, 12]
        ]
    }
    st.table(pd.DataFrame(detail_data))
    
    # --- Notes の詳細表示 ---
    notes_values = str(filtered_df.iloc[0, 12]).split(",")  # Notes を "," で分割
    st.subheader("Notes の詳細")
    for note in notes_values:
        note = note.strip()
        if note in notes_df.iloc[:, 2].values:  # 3列目に存在するか確認
            note_detail = notes_df[notes_df.iloc[:, 2] == note].iloc[0, 4]  # 5列目の詳細取得
            if st.button(note):  # クリック可能なボタンとして表示
                st.info(f"{note}: {note_detail}")

# --- 4. 温度データと許容引張応力データの取得 ---
temp_values = filtered_df.columns[13:].astype(float)  # 14列目以降が温度
stress_values = filtered_df.iloc[:, 13:].values  # 2D 配列のまま取得

# 🔹 stress_values を 1D 配列に変換する
if stress_values.shape[0] == 1:
    stress_values = stress_values.flatten()  # 1行だけならフラットにする
else:
    stress_values = stress_values.mean(axis=0)  # 複数行ある場合は平均を取る

# 🔹 NaN を除去して、データ長を一致させる
valid_idx = ~np.isnan(stress_values)  # NaN でないインデックスを取得
temp_values = temp_values[valid_idx]  # NaN を除外
stress_values = stress_values[valid_idx]  # NaN を除外

# --- 🔹 ここで temp_input を先に定義！ ---
temp_input = st.number_input("温度 (℃)", 
                             min_value=float(min(temp_values)), 
                             max_value=float(max(temp_values)), 
                             value=float(min(temp_values)), 
                             step=1.0)

# --- 5. 線形補間を実行して即時表示 ---
if len(temp_values) == len(stress_values):  # データ長が一致する場合のみ実行
    interpolated_value = np.interp(temp_input, temp_values, stress_values)
    st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")
else:
    st.error("データの不整合があり、補間できません。エクセルのデータを確認してください。")

# --- 6. グラフ描画（日本語フォント修正） ---
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(temp_values, stress_values, label="元データ", color="blue", marker="o")
ax.plot(temp_values, stress_values, linestyle="--", color="gray", alpha=0.7)
ax.scatter(temp_input, interpolated_value, color="red", marker="x", s=100, label="補間結果")
ax.set_xlabel("温度 (℃)")
ax.set_ylabel("許容引張応力 (MPa)")
ax.set_title("線形補間による許容引張応力の推定")
ax.legend()
ax.grid()
st.pyplot(fig)
