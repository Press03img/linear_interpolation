import streamlit as st
import pandas as pd
import numpy as np

# ★ matplotlib安定化
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 日本語対応（必要なら）
import japanize_matplotlib


def main():

    st.write("#### Table-1A : Maximum Allowable Stress Values, S, for Ferrous Materials")
    st.write("###### Section I; Section III, Division 1, Classes 2 and 3; Section VIII, Division 1; and Section XII")

    file_path = "data.xlsx"
    df = pd.read_excel(file_path, sheet_name="Table-1A")
    notes_df = pd.read_excel(file_path, sheet_name="Notes-1A")

    # ---------------------------
    # サイドバーフィルタ
    # ---------------------------
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
            if prev_value != "(選択してください)":
                filtered_df = filtered_df[filtered_df[prev_col] == prev_value]

            options = ["(選択してください)"] + sorted(filtered_df[col].dropna().unique().tolist())

        filter_values[col] = st.sidebar.selectbox(col, options)

    if filtered_df.empty:
        st.warning("データが選択されていません")
        st.stop()

    # ---------------------------
    # 温度・応力データ取得
    # ---------------------------
    temp_values = np.array(df.columns[13:], dtype=float)
    stress_values = filtered_df.iloc[:, 13:].to_numpy(dtype=float)

    # 複数行平均
    if stress_values.shape[0] > 1:
        stress_values = np.nanmean(stress_values, axis=0)
    else:
        stress_values = stress_values.flatten()

    # NaN除去（型統一済み）
    valid_idx = ~np.isnan(stress_values)
    temp_values = temp_values[valid_idx]
    stress_values = stress_values[valid_idx]

    # ---------------------------
    # データチェック
    # ---------------------------
    if len(temp_values) == 0 or len(stress_values) == 0:
        st.error("⚠️ 有効なデータがありません")
        st.stop()

    if len(temp_values) != len(stress_values):
        st.error("⚠️ データ長不一致")
        st.stop()

    # ---------------------------
    # 温度入力
    # ---------------------------
    st.subheader("設計温度と線形補間")

    temp_input = st.number_input(
        "設計温度 (℃)",
        min_value=float(temp_values.min()),
        max_value=float(temp_values.max()),
        value=float(temp_values.min()),
        step=1.0
    )

    # ---------------------------
    # 線形補間
    # ---------------------------
    interpolated_value = np.interp(temp_input, temp_values, stress_values)

    st.success(f"温度 {temp_input}℃ のときの許容引張応力: {interpolated_value:.2f} MPa")

    # ---------------------------
    # グラフ描画（安全版）
    # ---------------------------
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(temp_values, stress_values, marker="o", label="Data")
    ax.plot(temp_values, stress_values, linestyle="--", alpha=0.7)

    ax.scatter(temp_input, interpolated_value, marker="v", s=80, label="Interpolated")

    ax.set_xlabel("Temp. (℃)")
    ax.set_ylabel("Allowable Tensile Stress (MPa)")
    ax.set_title("Allowable Stress vs Temperature")
    ax.grid()
    ax.legend()

    st.pyplot(fig, clear_figure=True)


if __name__ == "__main__":
    main()
