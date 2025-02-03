import streamlit as st
st.markdown("## 📉 ASME BPVC Material Data Sheet")
st.write("---")  # 横線を追加してセクションっぽくする
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Matplotlib 日本語対応 ---
plt.rcParams['font.family'] = 'MS Gothic'  # Windows向け（macOS/Linuxなら適宜変更）

file_path = "data.xlsx"  # `data.xlsx` に統一

# --- シート切り替え用のラジオボタン ---
selected_sheet = st.radio("データシートを選択", ["Table-A", "Table-B"])

df = pd.read_excel(file_path, sheet_name=selected_sheet)  # 選択されたシートを読み込む
notes_df = pd.read_excel(file_path, sheet_name="Notes")  # "Notes" シートを読む

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
    filter_values[col] = st.sidebar.selectbox(col, options, key=f"{selected_sheet}_{col}")

# --- Type/Grade, Class, Size/Tck が1つしかない場合、自動で決定 ---
for col in ["Type/Grade", "Class", "Size/Tck"]:
    unique_values = filtered_df[col].dropna().unique()
    if len(unique_values) == 1:
        filter_values[col] = unique_values[0]

# --- 3. すべての選択が完了したらデータを表示 ---
if not filtered_df.empty:
    st.subheader(f"{selected_sheet} の選択されたデータの詳細")
    
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
    st.subheader(f"{selected_sheet} の Notes の詳細")
    for note in notes_values:
        note = note.strip()
        if note in notes_df.iloc[:, 2].values:  # 3列目に存在するか確認
            note_detail = notes_df[notes_df.iloc[:, 2] == note].iloc[0, 4]  # 5列目の詳細取得
            if st.button(note, key=f"{selected_sheet}_{note}"):
                st.info(f"{note}: {note_detail}")
