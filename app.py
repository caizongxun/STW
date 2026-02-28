# Smart Trading Terminal (STT) - Streamlit主界面入口
import streamlit as st
from strategies import AVAILABLE_VERSIONS

def main():
    st.title("Smart Trading Terminal (STT)")
    st.subheader("模块化加密货币机器学习交易系统")
    
    # 选择策略版本
    version = st.selectbox("选择策略版本", list(AVAILABLE_VERSIONS.keys()))
    
    # 渲染对应版本的界面
    AVAILABLE_VERSIONS[version].render()

if __name__ == "__main__":
    main()