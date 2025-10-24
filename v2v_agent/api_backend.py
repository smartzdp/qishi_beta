import base64
import tempfile
import os
import wave
from typing import Optional, Dict, Any, Generator
from zhipuai import ZhipuAI

class GLM4VoiceAPI:
    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)
    
    def audio_to_base64(self, audio_path: str) -> str:
        """将音频文件转换为base64字符串"""
        try:
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            print(f"Error converting audio to base64: {e}")
            return ""
    
    def save_audio_as_wav(self, audio_data: bytes, filepath: str):
        """保存音频数据为WAV文件"""
        try:
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(44100)
                wav_file.writeframes(audio_data)
            print(f"Audio saved to {filepath}")
        except Exception as e:
            print(f"Error saving audio: {e}")
    
    def process_audio_input(self, audio_path: str) -> Optional[str]:
        """处理音频输入，返回文本（仅用于转录）"""
        try:
            # 将音频转换为base64
            audio_base64 = self.audio_to_base64(audio_path)
            if not audio_base64:
                return None
            
            # 调用GLM-4-voice API
            response = self.client.chat.completions.create(
                model="glm-4-voice",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_base64,
                                    "format": "wav"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024,
                stream=False
            )
            
            # 提取文本内容
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                return "抱歉，我无法理解您的音频内容。"
                
        except Exception as e:
            print(f"Error processing audio input: {e}")
            return f"音频处理错误: {str(e)}"
    
    def unified_chat(self, input_type: str, input_content: str) -> Dict[str, Any]:
        """统一的聊天接口，支持音频和文本输入，返回音频和文本"""
        try:
            # 准备消息内容
            if input_type == "audio":
                # 音频输入
                audio_base64 = self.audio_to_base64(input_content)
                if not audio_base64:
                    return {"error": "音频文件读取失败"}
                
                message_content = [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_base64,
                            "format": "wav"
                        }
                    }
                ]
            else:
                # 文本输入
                message_content = [
                    {
                        "type": "text",
                        "text": input_content
                    }
                ]
            
            # 调用GLM-4-voice API
            response = self.client.chat.completions.create(
                model="glm-4-voice",
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                max_tokens=1024,
                stream=False
            )
            
            # 处理响应
            result = {
                "text": None,
                "audio_path": None,
                "audio_id": None,
                "error": None
            }
            
            if response.choices and response.choices[0].message:
                message = response.choices[0].message
                
                # 提取文本内容
                if hasattr(message, 'content') and message.content:
                    result["text"] = message.content
                
                # 提取音频内容
                if hasattr(message, 'audio') and message.audio:
                    audio_data = message.audio['data']
                    decoded_data = base64.b64decode(audio_data)
                    
                    # 保存到临时文件
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                        tmp_file.write(decoded_data)
                        result["audio_path"] = tmp_file.name
                    
                    # 提取音频ID（如果存在）
                    if 'id' in message.audio:
                        result["audio_id"] = message.audio['id']
                
                # 如果既没有文本也没有音频，返回错误
                if not result["text"] and not result["audio_path"]:
                    result["error"] = "API未返回有效内容"
            else:
                result["error"] = "API调用失败"
            
            return result
                
        except Exception as e:
            print(f"Error in unified chat: {e}")
            return {"error": f"聊天错误: {str(e)}"}
    
    def generate_audio_response(self, text: str) -> Optional[str]:
        """根据文本生成音频响应"""
        try:
            response = self.client.chat.completions.create(
                model="glm-4-voice",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": text
                            }
                        ]
                    }
                ],
                max_tokens=1024,
                stream=False
            )
            
            # 检查是否有音频响应
            if response.choices and response.choices[0].message.audio:
                audio_data = response.choices[0].message.audio['data']
                decoded_data = base64.b64decode(audio_data)
                
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_file.write(decoded_data)
                    return tmp_file.name
            else:
                # 如果没有音频响应，返回None
                print("No audio response received from API")
                return None
                
        except Exception as e:
            print(f"Error generating audio response: {e}")
            return None
    
    def get_text_response(self, text: str) -> str:
        """获取文本响应"""
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=1024,
                temperature=0.7
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                return "抱歉，我无法理解您的问题。"
                
        except Exception as e:
            print(f"Error getting text response: {e}")
            return f"文本响应错误: {str(e)}"

class ModelWorker:
    def __init__(self, api_key: str):
        self.api_client = GLM4VoiceAPI(api_key)
    
    def generate_stream(self, prompt: str, max_new_tokens: int = 100, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """生成流式响应"""
        try:
            # 尝试生成音频响应
            audio_path = self.api_client.generate_audio_response(prompt)
            
            if audio_path:
                yield {
                    "type": "audio",
                    "data": audio_path,
                    "text": prompt
                }
            else:
                # 如果音频生成失败，尝试获取文本响应
                text_response = self.api_client.get_text_response(prompt)
                yield {
                    "type": "text",
                    "data": text_response
                }
                
        except Exception as e:
            yield {
                "type": "error",
                "message": f"生成错误: {str(e)}"
            }
    
    def unified_chat_stream(self, input_type: str, input_content: str) -> Generator[Dict[str, Any], None, None]:
        """统一的聊天流式响应"""
        try:
            # 调用统一聊天接口
            result = self.api_client.unified_chat(input_type, input_content)
            
            if result.get("error"):
                yield {
                    "type": "error",
                    "message": result["error"]
                }
            else:
                # 同时返回文本和音频
                yield {
                    "type": "unified",
                    "text": result.get("text"),
                    "audio_path": result.get("audio_path"),
                    "audio_id": result.get("audio_id")
                }
                
        except Exception as e:
            yield {
                "type": "error",
                "message": f"统一聊天错误: {str(e)}"
            }
    
    def process_audio(self, audio_path: str) -> Optional[str]:
        """处理音频文件"""
        return self.api_client.process_audio_input(audio_path)

# 测试函数
def test_api():
    """测试API功能"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        raise ValueError("请设置 GLM_API_KEY 环境变量")
    
    worker = ModelWorker(api_key)
    
    # 测试文本生成
    print("测试文本生成...")
    for result in worker.generate_stream("你好，请介绍一下你自己"):
        print(f"结果类型: {result['type']}")
        if result['type'] == 'audio':
            print(f"音频文件: {result['data']}")
        elif result['type'] == 'text':
            print(f"文本内容: {result['data']}")
        else:
            print(f"错误: {result['message']}")

if __name__ == "__main__":
    test_api()
