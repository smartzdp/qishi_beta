import base64
import time
import uuid
import logging
from pathlib import Path
from time import sleep
from playwright.sync_api import sync_playwright
from CaptchaServiceClass import CaptchaService
import random
import math

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 路径配置
TARGET_URL = "https://www.tiktok.com/@contractorswholesale?is_from_webapp=1&sender_device=pc"
BASE_DIR = Path("tiktok_dump")
INNER_DIR = BASE_DIR / "inner_images"
OUTER_DIR = BASE_DIR / "outer_images"
ROTATED_DIR = BASE_DIR / "rotated"
for d in [INNER_DIR, OUTER_DIR, ROTATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# 🎯 高拟真轨迹生成器
def generate_track(distance: int, total_time: int = 800):
    """生成 (x偏移, y偏移, 延迟ms) 的滑动轨迹"""

    def ease_out_expo(x):
        return 1 - pow(2, -10 * x)

    # 增加随机性
    overshoot = random.randint(8, 15)
    target = distance + overshoot
    steps = 50 + random.randint(10, 20)  # 增加步数
    last_x = 0
    points = []

    # 初始停顿
    points.append((0, 0, random.randint(100, 200)))

    # 主要滑动轨迹
    for i in range(steps):
        t = i / steps
        eased = ease_out_expo(t)
        x = int(eased * target)
        delta = x - last_x
        last_x = x

        # 增加随机的垂直偏移
        y = random.randint(-3, 3)

        # 随机延迟，模拟人类操作
        if random.random() < 0.1:  # 10%概率出现停顿
            delay = random.randint(50, 150)
        else:
            delay = total_time // steps + random.randint(-10, 10)

        points.append((x, y, delay))

    # 接近目标时的微调
    for i in range(3):
        x = target - random.randint(1, 3)
        y = random.randint(-1, 1)
        delay = random.randint(30, 80)
        points.append((x, y, delay))

    # 最终回退
    for i in range(3):
        x = target - int((overshoot * (i + 1)) / 3)
        y = random.randint(-1, 1)
        delay = random.randint(20, 50)
        points.append((x, y, delay))

    return points


# ✅ 核心处理器
class TikTokCaptchaHandler:
    def __init__(self):
        self.handled_blobs = set()
        self.blob_pair = []
        self.captcha_service = CaptchaService(token="sqZ6nY13O9-sCycnDza4lNA2WvV2OLhDaCmGwoqDryc")

    def handle_blob_image(self, resp, page):
        if "blob:https://www.tiktok.com/" not in resp.url or resp.url in self.handled_blobs:
            return
        self.handled_blobs.add(resp.url)
        logger.info(f"🎯 捕获 blob 图像：{resp.url}")

        try:
            base64_data = page.evaluate(f"""
                async () => {{
                    const blob = await fetch("{resp.url}").then(r => r.blob());
                    const reader = new FileReader();
                    return await new Promise(resolve => {{
                        reader.onloadend = () => resolve(reader.result.split(",")[1]);
                        reader.readAsDataURL(blob);
                    }});
                }}
            """)
            png_bytes = base64.b64decode(base64_data)
            self.blob_pair.append({"data": png_bytes, "size": len(png_bytes)})

            if len(self.blob_pair) == 2:
                return self._process_pair()
        except Exception as e:
            logger.error(f"❌ blob 处理失败: {e}", exc_info=True)

    def _process_pair(self):
        inner, outer = sorted(self.blob_pair, key=lambda x: x["size"])
        uid = uuid.uuid4().hex
        inner_path = INNER_DIR / f"inner_{uid}.png"
        outer_path = OUTER_DIR / f"outer_{uid}.png"

        with open(inner_path, "wb") as f:
            f.write(inner["data"])
        with open(outer_path, "wb") as f:
            f.write(outer["data"])

        logger.info(f"✅ inner 保存: {inner_path}")
        logger.info(f"✅ outer 保存: {outer_path}")

        result = self.captcha_service.verify_captcha("90004", str(outer_path), str(inner_path))
        if result.get("msg") == "识别成功":
            data = result["data"]["data"]
            slide_px = data["slide_px"]
            rotate_angle = data["rotate_angle"]
            logger.info(f"🧠 slide_px = {slide_px}, rotate_angle = {rotate_angle}")

            self.blob_pair.clear()
            return {"slide_px": slide_px}
        else:
            logger.warning(f"⚠️ 验证码识别失败：{result}")
            self.blob_pair.clear()
            return None


# ✅ 主执行函数
def run(headless=True):
    start = time.time()
    logger.info("🚀 启动 TikTok 拖动验证码破解器")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            locale='en-SG',
            timezone_id='Asia/Singapore',
            geolocation={"longitude": 103.8198, "latitude": 1.3521},  # 新加坡经纬度
            permissions=["geolocation"]
        )

        page = context.new_page()
        handler = TikTokCaptchaHandler()
        result_holder = {}

        def capture_response(resp):
            res = handler.handle_blob_image(resp, page)
            if res:
                result_holder.update(res)

        def capture_item_list(resp):
            if "api/post/item_list" in resp.url and resp.status == 200:
                try:
                    json_data = resp.json()
                    logger.info(f"📦 接收到 item_list 响应：{resp.url}")
                    logger.info(f"🧾 数据预览: {json_data.get('itemList', [])[:2]}")
                except Exception as e:
                    logger.warning(f"⚠️ 无法解析 item_list JSON：{e}")

        page.on("response", capture_response)
        page.on("response", capture_item_list)

        try:
            page.goto(TARGET_URL, timeout=30000)
            sleep(10000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            logger.info("⏳ 等待滑块出现...")
            slide_button = page.wait_for_selector("#captcha_slide_button", timeout=10000)
            if slide_button:
                print('找到滑块了')
            box = slide_button.bounding_box()
            logger.info(f"📦 滑块坐标：{box}")

            # ✅ 验证码重试循环逻辑
            max_attempts = 5
            attempts = 0
            slide_px = None
            success = False

            while attempts < max_attempts and not success:
                logger.info(f"🔁 第 {attempts + 1} 次尝试识别验证码...")

                # 等待新的验证码加载
                page.wait_for_timeout(3000)

                # 检查是否有新的验证码识别结果
                if result_holder.get("slide_px"):
                    slide_px = result_holder.get("slide_px")
                    logger.info(f"🎯 识别成功，开始滑动 {slide_px}px...")

                    start_x = box["x"]  # x轴 按钮左上角距离浏览器左上角的距离
                    start_y = box["y"] + box["height"] / 2
                    track = generate_track(slide_px)  # 生成轨迹，slide_px为第三方提供的移动距离

                    # ✅ 执行缓动轨迹滑动
                    page.mouse.move(start_x, start_y)
                    page.mouse.down()
                    for dx, dy, delay in track:
                        page.mouse.move(start_x + dx, start_y + dy)
                        sleep(delay / 1000)
                    page.mouse.up()
                    logger.info("✅ 滑动完成")

                    # 等待验证结果
                    page.wait_for_timeout(2000)

                    # 检查是否验证成功
                    if not page.query_selector("#captcha_slide_button"):
                        logger.info("🎉 验证成功！")
                        success = True
                        break
                    else:
                        logger.warning("⚠️ 验证失败，准备重试...")
                        # 清空之前的结果
                        result_holder.clear()
                        # 等待新的验证码加载
                        page.wait_for_timeout(2000)

                attempts += 1

            if not success:
                logger.error("❌ 连续多次验证失败，退出！")
                return

            # ✅ 等待 item_list 接口响应
            logger.info("⌛ 等待 item_list 接口响应...")
            page.wait_for_timeout(5000)

        except Exception as e:
            logger.error(f"❌ 页面流程错误: {e}", exc_info=True)
        finally:
            context.close()
            browser.close()

    logger.info(f"🏁 结束，总耗时 {time.time() - start:.2f}s")


if __name__ == "__main__":
    run(headless=False)
