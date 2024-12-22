import gradio as gr
import requests
import threading
import uvicorn

from XcelBot.xbot_api import app


def gradio_interface(message, file):
    files = None if file is None else {'file': (file.name, file)}
    response = requests.post("http://localhost:8000/chat", data={"message": message}, files=files)
    return response.json()["reply"]


# 创建 Gradio UI
# 添加自定义样式
# demo.add_static_files("static", "static")
css = """
    #chatbox {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #ccc;
        padding: 10px;
        border-radius: 5px;
    }
    #message_input {
        width: 100%;
        margin-right: 10px;
        height: 60px; /* 调整为单行高度 */
    }
    #file_input {
        height: 60px; /* 调整为单行高度 */
        margin-right: 10px;
    }
    #send_button {
        display: flex;
        align-items: center;
        background-color: #28a745;
        color: white;
        border: none;
        padding: 5px 10px; /* 高度减少一半 */
        border-radius: 5px;
        height: 60px; /* 调整为单行高度 */
    }
    #send_button::after {
        content: url('https://img.icons8.com/?size=30&id=0prg0S64vdOO&format=png&color=000000');
        margin-left: 10px;
    }
    .gr-chatbot-message {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .gr-chatbot-message.user {
        justify-content: flex-end;
    }
    .gr-chatbot-message.bot {
        justify-content: flex-start;
    }
    .gr-chatbot-message.user::before {
        content: "User: ";
        margin-right: 5px;
        font-weight: bold;
    }
    .gr-chatbot-message.bot::before {
        width: 30px;
        height: 30px;
        display: inline-block; /* 确保图标作为块元素显示 */
        content: url('https://img.icons8.com/emoji/48/000000/robot-emoji.png');
        margin-right: 5px;
    }
"""
with gr.Blocks(css=css) as demo:
    gr.Markdown("# Chat Interface with File Upload")

    with gr.Row():
        chatbox = gr.Chatbot(label="Chat History", elem_id="chatbox")

    with gr.Row():
        message_input = gr.Textbox(show_label=False, placeholder="Type your message here...", lines=1,
                                   elem_id="message_input", scale=7)
        file_input = gr.File(show_label=False, elem_id="file_input", scale=2)
        submit_button = gr.Button("Send", elem_id="send_button", scale=1)


    def submit_message(message, file, chat_history):
        reply = gradio_interface(message, file)
        chat_history.append((message, reply))
        return chat_history


    submit_button.click(submit_message, inputs=[message_input, file_input, chatbox], outputs=chatbox)


# 运行 Gradio 和 FastAPI
def run_app():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    threading.Thread(target=run_app).start()
    demo.launch()