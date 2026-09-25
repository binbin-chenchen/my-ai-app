import streamlit as st
import requests

# 1. 基础配置
api_key = ""  
url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": "Bearer " + api_key,
    "Content-Type": "application/json"
}

# 2. 页面标题和说明
st.title("我的AI应用")
st.caption("基于 Streamlit 和 DeepSeek 构建")

# 3. 侧边栏控制面板
with st.sidebar:
    st.header("控制面板")
    role = st.selectbox(
        "选择AI的角色：",
        ["耐心的英语老师", "小红书文案专家", "犀利的面试官"]
    )
    st.divider()
    if st.button("清空聊天记录"):
        st.session_state.messages = [
            {"role": "system", "content": "你是一个" + role}
        ]
        st.rerun()

# 4. 根据用户选的，设定系统提示词
if role == "耐心的英语老师":
    system_prompt = "你是一个耐心的英语老师，每次我说中文，你都翻译成英文，并解释重点单词。"
elif role == "小红书文案专家":
    system_prompt = "你是一个小红书爆款文案专家，说话活泼，每次都要给我3个标题和一段正文。"
else:
    system_prompt = "你是一个互联网大厂的面试官，问问题很犀利，每次只问一个问题，等我回答后再继续。"

# 5. 初始化聊天记忆
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]

# 6. 显示聊天记录
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 7. 聊天输入框
user_input = st.chat_input("请输入你的问题：")

# 8. 处理用户输入
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    data = {
        "model": "deepseek-chat",
        "messages": st.session_state.messages
    }

    # 这里开始是今天新加的重点：错误处理
    try:
        with st.spinner("AI正在思考中，请稍等..."):
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            # 如果状态码不是200，抛出异常
            if response.status_code != 200:
                error_msg = result.get("error", {}).get("message", "未知错误")
                raise Exception(f"API返回错误({response.status_code}): {error_msg}")

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
