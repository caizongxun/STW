import streamlit as st
from strategies import v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13

# 設定頁面
st.set_page_config(
    page_title="STW - Smart Trading Workshop",
    page_icon="",
    layout="wide"
)

AVAILABLE_VERSIONS = {
    'V1 - 基礎量化系統': v1,
    'V2 - ATR 風險管理': v2,
    'V3 - 多維特徵強化': v3,
    'V4 - XGBoost 機器學習': v4,
    'V5 - 成交量過濾': v5,
    'V6 - 動態操作': v6,
    'V7 - 極致優化': v7,
    'V8 - 多幣種支持': v8,
    'V9 - 多時間框架': v9,
    'V10 - 動態排名': v10,
    'V11 - 深度特徵': v11,
    'V12 - Triple Barrier ML': v12,
    'V13 - DeepSeek-R1 AI': v13
}

def main():
    st.title("STW - Smart Trading Workshop")
    st.caption("AI 驅動的加密貨幣交易系統")

    # 側邊欄版本選擇
    with st.sidebar:
        st.header("系統設定")
        version = st.selectbox(
            "選擇策略版本",
            list(AVAILABLE_VERSIONS.keys()),
            index=len(AVAILABLE_VERSIONS) - 1  # 預設選擇最新版本
        )

        st.divider()
        st.markdown("""
        ### 版本說明
        - **V1-V3**: 基礎量化策略
        - **V4-V8**: 機器學習優化
        - **V9-V11**: 多維度擴展
        - **V12**: Triple Barrier 標籤
        - **V13**: DeepSeek-R1 AI 決策
        """)

    # 渲染選中的版本
    AVAILABLE_VERSIONS[version].render()

    # 底部資訊
    st.divider()
    st.caption("")

if __name__ == "__main__":
    main()
