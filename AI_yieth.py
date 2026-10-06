import glob
import io
import os
import sys
import pandas as pd
import pyperclip
from google import genai
from google.genai import types
from PIL import Image


def run():
  # ==========================================
  # 1. 安全取得當前目錄 (相容 .py 與 PyInstaller .exe)
  # ==========================================
  if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
  else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

  # ==========================================
  # 2. 設定相對路徑 (皆位於同一個資料夾下)
  # ==========================================
  api_key_path = os.path.join(base_dir, 'api_key.txt')
  image_dir = os.path.join(base_dir, 'combined')
  output_excel_path = os.path.join(base_dir, 'cards_result.xlsx')

  # 從 api_key.txt 讀取 API Key
  try:
    with open(api_key_path, 'r', encoding='utf-8') as f:
      GEMINI_API_KEY = f.read().strip()
    if not GEMINI_API_KEY:
      raise ValueError('api_key.txt 檔案內容為空！')
  except FileNotFoundError:
    print(f'❌ 錯誤：找不到 API Key 檔案，請確認檔案是否存在於：{api_key_path}')
    input('\n按 Enter 鍵回到主選單...')
    return
  except Exception as e:
    print(f'❌ 讀取 API Key 時發生錯誤：{e}')
    input('\n按 Enter 鍵回到主選單...')
    return

  # 初始化 Client
  client = genai.Client(api_key=GEMINI_API_KEY)

  # ==========================================
  # 3. Prompt 規則 (含多號碼提取規則)
  # ==========================================
  prompt_rules = """【严格输出格式】：
1. 提取所有名片中的信息，生成结构化数据。
2. 表头必须严格按照以下顺序：Company, Name, blank1, blank2, Job Title, Department, Email, Direct Line, Mobile Phone, Company phone, Fax, Address

【人名（Name）专有处理规则（重要）】：
1. **如果有中英文名字**：按【英文在前，中文在后】排列，中間用空格隔開（如：Maria 陳靜堃 / Sean Pey 曾憲沛）。
2. **如果只有中文名字，没有英文名字**：**必须**为该中文名字翻译/生成对应的英文拼音或英文名，并放在中文前面（如：原名“蔡鳳儀” -> 输出 “Choi Fung Yee 蔡鳳儀” 或 “Christina 蔡鳳儀”）。
3. **如果只有英文名字，没有中文名字**：**只需保留英文名字即可**，绝对不要强行翻译或添加中文名字（如：原名“John Smith” -> 直接输出 “John Smith”）。

【其他字段的原文忠实度与禁止自动翻译原则】：
1. **除 Name 字段外，其他所有字段绝对禁止自动翻译**：名片上原有什么语言就输出什么语言，绝对不要把中文自动翻译成英文，也不要把英文翻译成中文！
2. **单语言处理规则**：如果名片上某个字段（如公司、职位、地址）只有中文，就只输出中文；如果只有英文，就只输出英文。
3. **双语混排规则（仅当名片上原本同时存在中英文时适用）**：
   - 只有当名片原文中**同时印有**英文和中文时，才遵循【英文在前，中文在后】的顺序，中间用空格隔开。
   - 示例（卡片上有双语）：Apple Inc 苹果公司
   - 示例（卡片上只有中文）：香港交易所（绝对不要自行翻译成 Hong Kong Exchanges）
4. **禁止使用括号**：绝对不能使用任何括号（如圆括号 ()、方括号 []、花括号 {} 等）来包裹中文或英文，除非卡片原文内本身就印有括号。
5. 如果名片中没有提供某个字段，则该单元格请保持空白，绝对不要虚构，也不要写“无”。
6. blank1 和 blank2 两列必须完全留空（直接填入空格或保持空白）。

【电话号码格式化规则（适用于所有电话类字段：Direct Line, Mobile Phone, Company phone, Fax）】：
1. **香港号码转换**：
   - 识别特征：名片地址在香港、有“香港”字样，或者号码为 8 位数（如 23456789、91234567 等）。
   - 格式要求：统一转换为 **+852 XXXX XXXX**（加号、国家码852、空格、前4位数字、空格、后4位数字）。
   - 示例：原号码 9123 4567 或 (852)91234567 -> 转换为 +852 9123 4567

2. **大陆号码转换**：
   - 识别特征：名片地址在大陆、有中国省市字样，或者手机为 11 位数（以 13/14/15/16/17/18/19 开头），固定电话带大陆区号（如 021、010）。
   - 格式要求：
     - 大陆手机（11位）：统一转换为 **+86 XXX XXXX XXXX**
     - 大陆固定电话（带区号，如 010）：去首位0，统一转换为 **+86 區號 XXXX XXXX**（如 010-88888888 -> +86 10 8888 8888）

3. **其他号码**：如果不属于香港或大陆号码，则保留其原始数字。
4. **注意**：去除号码中多余的横杠（-）、括号、非必要的国家码前缀（如 0086），严格按照上述带空格的规范输出。
5. **多号码处理规则（重要）**：
   - 如果同一个字段（如 Mobile Phone、Direct Line、Company phone、Fax）包含两个或多个号码（例如：同时印有香港手机和内地手机）：
   - **必须将所有号码一并提取**，每个号码分别按上述格式化规则转换后，中间用斜线及空格 ` / ` 隔開。
   - 示例（同时有香港及内地手机）：原卡片印有 HK: 91234567 / CN: 13800138000 -> 输出 `+852 9123 4567 / +86 138 00138 000`

【输出限制】：
不要输出任何前言、后语、寒暄、解释或 Markdown 代码块以外的文字，只需要返回这一个 Markdown 表格。"""

  # ==========================================
  # 4. 獲取 combined 資料夾內的所有圖片
  # ==========================================
  image_paths = sorted(
      glob.glob(os.path.join(image_dir, '*.jpg'))
      + glob.glob(os.path.join(image_dir, '*.jpeg'))
      + glob.glob(os.path.join(image_dir, '*.png'))
  )

  if not image_paths:
    print(f'❌ 錯誤：在 {image_dir} 中找不到任何圖片檔！')
    input('\n按 Enter 鍵回到主選單...')
    return

  print(f'找到 {len(image_paths)} 張名片，準備載入圖片並傳送至 Gemini API...')

  images = [Image.open(p) for p in image_paths]

  # ==========================================
  # 5. 定義 JSON Schema 結構
  # ==========================================
  response_schema = {
      'type': 'ARRAY',
      'items': {
          'type': 'OBJECT',
          'properties': {
              'Company': {'type': 'STRING'},
              'Name': {'type': 'STRING'},
              'blank1': {'type': 'STRING'},
              'blank2': {'type': 'STRING'},
              'Job Title': {'type': 'STRING'},
              'Department': {'type': 'STRING'},
              'Email': {'type': 'STRING'},
              'Direct Line': {'type': 'STRING'},
              'Mobile Phone': {'type': 'STRING'},
              'Company phone': {'type': 'STRING'},
              'Fax': {'type': 'STRING'},
              'Address': {'type': 'STRING'},
          },
          'required': [
              'Company',
              'Name',
              'blank1',
              'blank2',
              'Job Title',
              'Department',
              'Email',
              'Direct Line',
              'Mobile Phone',
              'Company phone',
              'Fax',
              'Address',
          ],
      },
  }

  contents = [prompt_rules] + images

  # ==========================================
  # 6. 執行辨識並匯出 (自動追加數據)
  # ==========================================
  try:
    print('正在呼叫 Gemini 進行結構化辨識...')

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=response_schema,
            temperature=0.0,
        ),
    )

    df_new = pd.read_json(io.StringIO(response.text))

    columns_order = [
        'Company',
        'Name',
        'blank1',
        'blank2',
        'Job Title',
        'Department',
        'Email',
        'Direct Line',
        'Mobile Phone',
        'Company phone',
        'Fax',
        'Address',
    ]
    df_new = df_new.reindex(columns=columns_order)

    # ------------------------------------------
    # 🔄 追加數據 (Append Mode)
    # ------------------------------------------
    if os.path.exists(output_excel_path):
      try:
        df_existing = pd.read_excel(output_excel_path)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        print(
            f'ℹ️ 檢測到已有 Excel 檔案，正在追加 {len(df_new)} 筆新資料（總共'
            f' {len(df_final)} 筆）...'
        )
      except Exception as read_err:
        print(f'⚠️ 讀取舊 Excel 失敗 ({read_err})，將建立新檔覆蓋。')
        df_final = df_new
    else:
      df_final = df_new

    # 儲存 Excel
    df_final.to_excel(output_excel_path, index=False)
    print(f'✅ 已成功更新 Excel 至：{output_excel_path}')

    # 轉為 HTML 表格並複製本次新增數據到剪貼簿
    html_table = df_new.to_html(index=False, na_rep='', border=1)
    pyperclip.copy(html_table)

    print('\n' + '=' * 40 + ' 本次識別結果 ' + '=' * 40)
    print(df_new.to_string(index=False))
    print('\n🎉 本次新增的表格已成功複製到剪貼簿！')
    print('👉 請開啟 Outlook 郵件內文，按下 "Ctrl + V" 貼上帶有框線的表格。')

  except Exception as e:
    print(f'❌ 呼叫 Gemini API 時發生錯誤：{e}')

  input('\n按 Enter 鍵回到主選單...')


if __name__ == '__main__':
  run()