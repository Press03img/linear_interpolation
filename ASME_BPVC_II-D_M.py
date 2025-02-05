import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.markdown("## 📉 ASME BPVC Material Data Sheet")

# ラジオボタンの追加
st.subheader("許容引張応力のテーブル選択")
table_selection = st.radio("テーブルを選択してください", ("Table-1A", "Table-4"))

# 選択に応じたデータの読み込み
file_path = "data.xlsx"
table_sheet = table_selection  # 選択されたテーブル
notes_sheet = f"Notes-{table_selection.split('-')[1]}"  # Notesの対応シート

df = pd.read_excel(file_path, sheet_name=table_sheet)
notes_df = pd.read_excel(file_path, sheet_name=notes_sheet)

# サイドバーのデータ選択（共通）
st.sidebar.title("データ選択")
st.sidebar.write("ℹ️ 注意: Spec Noで複数のデータがある場合、許容引張応力は平均値が表示されます。")

columns_to_filter = ["Composition", "Product", "Spec No", "Type/Grade", "Class", "Size/Tck"]
filter_values = {}
filtered_df = df.copy()

for i, col in enumerate(columns_to_filter):
    options = ["(選択してください)"] + sorted(df[col].dropna().unique().tolist())
    filter_values[col] = st.sidebar.selectbox(col, options)
    if filter_values[col] != "(選択してください)":
        filtered_df = filtered_df[filtered_df[col] == filter_values[col]]

# 選択されたデータの詳細表示
if not filtered_df.empty:
    st.subheader("選択されたデータの詳細")
    st.write(f"選択されたテーブル: **{table_selection}**")
    
    detail_data = pd.DataFrame({
        "項目": ["Composition", "Product", "P-No.", "Group No.", "Min. Tensile Strength, MPa", 
                "Min. Yield Strength, MPa", "VIII-1—Applic. and Max. Temp. Limit (°C)", 
                "External Pressure Chart No.", "Notes"],
        "値": [filtered_df.iloc[0, i] for i in range(9)]
    })
    st.table(detail_data)

    # Notes の詳細表示
    st.subheader("Notes の詳細")
    st.write(f"選択されたNotesシート: **{notes_sheet}**")
    notes_values = str(filtered_df.iloc[0, 8]).split(",")
    for note in notes_values:
        note = note.strip()
        if note in notes_df.iloc[:, 2].values:
            note_detail = notes_df[notes_df.iloc[:, 2] == note].iloc[0, 4]
            st.info(f"{note}: {note_detail}")

# 温度データと許容引張応力データの取得
if not filtered_df.empty:
    try:
        temp_values = filtered_df.columns[9:].astype(float)
        stress_values = filtered_df.iloc[:, 9:].values.flatten()
    except ValueError:
        st.error("⚠️ データに数値でない列が含まれている可能性があります。Excelシートのフォーマットを確認してください。")
        temp_values, stress_values = np.array([]), np.array([])
    
    # NaN除去
    if temp_values.size > 0 and stress_values.size > 0:
        valid_idx = ~np.isnan(stress_values)
        temp_values, stress_values = temp_values[valid_idx], stress_values[valid_idx]

        st.subheader("設計温度と線形補間")
        temp_input = st.number_input("設計温度 (℃)", min_value=float(min(temp_values)), max_value=float(max(temp_values)), value=float(min(temp_values)), step=1.0)
        interpolated_value = np.interp(temp_input, temp_values, stress_values)
        st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")

# グラフ描画
if temp_values.size > 0 and stress_values.size > 0:
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
