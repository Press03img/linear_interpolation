import streamlit as st
st.markdown("## 📉 ASME BPVC Material Data Sheet 2023 Edition")
st.write("---")  # 横線を追加してセクションっぽくする
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

# --- Matplotlib 日本語対応 ---
if platform.system() == "Windows":
    plt.rcParams['font.family'] = "MS Gothic"
elif platform.system() == "Darwin":
    plt.rcParams['font.family'] = "Hiragino Maru Gothic Pro"
else:
    plt.rcParams['font.family'] = "IPAexGothic"

file_path = "data.xlsx"

# --- シート切り替え用のラジオボタン ---
selected_sheet = st.radio("データシートを選択", ["Table-1A", "Table-4"])

# シート名に応じて Notes シートを選択
notes_sheet = "Notes-1A" if selected_sheet == "Table-1A" else "Notes-4"

df = pd.read_excel(file_path, sheet_name=selected_sheet)
notes_df = pd.read_excel(file_path, sheet_name=notes_sheet)

# --- サイドバーでデータをフィルタリング ---
st.sidebar.title("データ選択")
columns_to_filter = ["Composition", "Product", "Spec No", "Type/Grade", "Class", "Size/Tck"]
filter_values = {}
filtered_df = df.copy()

for i, col in enumerate(columns_to_filter):
    if col in df.columns:
        if i == 0:
            options = ["(選択してください)"] + sorted(df[col].dropna().unique().tolist())
        else:
            prev_col = columns_to_filter[i - 1]
            prev_value = filter_values.get(prev_col, "(選択してください)")
            if prev_value == "(選択してください)" or prev_col not in filtered_df.columns:
                options = ["(選択してください)"] + sorted(df[col].dropna().unique().tolist())
            else:
                filtered_df = filtered_df[filtered_df[prev_col] == prev_value]
                options = ["(選択してください)"] + sorted(filtered_df[col].dropna().unique().tolist())
        filter_values[col] = st.sidebar.selectbox(col, options, key=f"{selected_sheet}_{col}")
    else:
        filter_values[col] = st.sidebar.selectbox(col, ["(選択してください)"], key=f"{selected_sheet}_{col}")

# --- データ表示 ---
if not filtered_df.empty:
    st.subheader(f"{selected_sheet} の選択されたデータの詳細")
    
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
    notes_values = str(filtered_df.iloc[0, 12]).split(",")
    st.subheader(f"{selected_sheet} の Notes の詳細")
    for note in notes_values:
        note = note.strip()
        if note in notes_df.iloc[:, 2].values:
            note_detail = notes_df[notes_df.iloc[:, 2] == note].iloc[0, 4]
            if st.button(note, key=f"{selected_sheet}_{note}"):
                st.info(f"{note}: {note_detail}")

# --- 温度データと許容引張応力データの取得 ---
temp_values = filtered_df.columns[13:].astype(float)
stress_values = filtered_df.iloc[:, 13:].values

if stress_values.shape[0] == 1:
    stress_values = stress_values.flatten()
else:
    stress_values = stress_values.mean(axis=0)

valid_idx = ~np.isnan(stress_values)
temp_values = temp_values[valid_idx]
stress_values = stress_values[valid_idx]

temp_values = pd.Series(temp_values).dropna()

if temp_values.empty:
    st.error("⚠️ 表示に必要なデータが選択されていません。")
else:
    temp_input = st.number_input(
        "温度 (℃)", 
        min_value=float(min(temp_values)), 
        max_value=float(max(temp_values)), 
        value=float(min(temp_values)), 
        step=1.0,
        key="temp_input"
    )

# --- 線形補間を実行 ---
if temp_values.empty or stress_values.size == 0:
    st.error("⚠️ 補間に必要なデータが選択されていません。")
elif len(temp_values) == len(stress_values):
    interpolated_value = np.interp(temp_input, temp_values, stress_values)
    st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")
else:
    st.error("データの不整合があり、補間できません。エクセルのデータを確認してください。")

# --- グラフ描画 ---
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(temp_values, stress_values, label="Original Curve", color="blue", marker="o")
ax.plot(temp_values, stress_values, linestyle="--", color="gray", alpha=0.7)
ax.scatter(temp_input, interpolated_value, color="red", marker="x", s=100, label="Linear Interpolation Result")
ax.set_xlabel("Temp. (℃)")
ax.set_ylabel("Allowable Tensile Stress (MPa)")
ax.set_title("Estimation of allowable tensile stress by linear interpolation")
ax.legend()
ax.grid()
st.pyplot(fig)
