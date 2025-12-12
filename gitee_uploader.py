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
    branch = 'main'      # 你的分支名，GitHub默认主分支是 'main'
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

            # ========== 【关键修改1】：使用GitHub上传API ==========
            # 正确API地址：上传到GitHub，而不是jsDelivr
            api_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{remote_path}'
            
            # ========== 【关键修改2】：使用正确的请求头和数据结构 ==========
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            data = {
                'message': message,
                'branch': branch,
                'content': content.decode('utf-8')  # base64编码的字符串
            }

            try:
                # ========== 【关键修改3】：使用PUT方法 ==========
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