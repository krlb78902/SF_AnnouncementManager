import streamlit as st

# 导入你的AnnouncementManager类
from AnnouncementManager import *


# 初始化数据库连接和公告管理器
@st.cache_resource
def init_manager():
    return AnnouncementManager()


def main():
    # 初始化session_state
    if 'set_expiry' not in st.session_state:
        st.session_state.set_expiry = False
    if 'expires_hours' not in st.session_state:
        st.session_state.expires_hours = 24

    # 页面配置
    st.set_page_config(
        page_title="公告管理系统",
        page_icon="📢",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 自定义CSS样式
    st.markdown("""
    <style>
    .announcement-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
    }
    .expired {
        border-left-color: #dc3545;
        opacity: 0.7;
    }
    .deleted {
        border-left-color: #6c757d;
        opacity: 0.6;
    }
    </style>
    """, unsafe_allow_html=True)

    # 初始化公告管理器
    manager = init_manager()

    # 启动过期检查器
    manager.start_expiry_checker(interval_seconds=300)

    # 标题
    st.title("📢 公告管理系统")
    st.markdown("---")

    # 侧边栏
    with st.sidebar:
        st.header("导航菜单")
        menu_option = st.radio(
            "选择功能",
            ["公告列表", "创建公告", "搜索公告", "管理公告"],
            index=0
        )

        st.markdown("---")
        st.header("统计信息")

        # 获取公告统计
        all_announcements = manager.get_all_announcements(include_deleted=True)
        active_announcements = manager.get_all_announcements(include_deleted=False)
        expired_count = sum(1 for ann in all_announcements
                            if ann[6] and datetime.strptime(ann[6][:19], '%Y-%m-%d %H:%M:%S') <= datetime.now())

        st.metric("总公告数", len(all_announcements))
        st.metric("活跃公告", len(active_announcements))
        st.metric("已过期", expired_count)

        st.markdown("---")
        if st.button("🔄 刷新数据"):
            st.rerun()

    # 公告列表页面
    if menu_option == "公告列表":
        st.header("所有公告")

        # 显示选项
        col1, col2 = st.columns([2, 1])
        with col1:
            show_deleted = st.checkbox("显示已删除的公告")
        with col2:
            sort_order = st.selectbox("排序方式", ["最新优先", "最旧优先"])

        # 获取公告列表
        announcements = manager.get_all_announcements(include_deleted=show_deleted)

        if sort_order == "最旧优先":
            announcements = announcements[::-1]

        if not announcements:
            st.info("暂无公告")
        else:
            for ann in announcements:
                print(ann)
                id, title, content, created_at, updated_at, deleted_at, expires_at = ann

                # 确定公告状态
                status = "active"
                if deleted_at:
                    status = "deleted"
                elif expires_at and datetime.strptime(expires_at[:19], '%Y-%m-%d %H:%M:%S') <= datetime.now():
                    status = "expired"

                # 创建公告卡片
                card_class = "announcement-card"
                if status == "expired":
                    card_class += " expired"
                elif status == "deleted":
                    card_class += " deleted"

                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(title)
                    st.write(content)
                with col2:
                    st.caption(f"创建时间: {created_at}")
                    if expires_at:
                        st.caption(f"过期时间: {expires_at}")
                    if deleted_at:
                        st.caption(f"删除时间: {deleted_at}")

                    # 状态标签
                    if status == "expired":
                        st.error("已过期")
                    elif status == "deleted":
                        st.warning("已删除")
                    else:
                        st.success("活跃中")

                st.markdown('</div>', unsafe_allow_html=True)

    # 创建公告页面
    elif menu_option == "创建公告":
        st.header("创建新公告")

        with st.form("create_announcement_form"):
            title = st.text_input("公告标题", max_chars=100,
                                  help="输入公告的标题，最多100个字符")
            content = st.text_area("公告内容", height=200,
                                   help="输入公告的详细内容")

            # 修改后的有效期设置（必填）
            expires_days = st.slider(
                "公告有效期（天）",
                min_value=1,
                max_value=30,
                value=1,
                help="设置公告自动删除的天数（1-30天，默认为1天）",
                key='expires_days_slider'
            )
            # 转换为小时（保持与原有接口兼容）
            expires_hours = expires_days * 24

            submitted = st.form_submit_button("发布公告", type="primary")

            if submitted:
                if not title or not content:
                    st.error("标题和内容不能为空！")
                else:
                    try:
                        new_id = manager.create_announcement(
                            title, content, expires_hours
                        )
                        st.success(f"公告发布成功！ID: {new_id}")
                        st.info(f"此公告将在 {expires_days} 天后自动删除")

                        # 显示预览
                        with st.expander("查看公告预览", expanded=True):
                            st.subheader(title)
                            st.write(content)
                            expiry_time = datetime.now() + timedelta(days=expires_days)
                            st.caption(f"⏰ 自动删除时间: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    except Exception as e:
                        st.error(f"创建公告时出错: {str(e)}")

    # 搜索公告页面
    elif menu_option == "搜索公告":
        st.header("搜索公告")

        search_col1, search_col2 = st.columns([2, 1])
        with search_col1:
            keyword = st.text_input("搜索关键词",
                                    help="输入标题或内容中的关键词进行搜索")
        with search_col2:
            search_type = st.radio("搜索范围", ["标题和内容", "仅标题", "仅内容"],
                                   horizontal=True)

        if keyword:
            search_title = search_type in ["标题和内容", "仅标题"]
            search_content = search_type in ["标题和内容", "仅内容"]

            results = manager.search_announcements(
                keyword, search_title, search_content
            )

            if not results:
                st.warning("未找到匹配的公告")
            else:
                st.success(f"找到 {len(results)} 条匹配的公告")

                for ann in results:
                    id, title, content, created_at, expires_at, updated_at, deleted_at = ann

                    st.markdown('<div class="announcement-card">', unsafe_allow_html=True)
                    st.subheader(title)
                    st.write(content)
                    st.caption(f"创建时间: {created_at}")
                    if expires_at:
                        st.caption(f"过期时间: {expires_at}")
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("请输入关键词开始搜索")

    # 管理公告页面
    elif menu_option == "管理公告":
        st.header("公告管理")

        tab1, tab2, tab3 = st.tabs(["编辑公告", "删除/恢复公告", "系统管理"])

        with tab1:
            st.subheader("编辑公告")
            announcements = manager.get_all_announcements(include_deleted=False)

            if not announcements:
                st.info("暂无可以编辑的公告")
            else:
                # 选择要编辑的公告
                ann_options = {f"{ann[1]} (ID: {ann[0]}, 创建于: {ann[3]})": ann[0]
                               for ann in announcements}
                selected_label = st.selectbox("选择要编辑的公告", list(ann_options.keys()))
                selected_id = ann_options[selected_label]

                # 获取选定公告的详细信息
                selected_ann = next(ann for ann in announcements if ann[0] == selected_id)
                id, old_title, old_content, created_at, expires_at, updated_at, _ = selected_ann

                with st.form("edit_announcement_form"):
                    new_title = st.text_input("标题", value=old_title, max_chars=100)
                    new_content = st.text_area("内容", value=old_content, height=200)

                    submitted = st.form_submit_button("更新公告")

                    if submitted:
                        if not new_title or not new_content:
                            st.error("标题和内容不能为空！")
                        else:
                            success = manager.update_announcement(
                                selected_id, new_title, new_content
                            )
                            if success:
                                st.success("公告更新成功！")
                                st.rerun()
                            else:
                                st.error("更新公告失败")

        with tab2:
            st.subheader("删除/恢复公告")
            all_announcements = manager.get_all_announcements(include_deleted=True)

            if not all_announcements:
                st.info("暂无公告")
            else:
                # 选择要操作的公告
                ann_options = {}
                for ann in all_announcements:
                    status = "已删除" if ann[6] else "活跃中"
                    ann_options[f"{ann[1]} (ID: {ann[0]}, 状态: {status})"] = ann[0]

                selected_label = st.selectbox("选择公告", list(ann_options.keys()))
                selected_id = ann_options[selected_label]

                # 获取选定公告的状态
                selected_ann = next(ann for ann in all_announcements if ann[0] == selected_id)
                is_deleted = selected_ann[6] is not None

                col1, col2, col3 = st.columns(3)

                with col1:
                    if not is_deleted:
                        if st.button("🗑️ 软删除公告", use_container_width=True):
                            success = manager.soft_delete_announcement(selected_id)
                            if success:
                                st.success("公告已软删除")
                                st.rerun()
                            else:
                                st.error("删除失败")
                    else:
                        if st.button("↩️ 恢复公告", use_container_width=True):
                            success = manager.restore_announcement(selected_id)
                            if success:
                                st.success("公告已恢复")
                                st.rerun()
                            else:
                                st.error("恢复失败")

                with col2:
                    if st.button("⚠️ 永久删除", use_container_width=True,
                                 help="此操作不可逆，将永久删除公告"):
                        if st.checkbox("确认永久删除"):
                            success = manager.hard_delete_announcement(selected_id)
                            if success:
                                st.success("公告已永久删除")
                                st.rerun()
                            else:
                                st.error("删除失败")

                with col3:
                    if st.button("🔄 刷新", use_container_width=True):
                        st.rerun()

        with tab3:
            st.subheader("系统管理")

            st.info("公告过期检查器运行中，每5分钟自动检查一次过期公告")

            if st.button("立即检查过期公告"):
                deleted_count = manager.check_and_delete_expired()
                if deleted_count > 0:
                    st.success(f"已删除 {deleted_count} 个过期公告")
                else:
                    st.info("没有找到过期公告")

            st.markdown("---")
            st.warning("危险区域")

            if st.button("清空所有已删除公告", help="永久删除所有标记为已删除的公告"):
                if st.checkbox("确认清空所有已删除公告（此操作不可逆）"):
                    all_announcements = manager.get_all_announcements(include_deleted=True)
                    deleted_announcements = [ann for ann in all_announcements if ann[6]]

                    success_count = 0
                    for ann in deleted_announcements:
                        if manager.hard_delete_announcement(ann[0]):
                            success_count += 1

                    st.success(f"已永久删除 {success_count} 个公告")
                    st.rerun()


if __name__ == "__main__":
    main()