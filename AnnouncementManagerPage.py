import streamlit as st
from datetime import datetime
import pandas as pd


# 导入你的AnnouncementManager类
from AnnouncementManager import AnnouncementManager

# 页面配置
st.set_page_config(
    page_title="公告管理系统",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏Streamlit默认菜单和页脚
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# 初始化数据库和管理器
@st.cache_resource
def init_manager():
    """初始化公告管理器"""
    manager = AnnouncementManager()
    return manager


# 创建管理器实例
manager = init_manager()

# 侧边栏导航
st.sidebar.title("📢 公告管理系统")
menu_option = st.sidebar.radio(
    "导航菜单",
    ["公告列表", "发布公告", "搜索公告", "管理公告"]
)

# 公告列表页面
if menu_option == "公告列表":
    st.title("📋 公告列表")

    # 显示已删除公告的选项
    show_deleted = st.checkbox("显示已删除的公告")

    # 获取公告数据
    announcements = manager.get_all_announcements(include_deleted=show_deleted)

    if not announcements:
        st.info("暂无公告")
    else:
        # 转换为DataFrame以便更好展示
        announcement_data = []
        for ann in announcements:
            announcement_data.append({
                "ID": ann[0],
                "标题": ann[1],
                "内容": ann[2][:50] + "..." if len(ann[2]) > 50 else ann[2],  # 内容预览
                "创建时间": ann[3],
                "更新时间": ann[4],
                "状态": "已删除" if ann[5] else "正常"
            })

        df = pd.DataFrame(announcement_data)

        # 显示表格
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "标题": st.column_config.TextColumn("标题", width="medium"),
                "内容": st.column_config.TextColumn("内容预览", width="large"),
                "创建时间": st.column_config.DatetimeColumn("创建时间"),
                "更新时间": st.column_config.DatetimeColumn("更新时间"),
                "状态": st.column_config.TextColumn("状态", width="small")
            }
        )

        # 查看详细内容
        st.subheader("📄 公告详情")
        selected_id = st.selectbox(
            "选择公告查看详情",
            options=[ann[0] for ann in announcements],
            format_func=lambda x: f"ID: {x} - {next((ann[1] for ann in announcements if ann[0] == x), '')}"
        )

        if selected_id:
            announcement = manager.get_announcement_by_id(selected_id)
            if announcement:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**ID:** {announcement[0]}")
                    st.write(f"**状态:** {'已删除' if announcement[5] else '正常'}")
                    if announcement[5]:
                        st.write(f"**删除时间:** {announcement[5]}")
                with col2:
                    st.write(f"**标题:** {announcement[1]}")
                    st.write(f"**创建时间:** {announcement[3]}")
                    st.write(f"**更新时间:** {announcement[4]}")
                    st.write("**内容:**")
                    st.write(announcement[2])

# 发布公告页面
elif menu_option == "发布公告":
    st.title("📝 发布新公告")

    # 使用表单组织输入字段[9,10](@ref)
    with st.form(key="create_announcement_form"):
        title = st.text_input("公告标题", max_chars=200, help="请输入公告标题，最多200个字符")
        content = st.text_area("公告内容", height=200, help="请输入公告详细内容")

        submitted = st.form_submit_button("发布公告", use_container_width=True)

        if submitted:
            if title and content:
                with st.spinner("正在发布公告..."):
                    try:
                        announcement_id = manager.create_announcement(title, content)
                        st.success(f"公告发布成功！公告ID: {announcement_id}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"发布失败: {str(e)}")
            else:
                st.error("请填写标题和内容")

# 搜索公告页面
elif menu_option == "搜索公告":
    st.title("🔍 搜索公告")

    col1, col2 = st.columns([2, 1])
    with col1:
        keyword = st.text_input("搜索关键词", help="输入关键词搜索公告标题或内容")
    with col2:
        search_option = st.radio(
            "搜索范围",
            ["标题和内容", "仅标题", "仅内容"],
            horizontal=True
        )

    if keyword:
        with st.spinner("正在搜索..."):
            search_title = search_option in ["标题和内容", "仅标题"]
            search_content = search_option in ["标题和内容", "仅内容"]

            results = manager.search_announcements(keyword, search_title, search_content)

            if results:
                st.success(f"找到 {len(results)} 条相关公告")

                # 显示搜索结果
                for ann in results:
                    with st.expander(f"{ann[1]} - {ann[3][:10]}"):
                        st.write(f"**ID:** {ann[0]}")
                        st.write(f"**创建时间:** {ann[3]}")
                        st.write("**内容预览:**")
                        st.write(ann[2][:200] + "..." if len(ann[2]) > 200 else ann[2])
            else:
                st.info("未找到相关公告")

# 管理公告页面
elif menu_option == "管理公告":
    st.title("⚙️ 管理公告")

    # 获取所有公告（包括已删除的）
    announcements = manager.get_all_announcements(include_deleted=True)

    if not announcements:
        st.info("暂无公告")
    else:
        # 按状态筛选
        status_filter = st.selectbox("筛选状态", ["全部", "正常", "已删除"])

        filtered_announcements = announcements
        if status_filter == "正常":
            filtered_announcements = [ann for ann in announcements if not ann[5]]
        elif status_filter == "已删除":
            filtered_announcements = [ann for ann in announcements if ann[5]]

        if not filtered_announcements:
            st.info(f"没有{status_filter}状态的公告")
        else:
            for announcement in filtered_announcements:
                is_deleted = announcement[5] is not None

                # 使用列布局
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    status = "🗑️ " if is_deleted else "✅ "
                    st.write(
                        f"**{announcement[1]}** - {announcement[3][:10]} - {status}{'已删除' if is_deleted else '正常'}")

                with col2:
                    if st.button("编辑", key=f"edit_{announcement[0]}"):
                        st.session_state.edit_id = announcement[0]
                        st.session_state.edit_title = announcement[1]
                        st.session_state.edit_content = announcement[2]

                with col3:
                    if is_deleted:
                        if st.button("恢复", key=f"restore_{announcement[0]}"):
                            with st.spinner("恢复中..."):
                                if manager.restore_announcement(announcement[0]):
                                    st.success("公告已恢复")
                                    st.rerun()
                    else:
                        if st.button("软删除", key=f"soft_del_{announcement[0]}"):
                            with st.spinner("软删除中..."):
                                if manager.soft_delete_announcement(announcement[0]):
                                    st.success("公告已软删除")
                                    st.rerun()

                with col4:
                    if st.button("硬删除", key=f"hard_del_{announcement[0]}", type="secondary"):
                        # 确认对话框
                        if st.session_state.get(f"confirm_{announcement[0]}", False):
                            with st.spinner("永久删除中..."):
                                if manager.hard_delete_announcement(announcement[0]):
                                    st.success("公告已永久删除")
                                    st.rerun()
                        else:
                            st.session_state[f"confirm_{announcement[0]}"] = True
                            st.warning("确认要永久删除吗？此操作不可恢复！")

                # 编辑表单
                if "edit_id" in st.session_state and st.session_state.edit_id == announcement[0]:
                    with st.form(key=f"edit_form_{announcement[0]}"):
                        edit_title = st.text_input(
                            "标题",
                            value=st.session_state.edit_title,
                            key=f"title_{announcement[0]}"
                        )
                        edit_content = st.text_area(
                            "内容",
                            value=st.session_state.edit_content,
                            height=200,
                            key=f"content_{announcement[0]}"
                        )

                        col_btn1, col_btn2 = st.columns(2)

                        with col_btn1:
                            if st.form_submit_button("保存"):
                                if edit_title and edit_content:
                                    with st.spinner("保存中..."):
                                        if manager.update_announcement(
                                                announcement[0], edit_title, edit_content
                                        ):
                                            st.success("公告已更新")
                                            if "edit_id" in st.session_state:
                                                del st.session_state.edit_id
                                            st.rerun()
                                        else:
                                            st.error("更新失败")
                                else:
                                    st.error("标题和内容不能为空")

                        with col_btn2:
                            if st.form_submit_button("取消"):
                                if "edit_id" in st.session_state:
                                    del st.session_state.edit_id
                                st.rerun()

                st.divider()

# 页脚信息
st.sidebar.divider()
st.sidebar.caption(f"系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 运行说明
if __name__ == "__main__":
    # 确保数据库已初始化
    try:
        from data.datainit import init_database

        init_database()
        st.sidebar.success("数据库已就绪")
    except:
        st.sidebar.warning("请确保数据库已初始化")