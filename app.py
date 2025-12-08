import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 配置部分 ---
ADMIN_PASSWORD = "admin"  # 管理员密码
EXPERT_PASSWORD = "123"   # 专家密码
PROJECTS_FILE = "projects.csv"
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

# --- 评分标准定义 (已修正波浪号为转义字符 '\~') ---
CRITERIA = {
    "中期": {
        "research": {"name": "研究目标 (20分)", "desc": "项目申请书规定的阶段性研究内容是否按计划推进", "max": 20, "tips": "符合要求16\~20分；基本符合12\~15分；不符合＜12分。"},
        "tech": {"name": "技术指标 (30分)", "desc": "主要技术指标是否达到项目中期节点要求", "max": 30, "tips": "符合要求24\~30分；基本符合18\~23分；不符合＜18分。"},
        "deliverables": {"name": "交付物 (20分)", "desc": "交付物形成情况能否支撑后续研究顺利完成", "max": 20, "tips": "符合要求16\~20分；基本符合12\~15分；不符合＜12分。"},
        "output": {"name": "成果产出 (20分)", "desc": "取得阶段性技术突破，提出初步的新理论、新方法；形成实验平台/仿真模型等", "max": 20, "tips": "符合要求16\~20分；基本符合12\~15分；不符合＜12分。"},
        "budget": {"name": "经费 (10分)", "desc": "经费使用合理合规，执行率与进度匹配", "max": 10, "tips": "符合要求8\~10分；基本符合5\~7分；不符合＜5分。"}
    },
    "结题": {
        "research": {"name": "研究目标 (20分)", "desc": "项目申请书规定的研究内容是否全部实现", "max": 20, "tips": "符合要求16\~20分；基本符合12\~15分；不符合＜12分。"},
        "tech": {"name": "技术指标 (30分)", "desc": "主要技术指标是否全部完成", "max": 30, "tips": "符合要求24\~30分；基本符合18\~23分；不符合＜18分。"},
        "deliverables": {"name": "交付物 (20分)", "desc": "交付物是否全部完成，且质量较高", "max": 20, "tips": "符合要求16\~20分；基本符合12\~15分；不符合＜12分。"},
        "output": {"name": "成果产出 (20分)", "desc": "取得技术突破，攻克关键核心技术；形成成果并取得知识产权/论文等", "max": 20, "tips": "符合要求16\~20分；基本符合12\~15分；不符合＜12分。"},
        "budget": {"name": "经费 (10分)", "desc": "经费使用合理合规，经费执行率高", "max": 10, "tips": "符合要求8\~10分；基本符合5\~7分；不符合＜5分。"}
    }
}

# --- 初始化 Session State ---
project_default_cols = ['name', 'applicant', 'stage', 'time']
vote_default_cols = ['Project Name', 'Stage', 'Expert', 'Research', 'Tech', 'Deliverables', 'Output', 'Budget', 'Total', 'Time']

if 'projects' not in st.session_state:
    st.session_state['projects'] = load_data(PROJECTS_FILE, project_default_cols)
if 'final_votes' not in st.session_state:
    st.session_state['final_votes'] = load_data(FINAL_VOTES_FILE, vote_default_cols) 

if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None 
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

if 'draft_votes' not in st.session_state:
    st.session_state['draft_votes'] = {} 
if 'final_submitted' not in st.session_state:
    st.session_state['final_submitted'] = {} 

# 初始化或更新实时分数缓存
if 'live_scores' not in st.session_state:
    st.session_state['live_scores'] = {}
if 'last_selected_project' not in st.session_state:
    st.session_state['last_selected_project'] = None
if 'current_errors' not in st.session_state:
    st.session_state['current_errors'] = []

# 用于显示操作成功的临时状态
if 'show_success' not in st.session_state:
    st.session_state['show_success'] = None


# --- 界面逻辑 ---

st.set_page_config(page_title="大飞机研究院项目评审系统", layout="wide")
st.title("✈️ 大飞机研究院项目评审打分系统")

# 检查并显示操作成功的提示框
if st.session_state['show_success']:
    st.toast(st.session_state['show_success'])
    st.session_state['show_success'] = None


# 1. 登录侧边栏
with st.sidebar:
    st.header("登录")
    role = st.radio("选择角色", ["专家", "管理员"])
    
    login_name_input = ""
    if role == "专家":
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
                
                if login_name_input not in st.session_state['draft_votes']:
                    st.session_state['draft_votes'][login_name_input] = {}
                
                # 如果当前专家没有最终提交记录，或者管理员清空了所有专家的记录，则需要重新检查
                if login_name_input not in st.session_state['final_submitted'] or not st.session_state['final_submitted'].get(login_name_input, False):
                    # 检查该专家是否已对所有项目完成最终提交
                    submitted = all(any(v['Project Name'] == p['name'] and v['Expert'] == login_name_input for v in st.session_state['final_votes']) 
                                    for p in st.session_state['projects'])
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
    
    # 2.1 添加项目 (已优化)
    with st.expander("➕ 添加新项目", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        new_name = c1.text_input("项目名称", key="new_project_name")
        new_applicant = c2.text_input("申请人", key="new_project_applicant")
        new_stage = c3.selectbox("评审阶段", ["中期", "结题"], key="new_project_stage")
        new_time = c4.number_input("时长", value=30, key="new_project_time")
        
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
                    
                    # 项目列表变动，重置所有专家的最终提交锁定状态
                    st.session_state['final_submitted'] = {} 
                    
                    st.session_state['show_success'] = f"项目 **{new_name}** 添加成功！"
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
            project_to_manage = st.selectbox("选择要管理的项目", project_names, key="manage_project_select")
        
        with col2:
            st.markdown("##### 选择操作")
            c_del1, c_del2 = st.columns(2)
            
            # --- 功能 1: 清空评分 (已优化) ---
            if c_del1.button(f"清空 {project_to_manage} 评分", help="只删除该项目的所有专家最终提交的打分，项目本身保留"):
                initial_votes_count = len(st.session_state['final_votes'])
                st.session_state['final_votes'] = [
                    v for v in st.session_state['final_votes'] if v['Project Name'] != project_to_manage
                ]
                
                votes_deleted = initial_votes_count - len(st.session_state['final_votes'])
                
                save_data(pd.DataFrame(st.session_state['final_votes']), FINAL_VOTES_FILE)
                
                # 清空分数后，所有专家需要重新提交，重置锁定状态，使评分页可见
                st.session_state['final_submitted'] = {} 

                st.session_state['show_success'] = f"项目 **{project_to_manage}** 的 {votes_deleted} 条最终评分已清空！"
                st.rerun()
            
            # --- 功能 2: 删除整个项目 (已优化) ---
            if c_del2.button(f"❌ 删除 {project_to_manage} 项目", type="primary", help="删除项目本身，以及该项目所有的专家最终提交的打分"):
                st.session_state['projects'] = [
                    p for p in st.session_state['projects'] if p['name'] != project_to_manage
                ]
                st.session_state['final_votes'] = [
                    v for v in st.session_state['final_votes'] if v['Project Name'] != project_to_manage
                ]
                
                save_data(pd.DataFrame(st.session_state['projects']), PROJECTS_FILE)
                save_data(pd.DataFrame(st.session_state['final_votes']), FINAL_VOTES_FILE)
                
                # 删除项目后，所有专家需要重新提交，重置锁定状态
                st.session_state['final_submitted'] = {} 
                
                st.session_state['show_success'] = f"项目 **{project_to_manage}** 已被彻底删除！"
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
    
    is_submitted = st.session_state['final_submitted'].get(current_user_name, False)
    
    if not st.session_state['projects']:
        st.warning("管理员暂未发布评审项目。")
        
    # 如果全局已锁定，直接显示已完成
    if is_submitted:
        st.success("🎉 您已完成所有项目的最终提交。感谢您的评审！")
        st.info("如需修改，请联系管理员。")
    
    else:
        # 1. 获取当前专家显式暂存的评分
        explicit_drafts = st.session_state['draft_votes'].get(current_user_name, {})

        # 2. 获取当前专家已提交的最终评分 (作为未显式暂存的草稿源)
        submitted_final_votes = {
            v['Project Name']: v 
            for v in st.session_state['final_votes'] 
            if v['Expert'] == current_user_name
        }
        
        # 3. 合并：以 explicit_drafts 为准，形成完整的“待提交评分集合” (my_effective_drafts)
        # 这个集合是用于总览和最终提交检查的唯一真实来源。
        my_effective_drafts = submitted_final_votes.copy()
        my_effective_drafts.update(explicit_drafts) # 显式暂存的覆盖已提交的
        
        # -------------------------------------------------------------
        # 3. 评分总览表 & 最终提交
        # -------------------------------------------------------------
        st.divider()
        st.subheader("📋 评分总览与最终提交")
        
        if st.session_state['projects']:
            summary_data = []
            project_names_list = []
            
            for p in st.session_state['projects']:
                p_name = p['name']
                project_names_list.append(p_name)
                
                # 状态判断基于 my_effective_drafts
                if p_name in my_effective_drafts:
                    effective_vote = my_effective_drafts[p_name]
                    total = effective_vote['Total']
                    
                    # 状态显示：
                    if p_name in explicit_drafts:
                        status = "💾 已暂存" 
                    elif p_name in submitted_final_votes:
                        # 只有在 global is_submitted=False 且项目未被重新暂存时，才显示此状态
                        status = "✅ 已提交" 
                    else:
                         status = "⏳ 待评分" # 理论上不发生
                         
                else:
                    status = "⏳ 待评分"
                    total = 0
                
                summary_data.append({
                    "项目名称": p_name,
                    "阶段": p['stage'],
                    "当前总分": total,
                    "状态": status,
                })
            
            summary_df = pd.DataFrame(summary_data)
            
            # 1. 显示简化后的总览表
            st.dataframe(summary_df, hide_index=True, use_container_width=True)
            
            # 2. 最终提交按钮
            all_scored = len(my_effective_drafts) == len(st.session_state['projects'])
            
            if all_scored:
                st.markdown("---")
                st.warning(f"⚠️ **请确认所有 {len(st.session_state['projects'])} 个项目评分准确无误。** 提交后将无法修改。")
                
                # 使用单个按钮直接提交
                if st.button("最终确认并提交所有评分", key="final_submission_button", type="primary", help="提交后将无法修改，并向管理员报送最终分数。"):
                    # 提交前进行最终验证 (针对当前选中的项目)
                    if st.session_state['current_errors']:
                        st.error("最终提交失败：请先修正当前选定项目中的所有评分错误。")
                        st.stop()
                        
                    final_vote_list = list(my_effective_drafts.values()) # <--- 使用合并后的集合进行提交
                    
                    # 核心逻辑：更新 final_votes
                    st.session_state['final_votes'] = [
                        v for v in st.session_state['final_votes'] if v['Expert'] != current_user_name
                    ]
                    st.session_state['final_votes'].extend(final_vote_list)
                    
                    # 3. 保存数据到文件
                    save_data(pd.DataFrame(st.session_state['final_votes']), FINAL_VOTES_FILE)
                    
                    # 4. 更新状态并刷新
                    st.session_state['final_submitted'][current_user_name] = True
                    # 提交成功后，清除所有暂存分数，防止下次误用
                    st.session_state['draft_votes'][current_user_name] = {}
                    st.session_state['show_success'] = "所有评分已成功提交！"
                    st.rerun() 
            else:
                st.warning(f"请先完成所有 {len(st.session_state['projects'])} 个项目的评分暂存，当前已完成 **{len(my_effective_drafts)}** 个。")
        
        st.divider()
        
        # -------------------------------------------------------------
        # 4. 详细评分界面 (文本输入与实时验证)
        # -------------------------------------------------------------
        
        if st.session_state['projects']:
            # 默认选择逻辑
            default_name = next((p['name'] for p in st.session_state['projects'] if p['name'] not in my_effective_drafts), st.session_state['projects'][0]['name'])
            default_index = project_names_list.index(default_name)
            
            selected_project_name = st.selectbox(
                "⬇️ 选择要评分或修改的项目", 
                project_names_list, 
                index=default_index,
                key='project_selector', 
                help="在上方总览表查看评分状态，在此选择项目进行详细评分或修改。",
            )
            
            project_data = next((p for p in st.session_state['projects'] if p['name'] == selected_project_name), None)
            
            if project_data:
                stage_type = project_data['stage']
                
                # --- 新增项目级锁定检查 ---
                # 只有在 global is_submitted=True (专家已提交) 且 final_votes 中存在本专家本项目的分数时，才锁定。
                # 由于 global is_submitted=False 已经进入本 else 块，所以我们只需要检查 final_votes 中是否存在该项目的分数，并检查是否被重新暂存过。
                project_is_locked = (
                    selected_project_name in submitted_final_votes and # 最终表中有记录
                    selected_project_name not in explicit_drafts        # 专家没有重新暂存
                )
                
                # 如果管理员清空了分数，selected_project_name 不在 submitted_final_votes 中，project_is_locked 为 False

                st.subheader(f"项目评分详情：{project_data['name']}")
                st.info(f"申请人：{project_data['applicant']} | 阶段：**{stage_type}** | 汇报时长：{project_data['time']}分钟")
                
                if project_is_locked:
                    st.warning("🔒 **此项目评分已最终提交，无法修改或暂存。** 若需修改，请联系管理员清空本项目的最终评分。")
                
                # 定义评分标准
                rubric = CRITERIA[stage_type]
                
                # 使用合并后的有效评分作为初始草稿源
                initial_draft_source = my_effective_drafts.get(selected_project_name, {})
                
                criteria_keys = ['Research', 'Tech', 'Deliverables', 'Output', 'Budget']
                rubric_map = {
                    'Research': rubric['research'], 'Tech': rubric['tech'], 'Deliverables': rubric['deliverables'],
                    'Output': rubric['output'], 'Budget': rubric['budget']
                }
                display_map = {
                    'Research': 1, 'Tech': 2, 'Deliverables': 3, 'Output': 4, 'Budget': 5
                }
                
                # --- 初始化 live_scores ---
                def get_initial_value(key, initial_draft):
                    """获取初始值。如果有暂存数据则返回，否则返回空字符串。"""
                    if key in initial_draft:
                        return str(initial_draft[key])
                    return ""
                    
                # 切换项目时，用该项目的暂存数据初始化 live_scores
                if st.session_state['last_selected_project'] != selected_project_name:
                    
                    # 无论是否锁定，都从有效评分源加载
                    st.session_state['live_scores'] = {
                        key: get_initial_value(key, initial_draft_source) for key in criteria_keys
                    }
                        
                    st.session_state['last_selected_project'] = selected_project_name
                    st.session_state['current_errors'] = []
                
                # --- 实时验证和计算总分 ---
                valid_scores = {}
                current_errors = []

                # 仅在项目未锁定时才进行实时验证
                if not project_is_locked:
                    for key in criteria_keys:
                        # 从 session state 获取 text_input 的当前值
                        input_key = f"text_input_{key}"
                        input_value_str = st.session_state.get(input_key, st.session_state['live_scores'].get(key, ""))
                        
                        max_val = rubric_map[key]['max']
                        
                        try:
                            # 尝试转换为整数
                            score = int(input_value_str)
                            if 0 <= score <= max_val:
                                valid_scores[key] = score
                                st.session_state['live_scores'][key] = str(score) 
                            else:
                                current_errors.append(f"❌ {rubric_map[key]['name']}：分数必须是 0 到 {max_val} 之间的整数。您输入了 {input_value_str}。")
                                valid_scores[key] = 0 
                        except ValueError:
                            if input_value_str.strip() == "":
                                valid_scores[key] = 0 
                                st.session_state['live_scores'][key] = "" 
                            else:
                                current_errors.append(f"❌ {rubric_map[key]['name']}：输入值 '{input_value_str}' 必须是整数。")
                                valid_scores[key] = 0
                                
                    live_total_score = sum(valid_scores.values())
                    st.session_state['current_errors'] = current_errors # 存储错误列表
                else:
                    # 如果项目锁定，分数取自 initial_draft_source，且不产生错误
                    valid_scores = {key: initial_draft_source.get(key, 0) for key in criteria_keys}
                    live_total_score = initial_draft_source.get('Total', 0)
                    st.session_state['current_errors'] = []

                # --- 显示错误和实时总分 ---
                if st.session_state['current_errors']:
                    st.error("请修正以下所有评分错误，否则无法暂存：\n" + "\n".join(st.session_state['current_errors']))

                st.markdown(f"#### 🚀 当前实时总分: **{live_total_score}** / 100 分")

                st.markdown(f"### {stage_type}评分标准")
                
                # --- 文本框定义 ---
                for key in criteria_keys:
                    max_val = rubric_map[key]['max']
                    display_num = display_map[key]
                    
                    # 禁用输入框
                    st.text_input(
                        label=f"{display_num}. {rubric_map[key]['name']} (最高 {max_val} 分)",
                        value=st.session_state['live_scores'].get(key, ""), 
                        key=f"text_input_{key}",
                        help=rubric_map[key]['tips'],
                        disabled=project_is_locked # <-- 项目级锁定
                    )
                    st.caption(rubric_map[key]['desc'])
                
                # --- 暂存表单 ---
                with st.form("grading_form"):
                    st.markdown("---")
                    
                    if project_is_locked:
                         submit_disabled = True
                         st.markdown("该项目已最终提交，**暂存按钮已被锁定**。")
                    else:
                         submit_disabled = False
                         st.markdown("点击 **暂存评分** 按钮，保存当前有效的输入分数，以便后续修改。")

                    # 专家暂存操作
                    if st.form_submit_button("💾 暂存评分", disabled=submit_disabled):
                        
                        # 再次检查是否有错误
                        if st.session_state['current_errors']:
                            st.error("暂存失败：请先修正上面的所有输入错误。")
                            st.stop()
                            
                        # 如果没有错误，保存到 explicit_drafts (st.session_state['draft_votes'])
                        vote_record = {
                            "Project Name": selected_project_name,
                            "Stage": stage_type,
                            "Expert": current_user_name,
                            "Research": valid_scores['Research'],
                            "Tech": valid_scores['Tech'],
                            "Deliverables": valid_scores['Deliverables'],
                            "Output": valid_scores['Output'],
                            "Budget": valid_scores['Budget'],
                            "Total": live_total_score, 
                            "Time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        
                        st.session_state['draft_votes'][current_user_name][selected_project_name] = vote_record
                        st.session_state['show_success'] = f"项目 **{selected_project_name}** 评分已暂存！总分：{live_total_score}"
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