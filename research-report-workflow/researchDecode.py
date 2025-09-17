
import os
import requests
from datetime import datetime, timedelta
import subprocess
import time
import json
import http.client
from urllib.parse import quote_plus

def get_token(base_url, username, password):
    # 解析 base_url 为 IP 地址和端口
    host, port = base_url.split(":")
    port = int(port)  # 将端口转换为整数

    # 创建 HTTP 连接
    conn = http.client.HTTPConnection(host, port)

    # 设置请求路径和请求体
    path = "/token"
    payload = f"username={username}&password={password}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"  # 表单数据的 MIME 类型
    }

    try:
        # 发送 POST 请求
        conn.request("POST", path, body=payload, headers=headers)
        response = conn.getresponse()

        # 检查响应状态码
        if response.status == 200:
            response_data = response.read().decode("utf-8")
            token_data = json.loads(response_data)
            return token_data.get("access_token")
        else:
            print(f"Failed to get token: {response.status} - {response.reason}")
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        conn.close()  # 关闭连接


# 判断行业文件夹是否在DomainClassification一级键值中,合格则创建此行业向量库
def create_vector_store(researchPath, ragAPIUrl,DomainClassification):
    ragAPIUrlCheck = ragAPIUrl + '/check_vector_store'
    ragAPIUrlCreate = ragAPIUrl + '/creat_vector_store'

    # 遍历researchPath下的子文件夹
    for folder_name in os.listdir(researchPath):
        folder_path = os.path.join(researchPath, folder_name)
        
        # 判断是否为有效行业
        if os.path.isdir(folder_path) and folder_name in DomainClassification:
            # 准备数据
            data = {
                "file_path": folder_path,
                "vector_store_name": DomainClassification[folder_name]["english"]
            }
            
            # 请求API先检查是否存在行业向量库,不存在则创建行业向量库
            try:
                response = requests.post(ragAPIUrlCheck, params=data)
                response.raise_for_status()  # 检查请求是否成功
                status = response.json().get("message", {}).get("statu")
                if status== "success":
                    print(f"已存在此行业向量库,{DomainClassification[folder_name]['english']}")
                else:
                    print(f"不已存在此行业向量库将创建它,{DomainClassification[folder_name]['english']}")
                    response = requests.post(ragAPIUrlCreate, params=data)
                    response.raise_for_status()  # 检查请求是否成功
                    print(f"成功创建向量库: {DomainClassification[folder_name]['english']}，响应: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"请求失败: {e}")

def check_task_status(task_id,ragAPIUrl,file_path,file_name,folder_name):
    ragAPIEmbeddingResult = f'{ragAPIUrl}/get_task_status'
    while True:
        try:
            response = requests.get(ragAPIEmbeddingResult, params={"task_id": task_id})
            response.raise_for_status()  # 检查请求是否成功
            status_info = response.json()  # 解析 JSON 响应

            print(status_info)

            if status_info["statu"] == "success":
                if save_to_database(file_path, file_name, folder_name):
                    print('保存记录成功')
                else:
                    print('保存记录失败')
                break

            elif status_info["statu"] == "error":
                print("处理出错:", status_info["description"])
                break

            print('等待10秒后再次查询')
            time.sleep(10)

        except requests.exceptions.RequestException as e:
            print("请求出错:", e)  # 捕获请求相关的异常
            break

        except ValueError as e:
            print("JSON 解析出错:", e)  # 捕获 JSON 解析相关的异常

        except Exception as e:
            print("发生未知错误:", e)  # 捕获其他未知异常


def save_to_database(file_path,file_name,folder_name):
    data = {
        "results":[{ "file_path": file_path, "file_name": file_name, "OCR_status":1,'type':folder_name}]
    }
    response = requests.post("http://192.168.3.123:51500/api/addResearchOCRResult", json =data)
    if response.json().get("status") == 1:
        return True
    else:
        print(response.json().get("message"))
        return False

def is_file_processed(file_name):
    params = {"file_name": file_name}
    response = requests.get("http://192.168.3.123:51500/api/getOCRStatus",params=params)
    if response.json().get("status") == 1:
        return True
    else:
        print(response.json().get("message"))
        return False


def process_files(researchPath,DomainClassification,filePath,ragAPIUrl,datas=10):
    # 获取当前日期10天前的日期
    ten_days_ago = datetime.now() - timedelta(days=datas)
    # 遍历researchPath文件夹
    for folder_name in os.listdir(researchPath):
        folder_path = os.path.join(researchPath, folder_name)
        # 判断是否为有效行业
        if os.path.isdir(folder_path) and folder_name in DomainClassification:
            print('处理文件夹：',folder_name)
            count = 0
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                print('处理文件：',file_path)
                # 检查是否为 PDF 文件
                if file_name.endswith('.pdf') and os.path.isfile(file_path):
                    # 获取文件的创建日期、访问日期和修改日期
                    file_create_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    file_access_time = datetime.fromtimestamp(os.path.getatime(file_path))
                    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                    # 检查任意一个日期是否在10天内
                    if (file_create_time >= ten_days_ago or
                            file_access_time >= ten_days_ago or
                            file_mod_time >= ten_days_ago):
                        if count == 10:
                            break
                        if is_file_processed(file_name):
                            print(f'已处理过！{file_name}')
                            break
                        print('文件满足条件开始处理：', file_path)
                        # 使用scp命令传输文件
                        print(f'{file_name}此文件并没有向量化')
                        scp_command = f"scp {file_path} spoce@192.168.3.249:{filePath}"
                        result = subprocess.run(scp_command, shell=True)
                        if result.returncode == 0:
                            # 组装数据并调用API进行向量化处理
                            data = {
                                "file_path": f"/home/spoce/temp/{file_name}",
                                "vector_store_name": DomainClassification[folder_name]["english"]
                            }
                            print(data)
                            ragAPIEmbedding = f'{ragAPIUrl}/embedding'
                            response = requests.post(ragAPIEmbedding, params=data)
                            print(response.text)
                            task_id = response.json().get("message")

                            # 等待1分钟后查询任务状态
                            time.sleep(10)
                            check_task_status(task_id,ragAPIUrl,file_path,file_name,folder_name)
                            count += 1

def delete_vector_store(base_url, domain_classification):
    # 解析 base_url 为 IP 地址和端口
    host, port = base_url.split(":")
    port = int(port)  # 将端口转换为整数
    # 创建 HTTP 连接
    conn = http.client.HTTPConnection(host, port)
    # 设置请求路径和请求体
    payload = ''
    headers = {}
    for key in domain_classification:
        print('删除向量库：',key)
        encoded_value = quote_plus(str(domain_classification[key]["english"]))

        path = f"/delete_vector_store?vector_store_name={encoded_value}"
        conn.request("POST",path,
                 payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        print(f'删除向量库：{domain_classification[key]["english"]}')
        time.sleep(1)

if __name__ == "__main__":
    domain_classification = {
    "内容运营": {"industry_id": 51, "包含": ["内容运营", "抖音运营", "小红书运营", "TikTok运营", "社群运营", "直播运营", "新媒体运营", "电商运营", "抖音电商", "视频号运营", "快手运营", "本地生活运营", "快手", "B站", "微博", "知乎", "跨境电商"], "english": "content_operation"},
    "人工智能": {"industry_id": 18, "包含": ["人工智能", "AIGC", "AI大模型", "数字人", "AIGC专题", "AI智算专题"], "english": "artificial_intelligence"},
    "新能源": {"industry_id": 19, "包含": ["新能源", "储能", "光伏", "氢能源", "充电桩"], "english": "new_energy"},
    "智能制造": {"industry_id": 20, "包含": ["智能智造", "机器人", "自动驾驶", "Robotax行业", "Robotax行业报告"], "english": "intelligent_manufacturing"},
    "互联网技术": {"industry_id": 21, "包含": ["web3.0", "云计算", "边缘计算行业", "数字化"], "english": "internet_technology"},
    "大数据": {"industry_id": 22, "包含": ["大数据", "数据要素"], "english": "big_data"},
    "集成电路": {"industry_id": 23, "包含": ["集成电路和微电子", "存储行业", "光模块行业", "光刻机行业", "存储行业报告", "光模块行业报告"], "english": "integrated_circuit"},
    "量子技术": {"industry_id": 24, "包含": ["量子信息技术"], "english": "quantum_technology"},
    "虚拟现实": {"industry_id": 25, "包含": ["增强现实/虚拟现实", "3D行业"], "english": "virtual_reality"},
    "区块链": {"industry_id": 26, "包含": ["区块链技术", "区块链行业"], "english": "blockchain"},
    "物联网": {"industry_id": 27, "包含": ["物联网", "智能手表", "数字孪生"], "english": "internet_of_things"},
    "显示技术": {"industry_id": 28, "包含": ["新型显示技术"], "english": "display_technology"},
    "软件开发": {"industry_id": 29, "包含": ["高端软件", "信创"], "english": "software_development"},
    "网络安全": {"industry_id": 30, "包含": ["网络安全"], "english": "network_security"},
    "航空航天": {"industry_id": 31, "包含": ["航天航空电子", "低空经济"], "english": "aerospace"},
    "健康医疗": {"industry_id": 32, "包含": ["健康", "医美", "口腔护理", "生命科学", "睡眠行业"], "english": "health_care"},
    "消费品": {"industry_id": 33, "包含": ["内衣行业", "食品行业", "咖啡行业", "奢侈品", "白酒", "母婴", "化妆品行业"], "english": "consumer_goods"},
    "文化娱乐": {"industry_id": 34, "包含": ["电影行业", "游戏", "短剧"], "english": "culture_entertainment"},
    "经济金融": {"industry_id": 35, "包含": ["经济", "保险行业", "三中全会"], "english": "economy_finance"},
    "运动户外": {"industry_id": 36, "包含": ["户外运动行业", "体育", "户外运动行业报告"], "english": "sports_outdoors"},
    "婚恋服务": {"industry_id": 37, "包含": ["婚姻+恋爱"], "english": "marriage_love_service"},
    "餐饮服务": {"industry_id": 38, "包含": ["餐饮", "茶饮"], "english": "catering_service"},
    "农业科技": {"industry_id": 39, "包含": ["数字乡村", "智慧农业解决方案", "农业行业", "乡村振兴"], "english": "agricultural_technology"},
    "企业管理": {"industry_id": 40, "包含": ["企业管理", "营销", "薪酬"], "english": "enterprise_management"},
    "经营方案": {"industry_id": 41, "包含": ["开业活动策划方案", "七夕方案", "中秋节方案", "运营方案", "运营合同"], "english": "business_plan"},
    "教育培训": {"industry_id": 42, "包含": ["教培", "AI+教育行业"], "english": "education_training"},
    "房地产": {"industry_id": 43, "包含": ["房地产", "家装行业"], "english": "real_estate"},
    "能源电力": {"industry_id": 44, "包含": ["电力行业"], "english": "energy_electricity"},
    "制造业": {"industry_id": 45, "包含": ["钢铁行业", "专精特新"], "english": "manufacturing"},
    "宠物服务": {"industry_id": 46, "包含": ["宠物行业"], "english": "pet_service"},
    "旅游业": {"industry_id": 47, "包含": ["旅游业"], "english": "tourism"},
    "广告业": {"industry_id": 48, "包含": ["广告"], "english": "advertising_industry"},
    "移动应用": {"industry_id": 49, "包含": ["移动应用"], "english": "mobile_app"},
    "其他": {"industry_id": 50, "包含": ["其它", "技术"], "english": "other"}
    }
    ragAPIUrl = 'http://192.168.3.249:51510'
    researchPath = '/srv/dev-disk-by-uuid-a63d7a76-8dbc-464a-a44b-6147edb1be39/study/research_reports/'
    sever_base_url = "122.51.236.10:51500"
    locae_base_url = "192.168.3.249:51510"
    fileTempPath= '/home/spoce/temp'
    username = 'spoce'
    password = '4G#8dL2!pQ9z'
    token = get_token(sever_base_url,username,password)
    create_vector_store(researchPath, ragAPIUrl,domain_classification) #创建行业向量库，根据文件夹对应的英文创建
    datas = 10 #10天内的文件
    process_files(researchPath,domain_classification,fileTempPath,ragAPIUrl,datas)
    #delete_vector_store(locae_base_url, domain_classification)
