import streamlit as st

from chat import get_graph
import tempfile

st.title("Chat Bot")
st.caption("A simple chat bot")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    with st.spinner("Loading PDF..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())  # Simpan konten file
            tmp_file_path = tmp_file.name 

            graph = get_graph(tmp_file_path)
            st.session_state['graph'] = graph 
            st.session_state['messages'] = [{"role": "assistant", "content": "Hello! How can I help you today?"}]
            st.success("PDF loaded successfully")

if "messages" not in st.session_state:
    st.session_state['messages'] = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

if "graph" in st.session_state:
    for msg in st.session_state['messages']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    user_input = st.chat_input("Ask me anything")

    if user_input:
        st.session_state['messages'].append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        
        with st.chat_message('assistant'):
            full_response = ""
            response_container = st.empty()

            input_stream = {
                "question": user_input,
            }
            response = graph.invoke(input_stream)
            full_response += response.get("answer", "")
            response_container.markdown(full_response)

            st.session_state['messages'].append({"role": "assistant", "content": full_response})
else:
    st.info("Please upload a PDF file to start the chat bot.")