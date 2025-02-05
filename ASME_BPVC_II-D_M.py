import streamlit as st
import importlib
import pandas as pd

st.markdown("## 📉 ASME BPVC Material Data Sheet")

# エディション情報の表示 ---
edition_df = pd.read_excel("data.xlsx", sheet_name="Edition", header=None)
st.write(f"#### {edition_df.iloc[0, 0]}")
st.write(f"##### {edition_df.iloc[1, 0]}")
st.write(f"##### {edition_df.iloc[2, 0]}")
st.write("---")  # 横線を追加してセクションっぽくする

# ラジオボタンで選択
option = st.radio("Tableを選択してください:", [
    "Table_1A", 
    "Table_3"])

# モジュール名を設定
module_name = option

try:
    # モジュールを動的にインポート
    module = importlib.import_module(module_name)
    
    # モジュール内の `main()` を呼び出す
    if hasattr(module, "main"):
        module.main()
    else:
        st.error(f"{module_name} に `main()` 関数が定義されていません。")
except ModuleNotFoundError:
    st.error(f"{module_name} が見つかりません。")
