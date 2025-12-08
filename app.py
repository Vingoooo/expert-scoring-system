import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 配置部分 ---
ADMIN_PASSWORD = "admin"  # 管理员密码
EXPERT_PASSWORD = "123"   # 专家密码
PROJECTS_FILE = "projects.csv"
VOTES_FILE = "votes.csv"
# 新增：用于存储专家最终提交的分数
FINAL_VOTES_FILE = "final_votes.csv" 

# --- 数据持久化函数 ---
def load_data(file_path, default_cols):
    """尝试加载CSV文件，如果文件不存在或为空，则返回空的DataFrame。"""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            for col in default_cols:
                if col not in df.columns:
                    df[col] = pd.NA
            return df.to_dict('records')
        except pd.errors.EmptyDataError:
            return []
        except Exception as e:
            st.error(f"加载数据文件 {file_path} 失败: {e}")
            return []
    return []

def save_data(df, file_path):
    """将DataFrame保存为CSV文件。"""
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    df.to_csv(file_path, index=False, encoding='utf-8')

# --- 评分标准定义 (不变) ---
CRITERIA = {
    "中期": {
        "research": {"name": "研究目标 (20分)", "desc": "项目申请书规定的阶段性研究内容是否按计划推进", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "tech": {"name": "技术指标 (30分)", "desc": "主要技术指标是否达到项目中期节点要求", "max": 30, "tips": "符合要求24~30; 基本符合18~23分; 不符合<18"},
        "deliverables": {"name": "交付物 (20分)", "desc": "交付物形成情况能否支撑后续研究顺利完成", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "output": {"name": "成果产出 (20分)", "desc": "取得阶段性技术突破，提出初步的新理论/方法；形成实验平台/仿真模型等", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "budget": {"name": "经费 (10分)", "desc": "经费使用合理合规，执行率与进度匹配", "max": 10, "tips": "符合要求8~10; 基本符合5~7; 不符合<5"}
    },
    "结题": {
        "research": {"name": "研究目标 (20分)", "desc": "项目申请书规定的研究内容是否全部实现", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "tech": {"name": "技术指标 (30分)", "desc": "主要技术指标是否全部完成", "max": 30, "tips": "符合要求24~30; 基本符合18~23分; 不符合<18"},
        "deliverables": {"name": "交付物 (20分)", "desc": "交付物是否全部完成，且质量较高", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "output": {"name": "成果产出 (20分)", "desc": "取得技术突破，攻克关键核心技术；形成成果并取得知识产权/论文等", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "budget": {"name": "经费 (10分)", "desc": "经费使用合理合规，经费执行率高", "max": 10, "tips": "符合要求8~10; 基本符合5~7; 不符合<5"}
    }
}

# --- 初始化 Session State ---
project_default_cols = ['name', 'applicant', 'stage', 'time']
vote_default_cols = ['Project Name', 'Stage', 'Expert', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget', 'Total', 'Time']

if 'projects' not in st.session_state:
    st.session_state['projects'] = load_data(PROJECTS_FILE, project_default_cols)
# ⚠️ 注意：管理员现在读取的是 'final_votes.csv'
if 'final_votes' not in st.session_state:
    st.session_state['final_votes'] = load_data(FINAL_VOTES_FILE, vote_default_cols) 

if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None 
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# 新增：专家暂存数据 (存储在内存中，直到最终提交)
if 'draft_votes' not in st.session_state:
    st.session_state['draft_votes'] = {} # 格式: {expert_name: {project_name: vote_record}}
# 新增：标记专家是否已最终提交
if 'final_submitted' not in st.session_state:
    st.session_state['final_submitted'] = {} # 格式: {expert_name: True/False}


# --- 界面逻辑 ---

st.set_page_config(page_title="大飞机研究院项目评审系统", layout="wide")
st.title("✈️ 大飞机研究院项目评审打分系统")

# 1. 登录侧边栏
with st.sidebar:
    st.header("登录")
    role = st.radio("选择角色", ["专家", "管理员"])
    
    login_name_input = ""
    if role == "专家":
        # 登录时加载该专家以前的暂存数据（如果有）
        if st.session_state.get('user_name') and st.session_state['logged_in_user'] == 'expert':
             login_name_input = st.session_state['user_name']
             st.info(f"当前专家：{login_name_input}")
        else:
             login_name_input = st.text_input("请输入您的姓名 (必填)")
    
    pwd = st.text_input("请输入密码", type="password")
    
    if st.button("登录"):
        if role == "管理员" and pwd == ADMIN_PASSWORD:
            st.session_state['logged_in_user'] = "admin"
            st.session_state['user_name'] = "管理员"
            st.success("管理员登录成功")
            st.rerun()
        elif role == "专家" and pwd == EXPERT_PASSWORD:
            if login_name_input.strip():
                st.session_state['logged_in_user'] = "expert"
                st.session_state['user_name'] = login_name_input 
                # 初始化该专家的暂存区和提交状态
                if login_name_input not in st.session_state['draft_votes']:
                    st.session_state['draft_votes'][login_name_input] = {}
                if login_name_input not in st.session_state['final_submitted']:
                    # 检查是否已存在于最终提交列表中
                    submitted = any(v['Expert'] == login_name_input for v in st.session_state['final_votes'])
                    st.session_state['final_submitted'][login_name_input] = submitted
                    
                st.success(f"欢迎您，{login_name_input} 专家")
                st.rerun()
            else:
                st.error("专家登录必须要输入姓名！")
        else:
            st.error("密码错误")

    if st.button("退出登录"):
        st.session_state['logged_in_user'] = None
        st.session_state['user_name'] = ""
        st.rerun()

# 2. 主要功能区
user_type = st.session_state['logged_in_user']
current_user_name = st.session_state['user_name']

# =================================================================
#                         管理员控制台
# =================================================================
if user_type == "admin":
    st.header("🔧 管理员控制台")
    
    # ... [管理员代码：添加项目, 项目与评分管理] (使用 final_votes.csv) ...
    
    # 2.1 添加项目 (新增写入 PROJECTS_FILE)
    with st.expander("➕ 添加新项目", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        new_name = c1.text_input("项目名称")
        new_applicant = c2.text_input("申请人")
        new_stage = c3.selectbox("评审阶段", ["中期", "结题"])
        new_time = c4.number_input("时长", value=30)
        
        if st.button("添加项目"):
            if new_name:
                if any(p['name'] == new_name for p in st.session_state['projects']):
                    st.error("该项目名称已存在！")
                else:
                    new_project = {
                        "name": new_name,
                        "applicant": new_applicant,
                        "stage": new_stage,
                        "time": new_time
                    }
                    st.session_state['projects'].append(new_project)
                    save_data(pd.DataFrame(st.session_state['projects']), PROJECTS_FILE)
                    st.success(f"项目 **{new_name}** 添加成功！数据已保存。")
                    st.rerun()
            else:
                st.warning("请输入项目名称")
    
    # 2.2 项目删减功能 (使用 final_votes.csv)
    st.divider()
    st.subheader("🗑️ 项目与评分管理")
    
    if st.session_state['projects']:
        project_names = [p['name'] for p in st.session_state['projects']]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            project_to_manage = st.selectbox("选择要管理的项目", project_names)
        
        with col2:
            st.markdown("##### 选择操作")
            c_del1, c_del2 = st.columns(2)
            
            # --- 功能 1: 清空评分 ---
            if c_del1.button("清空项目评分", help="只删除该项目的所有专家最终提交的打分，项目本身保留"):
                initial_votes_count = len(st.session_state['final_votes'])
                st.session_state['final_votes'] = [
                    v for v in st.session_state['final_votes'] if v['Project Name'] != project_to_manage
                ]
                
                votes_deleted = initial_votes_count - len(st.session_state['final_votes'])
                
                save_data(pd.DataFrame(st.session_state['final_votes']), FINAL_VOTES_FILE)
                st.success(f"✅ 项目 **{project_to_manage}** 的 **{votes_deleted}** 条最终评分已清空并保存！")
                st.rerun()
            
            # --- 功能 2: 删除整个项目 ---
            if c_del2.button("❌ 删除整个项目", type="primary", help="删除项目本身，以及该项目所有的专家最终提交的打分"):
                st.session_state['projects'] = [
                    p for p in st.session_state['projects'] if p['name'] != project_to_manage
                ]
                st.session_state['final_votes'] = [
                    v for v in st.session_state['final_votes'] if v['Project Name'] != project_to_manage
                ]
                
                save_data(pd.DataFrame(st.session_state['projects']), PROJECTS_FILE)
                save_data(pd.DataFrame(st.session_state['final_votes']), FINAL_VOTES_FILE)
                st.error(f"🗑️ 项目 **{project_to_manage}** 已被彻底删除！")
                st.rerun()
    else:
        st.info("暂无项目可供管理。")
        
    # 2.3 数据报表区 (使用 final_votes.csv)
    st.divider()
    st.subheader("📊 评审数据汇总")
    
    if st.session_state['final_votes']:
        all_votes_df = pd.DataFrame(st.session_state['final_votes'])
        all_votes_df['Total'] = all_votes_df[['Research', 'Tech', 'Deliverables', 'Output', 'Budget']].sum(axis=1)

        st.markdown("### 1️⃣ 各项目打分明细")
        unique_projects = all_votes_df['Project Name'].unique()
        
        for proj_name in unique_projects:
            with st.expander(f"📁 项目：{proj_name} (点击展开详情)", expanded=False): 
                proj_df = all_votes_df[all_votes_df['Project Name'] == proj_name].copy()
                display_cols = ['Expert', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget', 'Total', 'Time']
                st.dataframe(proj_df[display_cols], use_container_width=True)

        st.markdown("### 2️⃣ 最终平均分汇总表")
        summary_df = all_votes_df.groupby("Project Name")[['Total', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget']].mean().reset_index()
        summary_df = summary_df.round(2)
        summary_df = summary_df.sort_values(by="Total", ascending=False)
        
        st.dataframe(summary_df, use_container_width=True)
        
    else:
        st.info("暂无任何最终提交的打分数据。")

# =================================================================
#                           专家评审界面
# =================================================================
elif user_type == "expert":
    st.header(f"📝 专家评审：{current_user_name}")
    
    # 检查是否已最终提交
    is_submitted = st.session_state['final_submitted'].get(current_user_name, False)
    
    if not st.session_state['projects']:
        st.warning("管理员暂未发布评审项目。")
        is_submitted = True # 如果没有项目，则认为评审完成
    
    if is_submitted:
        st.success("🎉 您已完成所有项目的最终提交。感谢您的评审！")
        st.info("如需修改，请联系管理员。")
    
    else:
        # 获取当前专家暂存的评分
        my_drafts = st.session_state['draft_votes'].get(current_user_name, {})
        
        # -------------------------------------------------------------
        # 3. 评分总览表 (新增)
        # -------------------------------------------------------------
        st.divider()
        st.subheader("📋 评分总览与最终提交")
        
        if st.session_state['projects']:
            summary_data = []
            
            for p in st.session_state['projects']:
                p_name = p['name']
                
                if p_name in my_drafts:
                    draft = my_drafts[p_name]
                    status = "✅ 已暂存"
                    total = draft.get('Total', 0)
                else:
                    status = "⏳ 待评分"
                    total = 0
                
                summary_data.append({
                    "项目名称": p_name,
                    "阶段": p['stage'],
                    "当前总分": total,
                    "状态": status,
                    "进入修改": p_name # 用于识别点击的项目
                })
            
            summary_df = pd.DataFrame(summary_data)
            
            # 使用 st.data_editor 来实现表格点击跳转
            st.caption("点击表格最后一列的项目名称，进入修改界面。")
            edited_df = st.data_editor(
                summary_df,
                column_config={
                    "进入修改": st.column_config.ButtonColumn(
                        "进入修改",
                        help="点击进入该项目的详细评分界面",
                        key="edit_button_col"
                    )
                },
                disabled=["项目名称", "阶段", "当前总分", "状态"],
                hide_index=True,
                use_container_width=True
            )
            
            # 检测按钮点击事件
            clicked_rows = edited_df[edited_df["进入修改"] == True]
            if not clicked_rows.empty:
                clicked_project_name = clicked_rows.iloc[0]['项目名称']
                st.session_state['selected_project_for_edit'] = clicked_project_name
                st.rerun() # 触发页面刷新，进入详细评分区
            
            # -------------------------------------------------------------
            # 4. 最终提交按钮 (新增)
            # -------------------------------------------------------------
            
            # 检查是否所有项目都已暂存
            all_scored = len(my_drafts) == len(st.session_state['projects'])
            
            if all_scored:
                st.markdown("---")
                if st.button("最终提交所有评分", type="primary", help="提交后将无法修改，并向管理员报送最终分数。"):
                    # 使用 st.form 来模拟确认弹窗
                    with st.form("final_submission_form", clear_on_submit=True):
                        st.warning(f"⚠️ **您确定要最终提交所有 {len(st.session_state['projects'])} 个项目评分吗？** 提交后将无法修改。")
                        
                        if st.form_submit_button("确认提交"):
                            
                            # 1. 整理并写入 final_votes.csv
                            final_vote_list = list(my_drafts.values())
                            final_votes_df = pd.DataFrame(final_vote_list)
                            
                            # 2. 从 final_votes 中移除当前专家的旧数据，并添加新数据
                            # 确保不会重复提交，如果已经提交过，旧的会被覆盖 (用于管理员清空后重新提交)
                            st.session_state['final_votes'] = [
                                v for v in st.session_state['final_votes'] if v['Expert'] != current_user_name
                            ]
                            st.session_state['final_votes'].extend(final_vote_list)
                            
                            # 保存到 CSV
                            save_data(pd.DataFrame(st.session_state['final_votes']), FINAL_VOTES_FILE)
                            
                            # 3. 更新提交状态
                            st.session_state['final_submitted'][current_user_name] = True
                            st.success("✅ 所有评分已成功提交！")
                            st.rerun()
            else:
                st.warning(f"请先完成所有 {len(st.session_state['projects'])} 个项目的评分暂存，当前已暂存 {len(my_drafts)} 个。")
        
        st.divider()
        
        # -------------------------------------------------------------
        # 5. 详细评分界面 (Form)
        # -------------------------------------------------------------
        
        # 如果从表格跳转过来，则使用跳转的项目，否则使用第一个待评分的项目
        if 'selected_project_for_edit' in st.session_state:
             selected_project_name = st.session_state.pop('selected_project_for_edit') # 使用后即清除
        else:
             # 默认选择第一个未暂存的项目，如果没有则选择第一个项目
             default_name = next((p['name'] for p in st.session_state['projects'] if p['name'] not in my_drafts), st.session_state['projects'][0]['name'])
             selected_project_name = st.selectbox("选择或修改项目评分", [p['name'] for p in st.session_state['projects']], index=[p['name'] for p in st.session_state['projects']].index(default_name))
        
        project_data = next((p for p in st.session_state['projects'] if p['name'] == selected_project_name), None)
        
        if project_data:
            stage_type = project_data['stage']
            
            st.subheader(f"项目评分详情：{project_data['name']}")
            st.info(f"申请人：{project_data['applicant']} | 阶段：**{stage_type}** | 汇报时长：{project_data['time']}分钟")
            
            rubric = CRITERIA[stage_type]
            
            # 获取暂存数据，用于回填表单
            initial_draft = my_drafts.get(selected_project_name, {})
            
            # 使用 st.form 实现暂存逻辑
            with st.form("grading_form"):
                st.markdown(f"### {stage_type}评分标准")
                
                # 定义初始值 (若有暂存，则使用暂存数据，否则使用默认值)
                def get_initial_score(key, max_val):
                    if key in initial_draft:
                        return initial_draft[key]
                    return max_val - 2 if max_val > 2 else 0

                s1 = st.slider(f"1. {rubric['research']['name']}", 0, rubric['research']['max'], get_initial_score('Research', rubric['research']['max']), key="s1_form", help=rubric['research']['tips'])
                st.caption(rubric['research']['desc'])
                
                s2 = st.slider(f"2. {rubric['tech']['name']}", 0, rubric['tech']['max'], get_initial_score('Tech', rubric['tech']['max']), key="s2_form", help=rubric['tech']['tips'])
                st.caption(rubric['tech']['desc'])
                
                s3 = st.slider(f"3. {rubric['deliverables']['name']}", 0, rubric['deliverables']['max'], get_initial_score('Deliverables', rubric['deliverables']['max']), key="s3_form", help=rubric['deliverables']['tips'])
                st.caption(rubric['deliverables']['desc'])
                
                s4 = st.slider(f"4. {rubric['output']['name']}", 0, rubric['output']['max'], get_initial_score('Output', rubric['output']['max']), key="s4_form", help=rubric['output']['tips'])
                st.caption(rubric['output']['desc'])
                
                s5 = st.slider(f"5. {rubric['budget']['name']}", 0, rubric['budget']['max'], get_initial_score('Budget', rubric['budget']['max']), key="s5_form", help=rubric['budget']['tips'])
                st.caption(rubric['budget']['desc'])
                
                total_score = s1 + s2 + s3 + s4 + s5
                st.markdown(f"#### 🚀 当前总分: **{total_score}** / 100 分")

                if st.form_submit_button("💾 暂存评分"):
                    vote_record = {
                        "Project Name": selected_project_name,
                        "Stage": stage_type,
                        "Expert": current_user_name,
                        "Research": s1,
                        "Tech": s2,
                        "Deliverables": s3,
                        "Output": s4,
                        "Budget": s5,
                        "Total": total_score, # 暂存时计算总分
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    # 写入内存中的暂存区
                    st.session_state['draft_votes'][current_user_name][selected_project_name] = vote_record
                    st.success(f"✅ 项目 **{selected_project_name}** 评分已暂存！总分：{total_score}")
                    st.rerun() 

# =================================================================
#                             未登录状态
# =================================================================
else:
    st.info("👈 请在左侧登录")
    st.markdown("""
    ### 使用说明
    1. **管理员**：密码 `admin`，负责添加项目、管理数据、查看汇总。
    2. **专家**：密码 `123`，输入姓名后即可进入打分。
    """)