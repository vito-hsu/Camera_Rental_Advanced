# llm_chatbot/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import ollama # 導入 ollama 庫
import os
from decouple import config # 如果您使用 python-decouple

# 您可以在 settings.py 中定義 LLM_MODEL 或直接在這裡寫死
# 建議將 Ollama 服務地址設定為環境變數，以防您在其他機器上運行
# 例如在 .env 中增加：OLLAMA_HOST=http://localhost:11434
# 如果您是本地運行，Ollama 的默認地址通常是 http://localhost:11434，可以不用特別設置
OLLAMA_HOST = config('OLLAMA_HOST', default='http://localhost:11434') # 從環境變數讀取或使用默認值
OLLAMA_MODEL = 'llama3' # 您下載的模型名稱，例如 'llama3', 'mixtral', 'gemma' 等

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

            # --- 調用 Ollama 服務的核心邏輯 ---
            try:
                # 使用 ollama.chat() 進行對話模式
                # 如果是第一次運行或模型沒有在運行，可能會有啟動延遲
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[{'role': 'user', 'content': user_message}],
                    options={'num_predict': 200, 'temperature': 0.7}, # 可選參數，如生成 token 數和隨機性
                    host=OLLAMA_HOST # 指定 Ollama 服務的地址
                )
                response_content = response['message']['content']

            except Exception as e:
                response_content = f"抱歉，與 Ollama 服務連接或模型生成時發生錯誤：{e}"
                print(f"Ollama Error: {e}") # 打印錯誤以便調試

            return JsonResponse({'response': response_content})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)