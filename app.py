import streamlit as st
import pandas as pd
from datetime import datetime

# --- 配置部分 ---
ADMIN_PASSWORD = "admin"  # 管理员密码
EXPERT_PASSWORD = "123"   # 专家密码

# --- 初始化 Session State (模拟数据库) ---
if 'projects' not in st.session_state:
    st.session_state['projects'] = [] # 存储项目列表
if 'votes' not in st.session_state:
    st.session_state['votes'] = []    # 存储打分记录
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None # 当前登录角色

# --- 评分标准定义 (基于上传文档) ---
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

# --- 界面逻辑 ---

st.set_page_config(page_title="大飞机研究院项目评审系统", layout="wide")
st.title("✈️ 大飞机研究院项目评审打分系统")

# 1. 登录侧边栏
with st.sidebar:
    st.header("登录")
    role = st.radio("选择角色", ["专家", "管理员"])
    pwd = st.text_input("请输入密码", type="password")
    
    if st.button("登录"):
        if role == "管理员" and pwd == ADMIN_PASSWORD:
            st.session_state['logged_in_user'] = "admin"
            st.success("管理员登录成功")
        elif role == "专家" and pwd == EXPERT_PASSWORD:
            st.session_state['logged_in_user'] = "expert"
            st.success("专家登录成功")
        else:
            st.error("密码错误")

    if st.button("退出登录"):
        st.session_state['logged_in_user'] = None
        st.experimental_rerun()

# 2. 主要功能区
user_type = st.session_state['logged_in_user']

if user_type == "admin":
    st.header("🔧 管理员控制台")
    
    # 添加项目
    with st.expander("➕ 添加新项目", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        new_name = c1.text_input("项目名称")
        new_applicant = c2.text_input("申请人 (如: 张三/李四)")
        new_stage = c3.selectbox("评审阶段", ["中期", "结题"])
        new_time = c4.number_input("汇报时长(分)", value=30)
        
        if st.button("添加项目"):
            if new_name:
                st.session_state['projects'].append({
                    "name": new_name,
                    "applicant": new_applicant,
                    "stage": new_stage,
                    "time": new_time,
                    "id": len(st.session_state['projects']) + 1
                })
                st.success(f"项目 {new_name} 添加成功！")
            else:
                st.warning("请输入项目名称")

    # 查看汇总
    st.divider()
    st.subheader("📊 打分汇总")
    if st.session_state['votes']:
        df = pd.DataFrame(st.session_state['votes'])
        # 计算总分
        df['Total'] = df[['Research', 'Tech', 'Deliverables', 'Output', 'Budget']].sum(axis=1)
        st.dataframe(df, use_container_width=True)
        
        # 简单统计
        st.caption("平均分统计：")
        avg_scores = df.groupby("Project Name")['Total'].mean().reset_index()
        st.dataframe(avg_scores)
    else:
        st.info("暂无专家打分数据。")

    # 查看项目列表
    st.subheader("项目列表")
    if st.session_state['projects']:
        st.table(pd.DataFrame(st.session_state['projects']))

elif user_type == "expert":
    st.header("📝 专家评审界面")
    
    if not st.session_state['projects']:
        st.warning("管理员暂未发布评审项目。")
    else:
        # 选择项目
        project_names = [f"{p['name']} ({p['stage']})" for p in st.session_state['projects']]
        selected_option = st.selectbox("请选择要评审的项目", project_names)
        
        # 获取选中的项目数据
        selected_index = project_names.index(selected_option)
        project_data = st.session_state['projects'][selected_index]
        stage_type = project_data['stage'] # "中期" 或 "结题"
        
        st.info(f"正在评审：**{project_data['name']}** | 申请人：{project_data['applicant']} | 阶段：**{stage_type}**")
        
        # 加载对应的评分标准
        rubric = CRITERIA[stage_type]
        
        with st.form("grading_form"):
            st.markdown(f"### {stage_type}检查评分标准")
            
            # 1. 研究目标
            st.markdown(f"**1. {rubric['research']['name']}**")
            st.caption(f"要求：{rubric['research']['desc']}")
            s1 = st.slider("打分", 0, rubric['research']['max'], 15, key="s1", help=rubric['research']['tips'])
            
            # 2. 技术指标
            st.markdown(f"**2. {rubric['tech']['name']}**")
            st.caption(f"要求：{rubric['tech']['desc']}")
            s2 = st.slider("打分", 0, rubric['tech']['max'], 24, key="s2", help=rubric['tech']['tips'])
            
            # 3. 交付物
            st.markdown(f"**3. {rubric['deliverables']['name']}**")
            st.caption(f"要求：{rubric['deliverables']['desc']}")
            s3 = st.slider("打分", 0, rubric['deliverables']['max'], 15, key="s3", help=rubric['deliverables']['tips'])
            
            # 4. 成果产出
            st.markdown(f"**4. {rubric['output']['name']}**")
            st.caption(f"要求：{rubric['output']['desc']}")
            s4 = st.slider("打分", 0, rubric['output']['max'], 15, key="s4", help=rubric['output']['tips'])
            
            # 5. 经费
            st.markdown(f"**5. {rubric['budget']['name']}**")
            st.caption(f"要求：{rubric['budget']['desc']}")
            s5 = st.slider("打分", 0, rubric['budget']['max'], 8, key="s5", help=rubric['budget']['tips'])
            
            expert_name = st.text_input("专家姓名 (可选)")
            
            submitted = st.form_submit_button("提交评分")
            
            if submitted:
                # 记录分数
                vote_record = {
                    "Project Name": project_data['name'],
                    "Stage": stage_type,
                    "Expert": expert_name if expert_name else "Anonymous",
                    "Research": s1,
                    "Tech": s2,
                    "Deliverables": s3,
                    "Output": s4,
                    "Budget": s5,
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state['votes'].append(vote_record)
                st.success("评分提交成功！请选择下一个项目或通知管理员。")

else:
    st.info("👈 请在左侧侧边栏输入密码登录。")