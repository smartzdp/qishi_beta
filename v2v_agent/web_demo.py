import json
import os.path
import tempfile
import sys
import re
import uuid
import requests
from argparse import ArgumentParser
import gradio as gr
import torch
import torchaudio
from transformers import WhisperFeatureExtractor, AutoTokenizer

# Import our new API backend
from api_backend_v2 import ModelWorker

# Global variables
glm_tokenizer = None
api_worker = None
whisper_model, feature_extractor = None, None

def initialize_fn():
    global api_worker, feature_extractor, whisper_model, glm_tokenizer
    
    if api_worker is not None:
        return
    
    # Initialize API worker
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        raise gr.Error("请设置GLM_API_KEY环境变量")
    
    api_worker = ModelWorker(api_key)
    
    # Initialize tokenizer for text processing
    try:
        glm_tokenizer = AutoTokenizer.from_pretrained("THUDM/glm-4-voice-tokenizer", trust_remote_code=True)
    except Exception as e:
        print(f"Warning: Could not load tokenizer: {e}")
        glm_tokenizer = None
    
    # Initialize Whisper for audio processing (if needed)
    try:
        feature_extractor = WhisperFeatureExtractor.from_pretrained("openai/whisper-base")
    except Exception as e:
        print(f"Warning: Could not load Whisper feature extractor: {e}")
        feature_extractor = None

def inference_fn(
    user_input,
    history,
    input_mode,
    audio_path,
    **kwargs
):
    global api_worker, glm_tokenizer
    
    if api_worker is None:
        initialize_fn()
    
    try:
        # 统一处理音频和文本输入
        if input_mode == "audio":
            assert audio_path is not None
            input_type = "audio"
            input_content = audio_path
        else:
            input_type = "text"
            input_content = user_input
        
        # 用户输入已经在user函数中添加了，这里不需要重复添加
        
        # 使用统一聊天接口
        audio_status = "正在处理..."
        
        for result in api_worker.unified_chat_stream(input_type, input_content):
            if result["type"] == "unified":
                # 统一响应：同时包含文本和音频
                response_text = result.get("text")
                audio_response_path = result.get("audio_path")
                
                # 构建回复内容
                reply_content = ""
                if response_text:
                    reply_content += response_text
                if audio_response_path:
                    if reply_content:
                        reply_content += f"\n\n[音频回复: {audio_response_path}]"
                    else:
                        reply_content = f"[音频回复: {audio_response_path}]"
                
                # 添加到历史
                history.append({"role": "assistant", "content": reply_content})
                
                # 更新状态
                if audio_response_path and response_text:
                    audio_status = "音频和文本生成完成"
                elif audio_response_path:
                    audio_status = "音频生成完成"
                elif response_text:
                    audio_status = "文本回复"
                else:
                    audio_status = "无有效回复"
                
                yield history, "", audio_status, audio_response_path, audio_response_path
                return
                
            elif result["type"] == "error":
                audio_status = f"错误: {result['message']}"
                history.append({"role": "assistant", "content": f"错误: {result['message']}"})
                yield history, "", audio_status, None, None
                return
        
        # 如果没有收到任何响应
        audio_status = "无响应"
        history.append({"role": "assistant", "content": "抱歉，我没有收到任何回复。"})
        yield history, "", audio_status, None, None
        
    except Exception as e:
        print(f"Error in inference: {e}")
        import traceback
        traceback.print_exc()
        audio_status = f"错误: {str(e)}"
        history.append({"role": "assistant", "content": f"错误: {str(e)}"})
        yield history, "", audio_status, None, None

def create_interface():
    with gr.Blocks(title="GLM-4-Voice API Demo") as demo:
        gr.Markdown("# GLM-4-Voice API Demo")
        gr.Markdown("支持语音和文本输入，AI会同时生成文本和音频回复")
        
        # 移除顶部清除按钮，将移到发送按钮右边
        
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    value=[],
                    elem_id="chatbot",
                    height=400,
                    show_copy_button=True,
                    type="messages"
                )
                
                with gr.Row():
                    with gr.Column(scale=4):
                        msg = gr.Textbox(
                            placeholder="输入文本...",
                            show_label=False,
                            scale=4,
                            container=False,
                        )
                    with gr.Column(scale=1, min_width=40):
                        send_btn = gr.Button("发送", variant="primary", scale=1)
                    with gr.Column(scale=1, min_width=40):
                        clear_btn = gr.Button("清除", variant="secondary", scale=1)
                
                # 底部控制区域：左侧输入控制，右侧音频播放
                with gr.Row():
                    # 左侧：输入控制
                    with gr.Column(scale=1):
                        input_mode = gr.Radio(
                            choices=["text", "audio"],
                            value="text",
                            label="输入模式",
                        )
                        
                        audio_path = gr.Audio(
                            label="上传音频",
                            type="filepath",
                            visible=True,
                        )
                    
                    # 右侧：音频播放
                    with gr.Column(scale=1):
                        
                        # 实时音频播放（流式）
                        output_audio = gr.Audio(
                            label="♫ 实时音频播放",
                            streaming=True,
                            autoplay=True,
                            show_download_button=False,
                            visible=True
                        )
                        
                        # 完整音频播放
                        complete_audio = gr.Audio(
                            label="完整音频输出",
                            show_download_button=True,
                            visible=True
                        )
                        
                        # 音频状态显示
                        audio_status = gr.Textbox(
                            label="音频状态",
                            value="等待音频生成...",
                            interactive=False
                        )
        
        # Event handlers
        def update_audio_visibility(mode):
            return gr.update(visible=(mode == "audio"))
        
        input_mode.change(
            update_audio_visibility,
            inputs=[input_mode],
            outputs=[audio_path]
        )
        
        def user(user_message, history, input_mode, audio_path):
            if input_mode == "audio" and audio_path is not None:
                return "", history + [{"role": "user", "content": f"[音频: {audio_path}]"}]
            elif input_mode == "text" and user_message:
                return "", history + [{"role": "user", "content": user_message}]
            else:
                return user_message, history
        
        def bot(history, input_mode, audio_path):
            if not history:
                return history, "", "等待输入...", None, None
            
            last_message = history[-1]
            if isinstance(last_message["content"], str) and last_message["content"].startswith("[音频转录]"):
                # Extract text from audio transcription
                user_input = last_message["content"].replace("[音频转录] ", "")
                # 在音频模式下，保持audio_path不变
            else:
                user_input = last_message["content"]
                # 在文本模式下，audio_path应该为None
                if input_mode == "text":
                    audio_path = None
            
            for history, msg, audio_status, output_audio, complete_audio in inference_fn(
                user_input, history, input_mode, audio_path
            ):
                yield history, msg, audio_status, output_audio, complete_audio
        
        send_btn.click(
            user,
            inputs=[msg, chatbot, input_mode, audio_path],
            outputs=[msg, chatbot],
            queue=False
        ).then(
            bot,
            inputs=[chatbot, input_mode, audio_path],
            outputs=[chatbot, msg, audio_status, output_audio, complete_audio]
        )
        
        msg.submit(
            user,
            inputs=[msg, chatbot, input_mode, audio_path],
            outputs=[msg, chatbot],
            queue=False
        ).then(
            bot,
            inputs=[chatbot, input_mode, audio_path],
            outputs=[chatbot, msg, audio_status, output_audio, complete_audio]
        )
        
        def clear_conversation():
            """清空对话历史"""
            return [], "", "对话历史已清空", None, None
        
        clear_btn.click(clear_conversation, outputs=[chatbot, msg, audio_status, output_audio, complete_audio])
    
    return demo

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8889)
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv("GLM_API_KEY"):
        print("错误: 请设置GLM_API_KEY环境变量")
        print("示例: export GLM_API_KEY='your-api-key-here'")
        exit(1)
    
    # Create and launch interface
    demo = create_interface()
    demo.launch(
        server_port=args.port,
        server_name=args.host
    )
