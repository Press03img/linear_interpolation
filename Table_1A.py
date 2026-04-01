import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from matplotlib.backends.backend_agg import RendererAgg  # ← 追加

_lock = RendererAgg.lock  # ← 追加

def main():
    st.write("#### Table-1A : Maximum Allowable Stress Values, S, for Ferrous Materials")
    st.write("###### Section I; Section III, Division 1, Classes 2 and 3;* Section VIII, Division 1; and Section XII")

    file_path = "data.xlsx"
    df = pd.read_excel(file_path, sheet_name="Table-1A")
    notes_df = pd.read_excel(file_path, sheet_name="Notes-1A")

    st.sidebar.title("データ選択")
    st.sidebar.write("ℹ️ 注意  \n Spec Noで複数のデータがある場合、許容引張応力は平均値が表示されます。全て選択して値を確認してください。")

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

    if not filtered_df.empty:
        st.subheader("選択されたデータの詳細")
        excel_headers = df.columns[:13].tolist()
        detail_data = pd.DataFrame({
            "　　　　　　　　　　　　項目　　　　　　　　　　　　": excel_headers,
            "値": [filtered_df.iloc[0, i] for i in range(13)]
        })
        st.markdown(
            detail_data.style.set_table_styles([
                {"selector": "table", "props": [("width", "100%"), ("table-layout", "fixed")]},
                {"selector": "th", "props": [("text-align", "center")]},
                {"selector": "td:nth-child(2)", "props": [("text-align", "center"), ("width", "40%")]},
            ]).hide(axis="index").to_html(),
            unsafe_allow_html=True
        )

        notes_values = str(filtered_df.iloc[0, 12]).split(",")
        notes_table = []
        for note in notes_values:
            note = note.strip()
            if note in notes_df.iloc[:, 2].values:
                note_detail = notes_df[notes_df.iloc[:, 2] == note].iloc[0, 4]
                notes_table.append([note, note_detail])

        st.subheader("Notes")
        if notes_table:
            notes_df_display = pd.DataFrame(notes_table, columns=["Note", "Detail"])
            st.markdown(
                notes_df_display.style.hide(axis="index").set_table_styles([
                    {"selector": "th", "props": [("text-align", "center")]},
                    {"selector": "td", "props": [("text-align", "left")]},
                ]).to_html(),
                unsafe_allow_html=True
            )
        else:
            st.info("該当する Notes はありません。")

    if filtered_df.empty:
        st.warning("⚠️ データが選択されていません。サイドバーから条件を選択してください。")
        return

    if all(filter_values[col] != "(選択してください)" for col in ["Type/Grade", "Class", "Size/Tck"]):
        selected_df = filtered_df[
            (filtered_df["Type/Grade"] == filter_values["Type/Grade"]) &
            (filtered_df["Class"] == filter_values["Class"]) &
            (filtered_df["Size/Tck"] == filter_values["Size/Tck"])
        ]
    else:
        selected_df = filtered_df

    if selected_df.empty:
        st.warning("⚠️ 条件に一致するデータがありません。")
        return

    temp_columns = df.columns[13:].astype(float)
    stress_raw = selected_df.iloc[:, 13:].values

    if stress_raw.shape[0] == 1:
        stress_values = stress_raw.flatten().astype(float)
    else:
        stress_values = np.nanmean(stress_raw.astype(float), axis=0)

    valid_idx = ~np.isnan(stress_values)
    temp_values = temp_columns[valid_idx]
    stress_values = stress_values[valid_idx]

    if len(temp_values) == 0:
        st.error("⚠️ 有効な温度・応力データがありません。")
        return

    st.subheader("設計温度と線形補間")
    temp_input = st.number_input(
        "設計温度 (℃)",
        min_value=float(temp_values.min()),
        max_value=float(temp_values.max()),
        value=float(temp_values.min()),
        step=1.0,
        key="temp_input"
    )

    interpolated_value = np.interp(temp_input, temp_values, stress_values)
    st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")

    # グラフ描画（lockでスレッド安全に）← ここが修正のポイント
    with _lock:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(temp_values, stress_values, label="Original Curve", color="blue", marker="o")
        ax.plot(temp_values, stress_values, linestyle="--", color="gray", alpha=0.7)
        ax.scatter(temp_input, interpolated_value, color="red", marker="v", s=100, label="Linear Interpolation Result")
        ax.set_xlabel("Temp. (℃)")
        ax.set_ylabel("Allowable Tensile Stress (MPa)")
        ax.set_title("Estimation of allowable tensile stress by linear interpolation")
        ax.legend()
        ax.grid()
        st.pyplot(fig)
        plt.close(fig)

if __name__ == "__main__":
    main()
