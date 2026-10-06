import glob
import os
import re
import sys
import pandas as pd


# ==========================================
# 🛠️ 輔助函式：清理不合法檔名字元與提取英文
# ==========================================
def sanitize_filename(filename):
  """替換掉 Windows 檔案系統不允許的非法字元"""
  return re.sub(r'[\\/*?:"<>|]', '_', filename).strip()


def get_english_company_and_name(company_raw, name_raw):
  """從 Excel 讀取的文字中分離出英文公司名與英文姓名"""
  # 1. 提取英文姓名（遇到第一個中文即停止）
  name_str = str(name_raw) if pd.notna(name_raw) else 'Unknown'
  name_match = re.split(r'[\u4e00-\u9fa5]', name_str)
  eng_name = name_match[0].strip() if name_match else name_str.strip()

  # 2. 提取英文公司名（遇到第一個中文即停止）
  comp_str = str(company_raw) if pd.notna(company_raw) else ''
  company_match = re.split(r'[\u4e00-\u9fa5]', comp_str)
  eng_company = (
      company_match[0].strip() if company_match[0].strip() else comp_str.strip()
  )

  # 若公司或姓名提取後為空值，補上備用字串
  if not eng_company:
    eng_company = comp_str if comp_str else 'Company'
  if not eng_name:
    eng_name = 'Unknown'

  return eng_company, eng_name


# ==========================================
# 🚀 主執行邏輯 run()
# ==========================================
def run():
  if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
  else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

  excel_path = os.path.join(base_dir, 'cards_result.xlsx')
  image_dir = os.path.join(base_dir, 'combined')

  if not os.path.exists(excel_path):
    print(f'❌ 錯誤：找不到 Excel 檔案：{excel_path}')
    input('\n按 Enter 鍵回到主選單...')
    return

  # 讀取 Excel 檔案
  try:
    df = pd.read_excel(excel_path)
  except Exception as e:
    print(f'❌ 讀取 Excel 失敗：{e}')
    input('\n按 Enter 鍵回到主選單...')
    return

  # 取得圖片列表
  image_paths = sorted(
      glob.glob(os.path.join(image_dir, '*.jpg'))
      + glob.glob(os.path.join(image_dir, '*.jpeg'))
      + glob.glob(os.path.join(image_dir, '*.png'))
  )

  if not image_paths:
    print(f'❌ 錯誤：在 {image_dir} 中找不到任何圖片！')
    input('\n按 Enter 鍵回到主選單...')
    return

  if len(df) != len(image_paths):
    print(
        f'⚠️ 警告：Excel 資料筆數 ({len(df)} 筆) 與圖片數量'
        f' ({len(image_paths)} 張) 不一致，將按順序盡量比對。'
    )

  records = df.to_dict('records')

  print('=' * 50)
  print('開始直接從 Excel 讀取資料並對圖片重新命名...')
  print('=' * 50)

  rename_count = 0
  for idx, img_path in enumerate(image_paths):
    if idx < len(records):
      comp_raw = records[idx].get('Company', '')
      name_raw = records[idx].get('Name', '')

      eng_company, eng_name = get_english_company_and_name(comp_raw, name_raw)

      # 組合新檔名：英文公司名 - 英文姓名
      new_filename_base = sanitize_filename(f'{eng_company} - {eng_name}')

      ext = os.path.splitext(img_path)[1]
      new_filepath = os.path.join(image_dir, f'{new_filename_base}{ext}')

      # 避免檔名重複 (自動補 _1, _2...)
      counter = 1
      while os.path.exists(new_filepath) and new_filepath != img_path:
        new_filepath = os.path.join(
            image_dir, f'{new_filename_base}_{counter}{ext}'
        )
        counter += 1

      if img_path != new_filepath:
        os.rename(img_path, new_filepath)
        rename_count += 1
        print(
            f'✅ [{idx+1}/{len(image_paths)}] {os.path.basename(img_path)}  ➡️ '
            f' {os.path.basename(new_filepath)}'
        )
      else:
        print(
            f'ℹ️ [{idx+1}/{len(image_paths)}]'
            f' 檔名無變更：{os.path.basename(img_path)}'
        )

  print(f'\n🎉 完成！共成功重新命名 {rename_count} 個圖片檔案！')
  input('\n按 Enter 鍵回到主選單...')


if __name__ == '__main__':
  run()