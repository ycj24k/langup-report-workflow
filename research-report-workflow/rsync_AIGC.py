import os
import http.client
import time
import json
import requests
from urllib.parse import quote  # 导入 quote 方法


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


def report_pdf(base_url, token):
    conn = http.client.HTTPConnection(base_url)
    file_name = "虎啸：2024年虎啸年度洞察报告——3C家电行业.pdf"
    encoded_file_name = quote(file_name)  # 对 file_name 进行 URL 编码

    headers = {
        'Content-Type': 'application/json',
        "Authorization": f'Bearer {token}'
    }

    # 使用编码后的 file_name
    conn.request("POST", f"/report?file_name={encoded_file_name}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    conn.close()

if __name__ == '__main__':
    milvus_path = "/home/spoce/rag/Langup/Server/pickles"
    locale_base_url =  "192.168.3.249:51510"
    sever_base_url = "122.51.236.10:51500"
    username = 'spoce'
    password = '4G#8dL2!pQ9z'
    token = get_token(sever_base_url,username,password)
    #token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcG9jZSIsImV4cCI6MTczNzMzMDI2OH0.N3ByLA4Af2Xt6f0hKkBArnig662-JUvkJ7BOdXjz9-M'
    if token:
        print('Token:', token)
    else:
        print('Failed to get token')
    #backup_milvus(milvus_path, locale_base_url)
    report_pdf(sever_base_url,token)

