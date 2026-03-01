import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from strategies import v1, v2, v3, v4, v5, v6, v7

AVAILABLE_VERSIONS = {
    'v1': v1,
    'v2': v2,
    'v3': v3,
    'v4 (SMC/ICT Trend)': v4,
    'v5 (Pairs Trading)': v5,
    'v6 (Funding Arbitrage)': v6,
    'v7 (AI Multi-Strategy)': v7
}

def main():
    st.set_page_config(page_title="Smart Trading Terminal", layout="wide")
    
    st.sidebar.title("STT Version Control")
    version = st.sidebar.radio("Select Strategy Version", list(AVAILABLE_VERSIONS.keys()), index=6)
    
    # Render selected version
    AVAILABLE_VERSIONS[version].render()

if __name__ == "__main__":
    main()