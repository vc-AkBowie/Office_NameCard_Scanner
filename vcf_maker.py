import os
import sys
import pandas as pd


def run():
  # 動態取得當前資料夾路徑 (相容 PyInstaller 與 Python 腳本)
  if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
  else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

  # ==========================================
  # 1. 設定檔案路徑 (皆改為相對於 base_dir)
  # ==========================================
  input_file = os.path.join(base_dir, 'cards_result.xlsx')
  output_dir = os.path.join(base_dir, 'vcards_for_outlook')

  if not os.path.exists(input_file):
    print(f'❌ 錯誤：找不到 Excel 檔案：{input_file}')
    input('\n按 Enter 鍵回到主選單...')
    return

  os.makedirs(output_dir, exist_ok=True)

  # 讀取檔案 (.xlsx 或 .csv)
  try:
    if input_file.endswith('.csv'):
      df = pd.read_csv(input_file)
    else:
      df = pd.read_excel(input_file)
  except Exception as e:
    print(f'❌ 讀取檔案失敗：{e}')
    input('\n按 Enter 鍵回到主選單...')
    return

  # 填補空值 (NaN 轉為空字串)
  df = df.fillna('')

  # 定義標準欄位（其餘欄位會被自動放入 NOTE 備註）
  standard_fields = {
      'Company',
      'Name',
      'Job Title',
      'Department',
      'Email',
      'Direct Line',
      'Mobile Phone',
      'Company phone',
      'Fax',
      'Address',
      'Website',
  }

  count = 0

  # ==========================================
  # 2. 逐行讀取並為每位聯絡人生成獨立 VCF
  # ==========================================
  for index, row in df.iterrows():
    company = str(row.get('Company', '')).strip()
    name = str(row.get('Name', '')).strip()
    job_title = str(row.get('Job Title', '')).strip()
    department = str(row.get('Department', '')).strip()
    email = str(row.get('Email', '')).strip()
    direct_line = str(row.get('Direct Line', '')).strip()
    mobile_phone = str(row.get('Mobile Phone', '')).strip()
    company_phone = str(row.get('Company phone', '')).strip()
    fax = str(row.get('Fax', '')).strip()
    address = str(row.get('Address', '')).strip()
    website = str(row.get('Website', '')).strip()

    # 若無姓名也無公司名稱，跳過該行
    if not name and not company:
      continue

    vcard = ['BEGIN:VCARD', 'VERSION:3.0']

    # 1. 姓名 (FN 與 N)
    display_name = name if name else company
    vcard.append(f'FN;CHARSET=utf-8:{display_name}')
    vcard.append(f'N;CHARSET=utf-8:{display_name};;;;')

    # 2. 公司與部門 (ORG)
    if company or department:
      vcard.append(f'ORG;CHARSET=utf-8:{company};{department}')

    # 3. 職稱 (TITLE)
    if job_title:
      vcard.append(f'TITLE;CHARSET=utf-8:{job_title}')

    # 4. 電子郵件 (EMAIL)
    if email:
      vcard.append(f'EMAIL;TYPE=INTERNET,WORK:{email}')

    # 5. 電話號碼 (TEL)
    if mobile_phone:
      vcard.append(f'TEL;TYPE=CELL:{mobile_phone}')
    if direct_line:
      vcard.append(f'TEL;TYPE=WORK,DIR:{direct_line}')
    if company_phone:
      vcard.append(f'TEL;TYPE=WORK,VOICE:{company_phone}')
    if fax:
      vcard.append(f'TEL;TYPE=WORK,FAX:{fax}')

    # 6. 地址 (ADR)
    if address:
      vcard.append(f'ADR;TYPE=WORK;CHARSET=utf-8:;;{address};;;;')

    # 7. 網站 (URL)
    if website:
      vcard.append(f'URL:{website}')

    # 8. 動態處理自訂欄位 (Custom Fields -> NOTE & X- 欄位)
    custom_notes = []
    for col in df.columns:
      col_str = str(col).strip()
      val_str = str(row[col]).strip()

      if col_str not in standard_fields and val_str:
        custom_notes.append(f'{col_str}: {val_str}')
        clean_col_name = col_str.upper().replace(' ', '_')
        vcard.append(f'X-{clean_col_name};CHARSET=utf-8:{val_str}')

    if custom_notes:
      notes_text = '\\n'.join(custom_notes)
      vcard.append(f'NOTE;CHARSET=utf-8:{notes_text}')

    vcard.append('END:VCARD')

    # 檔名清理（清理不能作檔名的字元，確保可順利存檔）
    safe_filename = ''.join(
        [c for c in display_name if c.isalnum() or c in (' ', '_', '-')]
    ).strip()
    if not safe_filename:
      safe_filename = f'contact_{index + 1}'

    file_path = os.path.join(output_dir, f'{safe_filename}.vcf')

    # ==========================================
    # 3. 使用小寫 utf-8 開啟並寫入檔案
    # ==========================================
    with open(file_path, 'w', encoding='utf-8', newline='\r\n') as f:
      f.write('\n'.join(vcard))

    count += 1

  print(f'🎉 成功！已為 {count} 位聯絡人分別生成獨立的 VCF 檔案。')
  print(f'📁 檔案存放目錄：{output_dir}')
  input('\n按 Enter 鍵回到主選單...')


if __name__ == '__main__':
  run()