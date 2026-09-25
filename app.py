import streamlit as st
import requests

# 1. 获取云端秘密钥匙
api_key = st.secrets["DEEPSEEK_API_KEY"]
url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": "Bearer " + api_key,
    "Content-Type": "application/json"
}

st.title("液压工程师AI助手")
st.caption("专注液压选型、故障排查与系统设计")

with st.sidebar:
    st.header("控制面板")
    role = st.selectbox(
        "选择AI的角色：",
        ["液压系统选型助手", "液压故障排查助手", "液压系统设计顾问"]
    )
    st.divider()
    if st.button("清空聊天记录"):
        st.session_state.messages = [
            {"role": "system", "content": "你是一个" + role}
        ]
        st.rerun()

if role == "液压系统选型助手":
    system_prompt = "你是一个资深的液压系统工程师，专注于液压元件的选型。回答时必须根据用户提供的工况条件（压力、流量、温度等）推荐合适的泵、阀、缸。必须列出选型计算公式，不确定的参数必须提问，绝不能胡编乱造。"
elif role == "液压故障排查助手":
    system_prompt = "你是一个资深的液压故障诊断专家。用户描述故障现象时，请按照‘原因分析-排查步骤-解决方案’的框架回答。遇到可能涉及安全的问题，必须提醒用户先泄压断电。"
else:
    system_prompt = "你是一个精通液压系统设计的专家。负责解答液压回路设计、计算（如液压缸推力、管路流速、热平衡）等问题。回答必须列出详细的计算公式和步骤，切勿直接给结果。"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

user_input = st.chat_input("请输入你的问题：")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    data = {
        "model": "deepseek-chat",
        "messages": st.session_state.messages
    }

    try:
        with st.spinner("AI正在思考中，请稍等..."):
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # 探照灯：如果状态码不对，直接显示服务器返回的原始文本
            if response.status_code != 200:
                st.error(f"服务器返回错误码 {response.status_code}，详情：{response.text}")
                st.stop()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    except requests.exceptions.Timeout:
        st.error("网络超时了，请检查你的网络连接，或者稍后再试。")
    except requests.exceptions.ConnectionError:
        st.error("连接失败，请检查你的网络是否正常。")
    except Exception as e:
        st.error(f"AI 开小差了：{str(e)}")
