# pip install jupyter_client
# pip install ipykernel
from jupyter_client.manager import start_new_kernel
import logging

logger = logging.getLogger(f'2brain.{__name__}')


def run_code(code, client):
    """执行代码并获取输出结果"""
    try:
        # 发送代码执行请求
        client.execute(code)

        # 设置超时时间
        TIMEOUT = 30

        # 获取输出结果
        output = []
        while True:
            try:
                msg = client.get_iopub_msg(timeout=TIMEOUT)
                msg_type = msg['header']['msg_type']
                content = msg['content']

                if msg_type == 'stream':
                    output.append(content['text'])
                elif msg_type == 'execute_result':
                    if 'text/plain' in content.get('data', {}):
                        output.append(content['data']['text/plain'])
                elif msg_type == 'error':
                    return "ERROR:\n" + '\n'.join(content['traceback'])
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    break

            except Exception as e:
                logging.error(f"获取输出时发生错误: {str(e)}")
                break

        return '\n'.join(output) if output else "No output"

    except Exception as e:
        logging.error(f"代码执行发生错误: {str(e)}")
        return f"Exception occurred: {str(e)}"


def model_execute_main(command):
    """主函数:创建内核、执行代码并清理资源"""
    kernel_manager = None
    client = None

    try:
        # 创建新内核
        kernel_manager, client = start_new_kernel()
        logging.info(f"正在执行代码: {command}")

        # 执行代码并获取结果
        result = run_code(command, client)
        return result

    except Exception as e:
        logging.error(f"执行过程发生错误: {str(e)}")
        return f"Execution failed: {str(e)}"

    finally:
        # 清理资源
        if client:
            try:
                client.stop_channels()
            except Exception as e:
                logging.error(f"停止通道时发生错误: {str(e)}")

        if kernel_manager:
            try:
                kernel_manager.shutdown_kernel()
            except Exception as e:
                logging.error(f"关闭内核时发生错误: {str(e)}")

        del client
        del kernel_manager


if __name__ == "__main__":
    # 测试代码
    test_code = '''
import math
print("pi =", round(math.pi, 2))
'''
    res = model_execute_main(test_code)
    print(res)