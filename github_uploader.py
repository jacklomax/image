import sys
import base64
import hashlib
import datetime
import requests
import urllib.parse
import os

def main():
    # ========== 在这里填写你的GitHub配置 ==========
    # 重要：从环境变量读取Token，避免泄露
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        sys.exit(1)
        
    owner = 'jacklomax'  # 你的GitHub用户名
    repo = 'image'       # 你的GitHub仓库名
    branch = 'dontdeploy'      # 你的分支名，GitHub默认主分支是 'main'
    message = 'upload image from typora'
    # ===========================================

    param = [urllib.parse.unquote(par, 'utf8') for par in sys.argv]
    param.pop(0)

    md_filename = ''
    image_paths = []

    if len(param) > 0:
        if not os.path.exists(param[0]):
            md_filename = param[0]
            param.pop(0)
        image_paths = param

    for image_path in image_paths:
        with open(image_path, "rb") as f:
            content = base64.b64encode(f.read())

            file_ext = os.path.splitext(image_path)[-1]
            file_hash = hashlib.md5(content).hexdigest()
            new_filename = file_hash + file_ext

            today = str(datetime.date.today())
            remote_path = f'typora/{today}/{new_filename}'

            # ========== 【修改开始】新增文件检查逻辑 ==========
            api_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{remote_path}'
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # 第一步：尝试获取已存在文件的信息，以获取 sha
            existing_file_sha = None
            try:
                check_response = requests.get(api_url, headers=headers, params={'ref': branch}, timeout=10)
                if check_response.status_code == 200:
                    # 文件已存在，获取其 sha
                    existing_file_sha = check_response.json().get('sha')
            except Exception as e:
                # 如果检查失败，当作文件不存在处理，继续尝试上传
                pass

            # 第二步：准备上传数据，如果文件存在则加入 sha
            data = {
                'message': message,
                'branch': branch,
                'content': content.decode('utf-8')  # base64编码的字符串
            }
            if existing_file_sha:
                data['sha'] = existing_file_sha  # 加入 sha 以执行更新操作

            # 第三步：执行上传（创建或更新）
            try:
                response = requests.put(api_url, headers=headers, json=data, timeout=30)
                resp_json = response.json()

                if response.status_code in [201, 200]:
                    # ========== 【关键修改4】：生成jsDelivr CDN链接 ==========
                    # 上传成功后，生成用于加速访问的jsDelivr链接
                    image_url = f'https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{remote_path}'
                    print(image_url)
                else:
                    # 更详细的错误信息
                    error_msg = resp_json.get('message', f'HTTP {response.status_code}')
                    print(f'Error: Upload failed - {error_msg}')
                    # 打印调试信息（调试时可取消注释）
                    # print(f'Debug: API URL: {api_url}')
                    # print(f'Debug: Response: {resp_json}')
                    
            except Exception as e:
                print(f'Error: Network or API error - {str(e)}')

if __name__ == '__main__':
    main()
