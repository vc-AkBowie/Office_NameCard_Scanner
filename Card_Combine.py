import glob
import os
import sys
import cv2
import numpy as np


def run():
  # 1. 安全取得當前目錄 (相容 .py 與 PyInstaller .exe)
  if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
  else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

  # 設定資料夾路徑
  front_dir = os.path.join(base_dir, 'front')
  back_dir = os.path.join(base_dir, 'back')
  output_dir = os.path.join(base_dir, 'combined')

  # 自動建立輸出資料夾
  os.makedirs(output_dir, exist_ok=True)

  # 2. 獲取所有正面與背面圖片檔名
  front_files = sorted(glob.glob(os.path.join(front_dir, '*.jpg')))
  back_files = sorted(glob.glob(os.path.join(back_dir, '*.jpg')))

  if len(front_files) == 0 or len(back_files) == 0:
    print('❌ 錯誤：找不到正面或背面的圖片檔，請檢查檔案路徑。')
    input('\n按 Enter 鍵回到主選單...')
    return

  if len(front_files) != len(back_files):
    print(
        f'⚠️ 警告：正面圖片數量 ({len(front_files)}) 與背面圖片數量'
        f' ({len(back_files)}) 不一致！將按較少數量配對。'
    )

  # 3. 逐張配對並上下合併
  combined_count = 0
  for f_path, b_path in zip(front_files, back_files):
    img_front = cv2.imread(f_path)
    img_back = cv2.imread(b_path)

    if img_front is None or img_back is None:
      continue

    fh, fw = img_front.shape[:2]
    bh, bw = img_back.shape[:2]

    # --- 💡 步驟 3.1：寬度等比例對齊 ---
    if fw != bw:
      new_bh = int(bh * (fw / bw))
      img_back = cv2.resize(
          img_back, (fw, new_bh), interpolation=cv2.INTER_AREA
      )
      bh = new_bh

    # --- 💡 步驟 3.2：加入中間分隔線 ---
    divider_height = 6  # 分隔線厚度 (像素)
    divider = np.full((divider_height, fw, 3), 220, dtype=np.uint8)

    # --- 💡 步驟 3.3：垂直拼接 (上半部正面，下半部背面) ---
    combined_img = cv2.vconcat([img_front, divider, img_back])

    combined_count += 1
    base_name = os.path.basename(f_path)
    output_filename = os.path.join(
        output_dir, f'combined_{combined_count}_{base_name}'
    )

    cv2.imwrite(output_filename, combined_img)
    print(f'成功合併：{output_filename}')

  print(
      f'\n🎉 全部完成！已成功將 {combined_count}'
      ' 組名片正反面合併為單一張圖片！'
  )
  input('\n按 Enter 鍵回到主選單...')


# 確保單獨執行此檔時也能正常運作
if __name__ == '__main__':
  run()