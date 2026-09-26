import streamlit as st
import pandas as pd
import requests

# 本地测试用的 API Key，替换成你自己的真实 Key
try:
    api_key = st.secrets["DEEPSEEK_API_key"] 
except:
    api_key = ""
    url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer " + api_key,
    "Content-Type": "application/json"
}

st.title("超长臂设计助手（万能表头版）")
st.caption("兼容不同格式的Excel，用户可手动指定列名")

# 1. 侧边栏
with st.sidebar:
    st.header("第一步：导入数据")
    uploaded_file = st.file_uploader("上传你的Excel参数表", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.success("表格读取成功！")
        
        # 新增：获取所有列名
        all_columns = df.columns.tolist()
        
        st.header("第二步：指定列名")
        # 让用户自己选，哪一列是“吨位”，哪一列是“臂长”
        tonnage_col = st.selectbox("请选择【吨位】对应的列：", all_columns)
        arm_col = st.selectbox("请选择【臂长】对应的列：", all_columns)
        
        # 基于用户选择的列，提取选项
        tonnage_options = df[tonnage_col].unique().tolist()
        arm_length_options = df[arm_col].unique().tolist()
        
        st.header("第三步：选择设计参数")
        selected_tonnage = st.selectbox("选择挖机吨位：", tonnage_options)
        selected_arm_length = st.selectbox("选择目标臂长：", arm_length_options)
        
        generate_btn = st.button("🚀 生成设计方案")
    else:
        df = None
        generate_btn = False
        st.info("请先上传Excel文件")

# 2. 主页面逻辑
if generate_btn and df is not None:
    with st.chat_message("user"):
        st.markdown(f"我需要：**{selected_tonnage}** 挖机，**{selected_arm_length}** 臂长")
    
    # 3. 查表（使用用户指定的列名）
    # 注意：这里 df[tonnage_col] 就是动态列名
    filtered_data = df[(df[tonnage_col] == selected_tonnage) & (df[arm_col] == selected_arm_length)]
    
    if not filtered_data.empty:
        matched_row = filtered_data.iloc[0]
        real_data_str = matched_row.to_string()
        
        st.write("✅ 已在本地库找到匹配参数：")
        st.dataframe(filtered_data)
        
        # 4. 发给 AI 生成报告
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
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            with st.spinner("AI 正在撰写正式设计报告..."):
                response = requests.post(url, headers=headers, json=data, timeout=60)
                
                if response.status_code != 200:
                    st.error(f"API 报错 {response.status_code}：{response.text}")
                    st.stop()
                    
                result = response.json()
                report_text = result["choices"][0]["message"]["content"]
            
            with st.chat_message("assistant"):
                st.markdown(report_text)
            
            # 下载按钮
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
