import streamlit as st
import pandas as pd
import requests

# =========================================================
# 1. 基础配置
# =========================================================
# 【本地测试】：把 api_key = "" 改成你的真实 Key，例如 api_key = "sk-xxxxxx"
# 【上传公网】：必须把 api_key 改回空字符串 ""，云端会自动读取 Secrets
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = "" # 本地测试在这里填真实 Key

url = "https://api.deepseek.com/v1/chat/completions"

# =========================================================
# 2. 页面标题
# =========================================================
st.title("超长臂设计助手（万能表头版）")
st.caption("兼容不同格式的Excel，支持一键演示数据")

# =========================================================
# 3. 初始化“储物柜” (Session State)
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.is_demo = False

# =========================================================
# 4. 侧边栏逻辑
# =========================================================
with st.sidebar:
    st.header("第一步：导入数据")
    
    # 4.1 模板下载
    try:
        with open("test_data_diff.xlsx", "rb") as file:
            st.download_button("📥 下载示例表格", data=file, file_name="示例参数表.xlsx")
    except FileNotFoundError:
        pass
        
    st.divider()
    
    # 4.2 上传文件
    uploaded_file = st.file_uploader("上传你的Excel参数表", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # 如果有上传文件，存入储物柜
        st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.is_demo = False
        st.success("表格读取成功！")
        
    # 4.3 没有文件时的演示按钮
    else:
        st.info("👋 没有Excel？点击下方按钮一键体验。")
        if st.button("🚀 使用演示数据体验"):
            demo_data = {
                "型号": ["20吨", "20吨", "30吨"],
                "长度": ["12米", "15米", "18米"],
                "容量": ["0.8方", "0.6方", "0.8方"],
                "缸径": ["110mm", "125mm", "140mm"],
                "配重": ["2吨", "3.5吨", "5吨"]
            }
            st.session_state.df = pd.DataFrame(demo_data)
            st.session_state.is_demo = True
            st.success("已加载演示数据！")

    # 4.4 只要储物柜里有数据，就显示下拉菜单和生成按钮
    if st.session_state.df is not None:
        df = st.session_state.df
        
        if st.session_state.is_demo:
            # 演示模式，直接固定列名
            tonnage_col = "型号"
            arm_col = "长度"
        else:
            # 上传模式，让用户选列名
            all_columns = df.columns.tolist()
            tonnage_col = st.selectbox("请选择【吨位】对应的列：", all_columns)
            arm_col = st.selectbox("请选择【臂长】对应的列：", all_columns)
            
        tonnage_options = df[tonnage_col].unique().tolist()
        arm_length_options = df[arm_col].unique().tolist()
        
        selected_tonnage = st.selectbox("选择挖机吨位：", tonnage_options)
        selected_arm_length = st.selectbox("选择目标臂长：", arm_length_options)
        
        generate_btn = st.button("🚀 生成设计方案")
    else:
        generate_btn = False

# =========================================================
# 5. 主逻辑区
# =========================================================
if generate_btn and st.session_state.df is not None:
    df = st.session_state.df
    
    with st.chat_message("user"):
        st.markdown(f"我需要：**{selected_tonnage}** 挖机，**{selected_arm_length}** 臂长")
    
    # 查表
    filtered_data = df[(df[tonnage_col] == selected_tonnage) & (df[arm_col] == selected_arm_length)]
    
    if not filtered_data.empty:
        matched_row = filtered_data.iloc[0]
        real_data_str = matched_row.to_string()
        
        st.write("✅ 已在本地库找到匹配参数：")
        st.dataframe(filtered_data)
        
        prompt = f"""
        用户需求：生成{selected_tonnage}，{selected_arm_length}的设计方案。
        以下是我们数据库中查询到的真实参考数据：
        {real_data_str}
        
        请根据以上真实数据，为用户生成一份专业的《挖掘机超长臂改造初步设计报告》。
        要求：
        1. 必须使用正式、严谨的工程报告格式。
        2. 必须分为以下几个章节：一、原机基本参数；二、结构尺寸参数；三、三大油缸匹配选型；四、配重与稳定性计算；五、结论与安全建议。
        3. 必须基于我提供的真实数据，不允许自己编造参数。
        """
        
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
        headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
        
        try:
            with st.spinner("AI 正在撰写正式设计报告，请稍等..."):
                response = requests.post(url, headers=headers, json=data, timeout=60)
                if response.status_code != 200:
                    st.error(f"API 报错 {response.status_code}：{response.text}")
                    st.stop()
                result = response.json()
                report_text = result["choices"][0]["message"]["content"]
            
            with st.chat_message("assistant"):
                st.markdown(report_text)
            
            st.divider()
            st.subheader("📥 报告导出")
            st.download_button(
                label="点击下载报告（.txt格式）",
                data=report_text,
                file_name=f"{selected_tonnage}_{selected_arm_length}_设计报告.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"AI 开小差了：{str(e)}")
    else:
        st.warning("❌ 本地库中没有找到完全匹配的数据。")
