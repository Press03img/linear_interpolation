import streamlit as st
import importlib

# ラジオボタンで選択
option = st.radio("データを選択してください:", ["Table_1A", "Table_4"])

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
