import os
import sys

# 1. 強制切換 CMD 頁碼與標準輸出為 UTF-8 (徹底解決 Windows 中文亂碼)
if sys.platform == 'win32':
  os.system('chcp 65001 >nul')
  try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
  except AttributeError:
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# 自動取得執行檔/腳本所在的基礎路徑
if getattr(sys, 'frozen', False):
  base_dir = os.path.dirname(sys.executable)
else:
  base_dir = os.path.dirname(os.path.abspath(__file__))


def print_header():
  os.system('cls' if os.name == 'nt' else 'clear')
  print('==========================================')
  print('       🎴 名片批次掃描與自動化處理系統       ')
  print('==========================================')
  print(f'📁 目前工作目錄：{base_dir}\n')


def main():
  while True:
    print_header()
    print('請選擇要執行的功能：')
    print(' [1] 裁切「正面」名片 (Card_front_RGB_usage)')
    print(' [2] 裁切「背面」名片 (Card_back_RGB_usage)')
    print(' [3] 上下合併正反面圖片 (Card_Combine)')
    print(' [4] 呼叫 Gemini AI 辨識名片並產出 Excel (AI_yieth)')
    print(' [5] 直接讀取 Excel 對圖片重新命名 (rename_from_excel)')
    print(' [6] 生成 Outlook VCF 通訊錄檔案 (vcf_maker)')
    print(' [A] 🚀 一鍵全自動執行 (步驟 3 -> 4 -> 5 -> 6)')
    print(' [Q] 退出程式')
    print('------------------------------------------')

    choice = input('請輸入選項 (1-6 / A / Q): ').strip().upper()

    try:
      if choice == '1':
        import Card_front_RGB_usage

        Card_front_RGB_usage.run()
      elif choice == '2':
        import Card_back_RGB_usage

        Card_back_RGB_usage.run()
      elif choice == '3':
        import Card_Combine

        Card_Combine.run()
      elif choice == '4':
        import AI_yieth

        AI_yieth.run()
      elif choice == '5':
        import rename_from_excel

        rename_from_excel.run()
      elif choice == '6':
        import vcf_maker

        vcf_maker.run()
      elif choice == 'A':
        print('\n🚀 開始執行一鍵全自動流程...\n')
        import AI_yieth
        import Card_Combine
        import rename_from_excel
        import vcf_maker

        print('--- [步驟 1/4] 上下合併圖片 ---')
        Card_Combine.run()
        print('\n--- [步驟 2/4] AI 辨識名片 ---')
        AI_yieth.run()
        print('\n--- [步驟 3/4] 依 Excel 重新命名圖片 ---')
        rename_from_excel.run()
        print('\n--- [步驟 4/4] 產出 VCF 通訊錄 ---')
        vcf_maker.run()

        print('\n🎉 所有自動化流程已全數執行完畢！')
        input('\n按 Enter 鍵回到主選單...')
      elif choice == 'Q':
        print('\n感謝使用，程式即將退出。')
        break
      else:
        input('❌ 無效選項，按 Enter 鍵重新選擇...')
    except Exception as e:
      print(f'\n❌ 執行過程發生非預期錯誤：{e}')
      input('\n按 Enter 鍵回到主選單...')


if __name__ == '__main__':
  main()