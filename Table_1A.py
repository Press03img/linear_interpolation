import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- データ読み込み ----------
def load_data("data.xlsx"):
    df = pd.read_excel(path, sheet_name="Table-1A")
    notes_df = pd.read_excel(path, sheet_name="Notes-1A")

    # 数値カラムを float に変換（温度列以降）
    df.iloc[:, 13:] = df.iloc[:, 13:].apply(pd.to_numeric, errors="coerce")
    return df, notes_df


# ---------- サイドバー UI ----------
def sidebar_filters(df):
    st.sidebar.header("フィルター条件")
    filter_values = {}
    filtered_df = df.copy()

    # フィルター対象列（例）
    filter_columns = df.columns[:5]

    for col in filter_columns:
        options = ["(選択してください)"] + sorted(filtered_df[col].dropna().unique().tolist())
        default_idx = 0
        filter_values[col] = st.sidebar.selectbox(col, options, index=default_idx)

        if filter_values[col] != "(選択してください)":
            filtered_df = filtered_df[filtered_df[col] == filter_values[col]]

    # リセットボタン
    if st.sidebar.button("フィルターをリセット"):
        st.experimental_rerun()

    return filter_values, filtered_df


# ---------- 詳細情報表示 ----------
def display_details(filtered_df):
    st.subheader("詳細情報")
    details = filtered_df.iloc[:, :13]  # 最初の13列までを詳細情報として表示
    st.markdown(
        details.style
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "left")]},
        ])
        .to_html(),
        unsafe_allow_html=True
    )


# ---------- Notes 表示 ----------
def display_notes(filtered_df, notes_df):
    st.subheader("Notes")
    if filtered_df.empty:
        st.info("該当する Notes はありません。")
        return

    note_list = [n.strip() for n in str(filtered_df.iloc[0, 12]).split(",") if n.strip()]
    if not note_list:
        st.info("該当する Notes はありません。")
        return

    notes_display = pd.DataFrame(note_list, columns=["Note"])
    notes_display = notes_display.merge(
        notes_df.iloc[:, [2, 4]],
        left_on="Note",
        right_on=notes_df.columns[2],
        how="left"
    ).drop(columns=[notes_df.columns[2]])

    notes_display = notes_display.rename(columns={notes_df.columns[4]: "Detail"})

    st.markdown(
        notes_display.style
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "left")]},
        ])
        .to_html(),
        unsafe_allow_html=True
    )


# ---------- 補間とグラフ ----------
def interpolation_and_plot(filtered_df, filter_values):
    st.subheader("温度データ補間＆グラフ")
    if filtered_df.empty:
        st.warning("条件に合致するデータがありません。")
        return

    # 温度カラム
    temp_cols = filtered_df.columns[13:]
    temps = temp_cols.astype(float)
    values = filtered_df.iloc[0, 13:].values

    # 補間処理
    target_temp = st.number_input("補間したい温度 (°C)", value=float(temps.min()), step=5.0)
    interp_val = np.interp(target_temp, temps, values)
    st.write(f"{target_temp}°C の補間値: **{interp_val:.2f}**")

    # グラフ描画
    fig, ax = plt.subplots()
    ax.plot(temps, values, marker="o", label="実測値")
    ax.plot(target_temp, interp_val, "rx", label="補間値")
    ax.set_xlabel("温度 (°C)")
    ax.set_ylabel("値")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)


# ---------- メイン処理 ----------
def main():
    st.title("圧力容器データビューア")

    # データ読み込み
    df, notes_df = load_data("sample.xlsx")

    # フィルター
    filter_values, filtered_df = sidebar_filters(df)

    if not filtered_df.empty:
        display_details(filtered_df)
        display_notes(filtered_df, notes_df)
        interpolation_and_plot(filtered_df, filter_values)
    else:
        st.warning("条件に合致するデータがありません。")


if __name__ == "__main__":
    main()

