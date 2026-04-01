import streamlit as st
import pandas as pd
import numpy as np

# ★追加（ここだけ）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    
    st.write("#### Table-1A : Maximum Allowable Stress Values, S, for Ferrous Materials")
    st.write("###### Section I; Section III, Division 1, Classes 2 and 3;* Section VIII, Division 1; and Section XII")

    # Matplotlib 日本語対応（※一旦そのまま残す）
    plt.rcParams['font.family'] = 'MS Gothic'

    file_path = "data.xlsx"
    df = pd.read_excel(file_path, sheet_name="Table-1A")
    notes_df = pd.read_excel(file_path, sheet_name="Notes-1A")

    # サイドバーでデータフィルタリング
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

    # -------------------------------
    # ここまでは完全に元コード維持
    # -------------------------------

    # 温度データと許容引張応力データ取得
    if not filtered_df.empty:
        # ★修正①：型をnumpyに統一
        temp_values = np.array(filtered_df.columns[13:], dtype=float)
        stress_values = filtered_df.iloc[:, 13:].to_numpy(dtype=float)

        if all(filter_values[col] != "(選択してください)" for col in ["Type/Grade", "Class", "Size/Tck"]):
            selected_df = filtered_df[
                (filtered_df["Type/Grade"] == filter_values["Type/Grade"]) &
                (filtered_df["Class"] == filter_values["Class"]) &
                (filtered_df["Size/Tck"] == filter_values["Size/Tck"])
            ]
        else:
            selected_df = filtered_df

        if not selected_df.empty:
            stress_values = selected_df.iloc[:, 13:].to_numpy(dtype=float)

            if stress_values.shape[0] == 1:
                stress_values = stress_values.flatten()
            elif stress_values.shape[0] > 1:
                stress_values = np.nanmean(stress_values, axis=0)

    # ★修正②：NaN処理（型統一後）
    valid_idx = ~np.isnan(stress_values)
    temp_values = temp_values[valid_idx]
    stress_values = stress_values[valid_idx]

    temp_values = pd.Series(temp_values).dropna()

    st.subheader("設計温度と線形補間")

    if temp_values.empty:
        st.error("⚠️ 表示に必要なデータが選択されていません。")
        st.stop()

    temp_input = st.number_input(
        "設計温度 (℃)", 
        min_value=float(min(temp_values)), 
        max_value=float(max(temp_values)), 
        value=float(min(temp_values)), 
        step=1.0,
        key="temp_input"
    )

    if stress_values.size == 0:
        st.error("⚠️ 補間に必要なデータが選択されていません。")
        st.stop()

    if len(temp_values) == len(stress_values):
        interpolated_value = np.interp(temp_input, temp_values, stress_values)
        st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")
    else:
        st.error("データの不整合があり、補間できません。")
        st.stop()

    # -------------------------------
    # ★修正③：グラフ描画ガード
    # -------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(temp_values, stress_values, marker="o")
    ax.plot(temp_values, stress_values, linestyle="--", alpha=0.7)
    ax.scatter(temp_input, interpolated_value, marker="v", s=40)

    ax.set_xlabel("Temp. (℃)")
    ax.set_ylabel("Allowable Tensile Stress (MPa)")
    ax.set_title("Estimation of allowable tensile stress by linear interpolation")
    ax.grid()

    st.pyplot(fig, clear_figure=True)


if __name__ == "__main__":
    main()
