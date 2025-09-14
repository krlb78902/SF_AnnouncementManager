import os

import streamlit as st

# 初始化 session_state 中的页面状态
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# 定义不同页面的内容
def home_page():
    st.title("主页")
    st.write("欢迎来到主页！")
    if st.button("前往详情页"):
        st.session_state.current_page = 'details' # 点击按钮改变页面状态
        if __name__ == "__main__":
            print(1)
            os.system("streamlit run AnnouncementManagerPage2.py")
        st.rerun() # 重新运行脚本以应用更改

def details_page():
    st.title("详情页")
    st.write("这是详情页面。")
    if st.button("返回主页"):
        st.session_state.current_page = 'home' # 点击按钮改变页面状态
        st.rerun() # 重新运行脚本以应用更改

# 根据当前状态显示页面
if st.session_state.current_page == 'home':
    home_page()
elif st.session_state.current_page == 'details':
    details_page()