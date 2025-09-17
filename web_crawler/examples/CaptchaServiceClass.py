# 验证码识别服务
import base64
import requests
import os
import logging

logger = logging.getLogger(f'{__name__}')


class CaptchaService:
    """验证码识别服务封装类"""

    def __init__(self, token: str, api_url: str = "http://hk.api.jfbym.com/api/YmServer/customApi"):
        self.token = token
        self.api_url = api_url
        self.headers = {"Content-Type": "application/json"}

    def encode_image(self, image_path: str):
        """将图片编码为base64字符串"""
        if not os.path.exists(image_path):
            logger.error(f"图片路径不存在: {image_path}")
            return None

        try:
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.error(f"图片编码失败: {str(e)}")
            return None

    def verify_captcha(self, captcha_type: str, image_path_1: str, image_path_2: str = None):
        """验证码识别，支持一张或两张图片"""
        logger.info(f'开始验证服务{image_path_1}-{image_path_2}')
        image_base64_1 = self.encode_image(image_path_1)
        if not image_base64_1:
            return {"success": False, "message": "图片1编码失败"}

        data = {
            "token": self.token,
            "type": captcha_type,
            "out_ring_image": image_base64_1
        }

        if image_path_2:
            image_base64_2 = self.encode_image(image_path_2)
            if not image_base64_2:
                return {"success": False, "message": "图片2编码失败"}
            data["inner_circle_image"] = image_base64_2

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            ).json()
            logger.info(f"验证码识别结果: {response}")
            return response
        except Exception as e:
            error_msg = f"验证码识别请求失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    def verify_captcha_single_slider(self, captcha_type: str, image_path_1: str): # 单滑块
        """验证码识别，支持一张或两张图片"""
        logger.info('开始验证服务')
        image_base64_1 = self.encode_image(image_path_1)
        if not image_base64_1:
            return {"success": False, "message": "图片1编码失败"}

        data = {
            "token": self.token,
            "type": captcha_type,
            "image": image_base64_1,
            "extra": True
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            ).json()
            logger.info(f"验证码识别结果: {response}")
            return response
        except Exception as e:
            error_msg = f"验证码识别请求失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}
if __name__ == '__main__':

    # 使用示例
    captcha_service = CaptchaService(token="sqZ6nY13O9-sCycnDza4lNA2WvV2OLhDaCmGwoqDryc")
    # 单图片验证码
    result = captcha_service.verify_captcha( "90004","images/out_range.jpg", 'images/inner_circle.jpg')
    # result = captcha_service.verify_captcha_single_slider( "22222","captcha_image.png")

    print(result)
    # {'msg': '识别成功', 'code': 10000, 'data': {'code': 0, 'data': {'rotate_angle': 114, 'slide_px': 88}, 'time': 0.20470881462097168, 'unique_code': '72ef4132c05f8d4b0044894f3cf3f3ee'}}