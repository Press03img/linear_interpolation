import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.markdown("## 📉 ASME BPVC Material Data Sheet")

# --- 1. エディション情報の表示 ---
edition_df = pd.read_excel("data.xlsx", sheet_name="Edition", header=None)
st.write(f"#### {edition_df.iloc[0, 0]}")
st.write(f"##### {edition_df.iloc[1, 0]}")
st.write(f"##### {edition_df.iloc[2, 0]}")

st.write("---")

# --- 2. Matplotlib 日本語対応 ---
plt.rcParams['font.family'] = 'MS Gothic'

# --- 2.5. データセットの選択 ---
sheet_selection = st.radio("データセット選択", ["Table-1A", "Table-4"], index=0)
file_path = "data.xlsx"

df = pd.read_excel(file_path, sheet_name=sheet_selection)  # メインデータ
notes_sheet = "Notes-1A" if sheet_selection == "Table-1A" else "Notes-4"
notes_df = pd.read_excel(file_path, sheet_name=notes_sheet)

# --- 3. サイドバーでデータをフィルタリング ---
st.sidebar.title("データ選択")
st.sidebar.write("ℹ️ 注意 \n Spec Noで複数のデータがある場合、許容引張応力は平均値が表示されます。")

columns_to_filter = ["Composition", "Product", "Spec No", "Type/Grade", "Class", "Size/Tck"]
filter_values = {}
filtered_df = df.copy()

for i, col in enumerate(columns_to_filter):
    options = ["(選択してください)"] + sorted(df[col].dropna().unique().tolist())
    filter_values[col] = st.sidebar.selectbox(col, options)
    if filter_values[col] != "(選択してください)":
        filtered_df = filtered_df[filtered_df[col] == filter_values[col]]

# --- 4. 選択されたデータの詳細を表形式で表示 ---
if not filtered_df.empty:
    st.subheader("選択されたデータの詳細")
    
    # 追加情報を表形式で表示（中央揃え & 幅調整）
    detail_data = pd.DataFrame({
        "項目": [
            "Composition", "Product", "P-No.", "Group No.", "Min. Tensile Strength, MPa", 
            "Min. Yield Strength, MPa", "VIII-1—Applic. and Max. Temp. Limit (°C)　　　　　　　　　　　", 
            "External Pressure Chart No.", "Notes"
        ],
        "値": [
            filtered_df["Composition"].iloc[0], filtered_df["Product"].iloc[0], 
            filtered_df.iloc[0, 6], filtered_df.iloc[0, 7], filtered_df.iloc[0, 8], 
            filtered_df.iloc[0, 9], filtered_df.iloc[0, 10], filtered_df.iloc[0, 11], 
            filtered_df.iloc[0, 12]
        ]
    })
    
    st.markdown(
        detail_data.style.set_table_styles([
            {"selector": "table", "props": [("width", "100%"), ("table-layout", "fixed")]},
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td:nth-child(2)", "props": [("text-align", "center"), ("width", "40%")]},
        ]).hide(axis="index").to_html(),
        unsafe_allow_html=True
    )

    # --- Notes の詳細表示 ---
    notes_values = str(filtered_df.iloc[0, 12]).split(",")  # Notes を "," で分割
    st.subheader("Notes の詳細")
    for note in notes_values:
        note = note.strip()
        if note in notes_df.iloc[:, 2].values:  # 3列目に存在するか確認
            note_detail = notes_df[notes_df.iloc[:, 2] == note].iloc[0, 4]  # 5列目の詳細取得
            if st.button(note):  # クリック可能なボタンとして表示
                st.info(f"{note}: {note_detail}")

# --- 5. 温度データと許容引張応力データの取得（フィルタ適用後） ---
if not filtered_df.empty:
    temp_values = filtered_df.columns[13:].astype(float)
    stress_values = filtered_df.iloc[:, 13:].values  # 2D 配列のまま取得

    # 🔹 選択データのうち、Type/Grade、Class、Size/Tck すべてが選択されている場合のみ適用
    if all(filter_values[col] != "(選択してください)" for col in ["Type/Grade", "Class", "Size/Tck"]):
        selected_df = filtered_df[
            (filtered_df["Type/Grade"] == filter_values["Type/Grade"]) &
            (filtered_df["Class"] == filter_values["Class"]) &
            (filtered_df["Size/Tck"] == filter_values["Size/Tck"])
        ]
    else:
        selected_df = filtered_df

    # 🔹 stress_values を 1D 配列に変換する
    if not selected_df.empty:
        stress_values = selected_df.iloc[:, 13:].values  # 2D 配列のまま取得
        if stress_values.shape[0] == 1:
            stress_values = stress_values.flatten()
        elif stress_values.shape[0] > 1:
            stress_values = np.mean(stress_values, axis=0)  # 平均を取る

# 🔹 NaN を除去して、データ長を一致させる
valid_idx = ~np.isnan(stress_values)  # NaN でないインデックスを取得
temp_values = temp_values[valid_idx]  # NaN を除外
stress_values = stress_values[valid_idx]  # NaN を除外

# --- 🔹 ここにエラーチェックを追加！ ---
temp_values = pd.Series(temp_values).dropna()  # NaN を除去
st.subheader("設計温度と線形補間")
if temp_values.empty:
    st.error("⚠️ 表示に必要なデータが選択されていません。")
else:
    temp_input = st.number_input(
        "設計温度 (℃)", 
        min_value=float(min(temp_values)), 
        max_value=float(max(temp_values)), 
        value=float(min(temp_values)), 
        step=1.0,
        key="temp_input"  # 🔹 keyを指定して重複を防ぐ
    )

# --- 6. 線形補間を実行して即時表示 ---
if temp_values.empty or stress_values.size == 0:
    st.error("⚠️ 補間に必要なデータが選択されていません。")
elif len(temp_values) == len(stress_values):  # データ長が一致する場合のみ実行
    interpolated_value = np.interp(temp_input, temp_values, stress_values)
    st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")
else:
    st.error("データの不整合があり、補間できません。エクセルのデータを確認してください。")


# --- 7. グラフ描画（日本語フォント修正） ---
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
