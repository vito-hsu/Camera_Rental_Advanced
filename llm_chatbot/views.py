# llm_chatbot/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import ollama
from ollama import Client # 導入 Client 類別
import os # 導入 os 模組用於路徑操作
from decouple import config

# --- Ollama 配置 ---
OLLAMA_HOST = config('OLLAMA_HOST', default='http://localhost:11434')
OLLAMA_MODEL = 'llama3.2' # 沿用上次設定的模型名稱

# 初始化 Ollama 客戶端實例，這個實例會被所有請求重複使用
ollama_client = Client(host=OLLAMA_HOST)

# --- 載入上下文資訊 ---
# 獲取當前 views.py 檔案所在的目錄路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 構建到 'data' 資料夾的完整路徑
CONTEXT_DIR = os.path.join(BASE_DIR, 'data')

rental_regulations_content = ""
about_us_content = ""

try:
    # 讀取租賃規章內容
    with open(os.path.join(CONTEXT_DIR, 'rental_regulations.txt'), 'r', encoding='utf-8') as f:
        rental_regulations_content = f.read()
    # 讀取關於我們內容
    with open(os.path.join(CONTEXT_DIR, 'about_us.txt'), 'r', encoding='utf-8') as f:
        about_us_content = f.read()
    print("上下文資訊已成功載入。") # 成功載入的提示
except FileNotFoundError as e:
    print(f"警告：上下文文件未找到！請確保 'data' 目錄及 'rental_regulations.txt' 和 'about_us.txt' 文件存在於 {CONTEXT_DIR}。錯誤：{e}")
    # 在此處可以考慮提供一個預設的簡單上下文，或讓程式知道缺乏這些資訊
    rental_regulations_content = "未載入租賃規章資訊。"
    about_us_content = "未載入關於我們資訊。"
except Exception as e:
    print(f"讀取上下文文件時發生未知錯誤：{e}")
    rental_regulations_content = "載入租賃規章時發生錯誤。"
    about_us_content = "載入關於我們時發生錯誤。"


# --- 建構初始的系統提示 (System Prompt) ---
# 這個提示會被傳送給 LLM，告訴它自己的角色、背景資訊和行為準則
SYSTEM_PROMPT = f"""
您是一位專業、友善且細心的 AI 助理。
您的主要職責是針對本租賃店的**租賃業務、器材資訊、服務範圍**等相關問題提供**準確且基於提供的資訊**的回覆。
以下是本租賃店的相關背景資訊和營運細節，請您以此為基礎進行所有回覆：

--- 租賃規章 ---
{rental_regulations_content}

--- 關於我們 (店鋪介紹) ---
{about_us_content}

--- 您的回覆原則 (非常重要) ---
1.  **角色明確：** 您是租賃器材店的AI助理，請以第一人稱「我」或「我們店」來稱呼自己。
2.  **專注業務：** 僅回答與業務直接相關的問題，例如器材租賃流程、價格、規章、營業時間、聯絡方式、店鋪服務範圍等。
3.  **基於事實：** 回覆的內容必須完全基於您所知道的「租賃規章」和「關於我們」提供的資訊。
4.  **不確定或超出業務範圍：** 如果問題超出您的知識範圍或不在業務範疇內，請禮貌地告知使用者您無法回答。   
5.  **友善專業：** 保持禮貌、耐心和專業的語氣。
6.  **簡潔明瞭：** 在確保資訊完整性的前提下，盡量提供簡潔明瞭的回答。
"""

# --- 聊天視圖 ---
def chat_view(request):
    """
    渲染 LLM 聊天介面頁面。
    """
    return render(request, 'llm_chatbot/llm_chat.html')

@csrf_exempt
@require_POST
def llm_api_view(request):
    """
    處理來自前端的 LLM 查詢請求並返回 Ollama 模型的回覆。
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                return JsonResponse({'error': 'No message provided'}, status=400)

            try:
                # 將系統提示作為對話的第一個訊息發送給模型
                messages = [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_message}
                ]
                
                # 您可以考慮在這裡加入對話歷史，以實現更連貫的對話
                # 例如：messages.extend(get_conversation_history(session_id))
                # 但這需要額外的會話管理和數據庫儲存來實現

                response = ollama_client.chat(
                    model=OLLAMA_MODEL,
                    messages=messages,
                    options={'num_predict': 200, 'temperature': 0.7}, # 可選參數
                )
                response_content = response['message']['content']

            except Exception as e:
                response_content = f"抱歉，與 Ollama 服務連接或模型生成時發生錯誤：{e}"
                print(f"Ollama Error: {e}") # 打印錯誤以便調試
                return JsonResponse({'error': response_content}, status=500) # 返回 500 錯誤

            return JsonResponse({'response': response_content})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400) # 無效的 JSON 格式
        except Exception as e:
            print(f"General API Error: {e}")
            return JsonResponse({'error': f"服務器內部錯誤: {e}"}, status=500) # 通用服務器錯誤

    return JsonResponse({'error': 'Invalid request method'}, status=405) # 方法不允許