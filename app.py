import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 配置部分 ---
ADMIN_PASSWORD = "admin"  # 管理员密码
EXPERT_PASSWORD = "123"   # 专家密码
PROJECTS_FILE = "projects.csv"
VOTES_FILE = "votes.csv"

# --- 数据持久化函数 ---
def load_data(file_path, default_cols):
    """尝试加载CSV文件，如果文件不存在或为空，则返回空的DataFrame。"""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            # 检查列是否完整，如果缺失则补充空列，保证后续操作不出错
            missing_cols = [col for col in default_cols if col not in df.columns]
            for col in missing_cols:
                df[col] = pd.NA
            # 确保返回的是列表格式以便在 session_state 中操作
            return df.to_dict('records')
        except pd.errors.EmptyDataError:
            return []
    return []

def save_data(df, file_path):
    """将DataFrame保存为CSV文件。"""
    # 确保文件所在的目录存在
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    df.to_csv(file_path, index=False, encoding='utf-8')

# --- 评分标准定义 (不变) ---
CRITERIA = {
    "中期": {
        "research": {"name": "研究目标 (20分)", "desc": "项目申请书规定的阶段性研究内容是否按计划推进", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "tech": {"name": "技术指标 (30分)", "desc": "主要技术指标是否达到项目中期节点要求", "max": 30, "tips": "符合要求24~30; 基本符合18~23; 不符合<18"},
        "deliverables": {"name": "交付物 (20分)", "desc": "交付物形成情况能否支撑后续研究顺利完成", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "output": {"name": "成果产出 (20分)", "desc": "取得阶段性技术突破，提出初步新理论/方法；形成实验平台/仿真模型等", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "budget": {"name": "经费 (10分)", "desc": "经费使用合理合规，执行率与进度匹配", "max": 10, "tips": "符合要求8~10; 基本符合5~7; 不符合<5"}
    },
    "结题": {
        "research": {"name": "研究目标 (20分)", "desc": "项目申请书规定的研究内容是否全部实现", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "tech": {"name": "技术指标 (30分)", "desc": "主要技术指标是否全部完成", "max": 30, "tips": "符合要求24~30; 基本符合18~23; 不符合<18"},
        "deliverables": {"name": "交付物 (20分)", "desc": "交付物是否全部完成，且质量较高", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "output": {"name": "成果产出 (20分)", "desc": "取得技术突破，攻克关键核心技术；形成成果并取得知识产权/论文等", "max": 20, "tips": "符合要求16~20; 基本符合12~15; 不符合<12"},
        "budget": {"name": "经费 (10分)", "desc": "经费使用合理合规，经费执行率高", "max": 10, "tips": "符合要求8~10; 基本符合5~7; 不符合<5"}
    }
}

# --- 初始化 Session State (从文件加载数据) ---
if 'projects' not in st.session_state:
    st.session_state['projects'] = load_data(PROJECTS_FILE, ['name', 'applicant', 'stage', 'time'])
if 'votes' not in st.session_state:
    st.session_state['votes'] = load_data(VOTES_FILE, ['Project Name', 'Stage', 'Expert', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget', 'Time'])
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None 
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# --- 界面逻辑 (大部分不变) ---

st.set_page_config(page_title="大飞机研究院项目评审系统", layout="wide")
st.title("✈️ 大飞机研究院项目评审打分系统")

# 1. 登录侧边栏
with st.sidebar:
    st.header("登录")
    role = st.radio("选择角色", ["专家", "管理员"])
    
    login_name_input = ""
    if role == "专家":
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

if user_type == "admin":
    st.header("🔧 管理员控制台")
    
    # 添加项目 (新增写入 CSV)
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
                    # 将更新后的数据保存到 CSV
                    save_data(pd.DataFrame(st.session_state['projects']), PROJECTS_FILE)
                    st.success(f"项目 {new_name} 添加成功！数据已保存。")
                    st.rerun()
            else:
                st.warning("请输入项目名称")

    # 数据报表区 (使用最新加载的数据)
    st.divider()
    st.subheader("📊 评审数据汇总")
    
    if st.session_state['votes']:
        all_votes_df = pd.DataFrame(st.session_state['votes'])
        all_votes_df['Total'] = all_votes_df[['Research', 'Tech', 'Deliverables', 'Output', 'Budget']].sum(axis=1)

        # 1. 按项目展示详细打分表
        st.markdown("### 1️⃣ 各项目打分明细")
        unique_projects = all_votes_df['Project Name'].unique()
        
        for proj_name in unique_projects:
            with st.expander(f"📁 项目：{proj_name} (点击展开详情)", expanded=True):
                proj_df = all_votes_df[all_votes_df['Project Name'] == proj_name].copy()
                display_cols = ['Expert', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget', 'Total', 'Time']
                st.dataframe(proj_df[display_cols], use_container_width=True)

        # 2. 最终汇总表
        st.markdown("### 2️⃣ 最终平均分汇总表")
        summary_df = all_votes_df.groupby("Project Name")[['Total', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget']].mean().reset_index()
        summary_df = summary_df.round(2)
        summary_df = summary_df.sort_values(by="Total", ascending=False)
        
        st.dataframe(summary_df, use_container_width=True)
        
    else:
        st.info("暂无任何打分数据。")

    # 查看原始项目列表
    with st.expander("查看所有项目配置"):
        if st.session_state['projects']:
            st.table(pd.DataFrame(st.session_state['projects']))
        else:
            st.write("暂无项目")

elif user_type == "expert":
    st.header(f"📝 专家评审：{current_user_name}")
    
    if not st.session_state['projects']:
        st.warning("管理员暂未发布评审项目。")
    else:
        # 获取当前专家已评的项目名称列表
        my_votes = [v['Project Name'] for v in st.session_state['votes'] if v['Expert'] == current_user_name]
        
        # 构建下拉菜单的选项，带状态标记
        project_options = []
        for p in st.session_state['projects']:
            p_name = p['name']
            status = "✅ 已评分" if p_name in my_votes else "⏳ 待评分"
            project_options.append(f"{p_name} | {status}")
        
        selected_option = st.selectbox("请选择要评审的项目", project_options)
        
        selected_project_name = selected_option.split(" | ")[0]
        
        if selected_project_name in my_votes:
            st.success(f"🎉 项目 **{selected_project_name}** 您已完成打分。")
        else:
            project_data = next((p for p in st.session_state['projects'] if p['name'] == selected_project_name), None)
            
            if project_data:
                stage_type = project_data['stage']
                st.info(f"正在评审：**{project_data['name']}** | 申请人：{project_data['applicant']} | 阶段：**{stage_type}**")
                
                rubric = CRITERIA[stage_type]
                
                with st.form("grading_form"):
                    st.markdown(f"### {stage_type}评分标准")
                    
                    # 使用默认值以减少鼠标操作
                    s1_default = rubric['research']['max'] - 2 if rubric['research']['max'] > 2 else 0
                    s2_default = rubric['tech']['max'] - 3 if rubric['tech']['max'] > 3 else 0
                    s3_default = rubric['deliverables']['max'] - 2 if rubric['deliverables']['max'] > 2 else 0
                    s4_default = rubric['output']['max'] - 2 if rubric['output']['max'] > 2 else 0
                    s5_default = rubric['budget']['max'] - 1 if rubric['budget']['max'] > 1 else 0
                    
                    st.markdown(f"**1. {rubric['research']['name']}**")
                    st.caption(rubric['research']['desc'])
                    s1 = st.slider("得分", 0, rubric['research']['max'], s1_default, key="s1", help=rubric['research']['tips'])
                    
                    st.markdown(f"**2. {rubric['tech']['name']}**")
                    st.caption(rubric['tech']['desc'])
                    s2 = st.slider("得分", 0, rubric['tech']['max'], s2_default, key="s2", help=rubric['tech']['tips'])
                    
                    st.markdown(f"**3. {rubric['deliverables']['name']}**")
                    st.caption(rubric['deliverables']['desc'])
                    s3 = st.slider("得分", 0, rubric['deliverables']['max'], s3_default, key="s3", help=rubric['deliverables']['tips'])
                    
                    st.markdown(f"**4. {rubric['output']['name']}**")
                    st.caption(rubric['output']['desc'])
                    s4 = st.slider("得分", 0, rubric['output']['max'], s4_default, key="s4", help=rubric['output']['tips'])
                    
                    st.markdown(f"**5. {rubric['budget']['name']}**")
                    st.caption(rubric['budget']['desc'])
                    s5 = st.slider("得分", 0, rubric['budget']['max'], s5_default, key="s5", help=rubric['budget']['tips'])
                    
                    submitted = st.form_submit_button("提交评分")
                    
                    if submitted:
                        vote_record = {
                            "Project Name": project_data['name'],
                            "Stage": stage_type,
                            "Expert": current_user_name,
                            "Research": s1,
                            "Tech": s2,
                            "Deliverables": s3,
                            "Output": s4,
                            "Budget": s5,
                            "Time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state['votes'].append(vote_record)
                        # 将更新后的数据保存到 CSV
                        save_data(pd.DataFrame(st.session_state['votes']), VOTES_FILE)
                        st.success("评分提交成功！数据已保存。")
                        st.rerun() 

else:
    st.info("👈 请在左侧登录")
    st.markdown("""
    ### 使用说明
    1. **管理员**：密码 `admin`，负责添加项目、查看汇总。
    2. **专家**：密码 `123`，输入姓名后即可进入打分。
    """)