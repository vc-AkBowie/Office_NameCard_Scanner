import os
import sys
import cv2
import numpy as np


def order_points_precise(pts):
  pts = pts.reshape(4, 2)
  rect = np.zeros((4, 2), dtype='float32')
  s = pts.sum(axis=1)
  rect[0] = pts[np.argmin(s)]
  rect[2] = pts[np.argmax(s)]
  diff = np.diff(pts, axis=1)
  rect[1] = pts[np.argmin(diff)]
  rect[3] = pts[np.argmax(diff)]
  return rect


def trim_background_borders(img_crop, lower_range, upper_range):
  h_crop, w_crop = img_crop.shape[:2]
  crop_hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
  crop_bg_mask = cv2.inRange(crop_hsv, lower_range, upper_range)

  top, bottom, left, right = 0, h_crop, 0, w_crop
  for y in range(min(20, h_crop // 5)):
    if np.sum(crop_bg_mask[y, :] > 0) > (w_crop * 0.1):
      top = y + 1
    else:
      break
  for y in range(h_crop - 1, max(h_crop - 20, h_crop * 4 // 5), -1):
    if np.sum(crop_bg_mask[y, :] > 0) > (w_crop * 0.1):
      bottom = y
    else:
      break
  for x in range(min(20, w_crop // 5)):
    if np.sum(crop_bg_mask[:, x] > 0) > (h_crop * 0.1):
      left = x + 1
    else:
      break
  for x in range(w_crop - 1, max(w_crop - 20, w_crop * 4 // 5), -1):
    if np.sum(crop_bg_mask[:, x] > 0) > (h_crop * 0.1):
      right = x
    else:
      break

  if top < bottom and left < right:
    return img_crop[top:bottom, left:right]
  return img_crop


# 關鍵：將所有執行邏輯包裹在 run() 函式內
def run():
  if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
  else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

  image_path = os.path.join(base_dir, 'front.jpg')
  output_dir = os.path.join(base_dir, 'front')

  if not os.path.exists(image_path):
    print(f'❌ 錯誤：找不到圖片檔案 {image_path}')
    input('\n按 Enter 鍵回到主選單...')
    return

  color_options = {
      '1': (
          '木紋/棕色/牛皮紙 (Wood/Brown)',
          np.array([10, 20, 20]),
          np.array([30, 255, 255]),
      ),
      '2': (
          '黑色/深色桌面 (Black/Dark)',
          np.array([0, 0, 0]),
          np.array([180, 255, 60]),
      ),
      '3': (
          '白色/淺色桌面 (White/Light)',
          np.array([0, 0, 160]),
          np.array([180, 50, 255]),
      ),
      '4': (
          '綠色切割墊 (Green)',
          np.array([35, 40, 40]),
          np.array([85, 255, 255]),
      ),
      '5': (
          '藍色桌面 (Blue)',
          np.array([90, 40, 40]),
          np.array([130, 255, 255]),
      ),
  }

  print('==========================================')
  print('請選擇正面圖片的「底紙/背景顏色」：')
  for key, value in color_options.items():
    print(f' [{key}] {value[0]}')
  print('==========================================')

  choice = input('請輸入編號 (預設 1 - 木紋): ').strip()
  if choice not in color_options:
    choice = '1'

  selected_color_name, bg_lower, bg_upper = color_options[choice]
  print(f'👉 已選擇背景顏色：【{selected_color_name}】\n')

  img = cv2.imread(image_path)
  if img is None:
    print(f'❌ 錯誤：無法讀取圖片 {image_path}')
    input('\n按 Enter 鍵回到主選單...')
    return

  orig = img.copy()
  h, w = img.shape[:2]
  os.makedirs(output_dir, exist_ok=True)

  hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
  bg_mask = cv2.inRange(hsv, bg_lower, bg_upper)
  card_mask = cv2.bitwise_not(bg_mask)

  kernel_fill = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
  closed_mask = cv2.morphologyEx(card_mask, cv2.MORPH_CLOSE, kernel_fill)

  kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
  cleaned_mask = cv2.morphologyEx(closed_mask, cv2.MORPH_OPEN, kernel_clean)

  contours, _ = cv2.findContours(
      cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
  )

  min_area = (h * w) * 0.03
  max_area = (h * w) * 0.25

  valid_cards = []
  for c in contours:
    area = cv2.contourArea(c)
    if min_area <= area <= max_area:
      rect = cv2.minAreaRect(c)
      box = cv2.boxPoints(rect)
      M = cv2.moments(c)
      if M['m00'] != 0:
        cy = int(M['m01'] / M['m00'])
        cx = int(M['m10'] / M['m00'])
        valid_cards.append({'contour_pts': box, 'cy': cy, 'cx': cx})

  row_threshold = 100
  valid_cards.sort(key=lambda item: item['cy'])

  rows = []
  for card in valid_cards:
    placed = False
    for row in rows:
      if abs(card['cy'] - row[0]['cy']) < row_threshold:
        row.append(card)
        placed = True
        break
    if not placed:
      rows.append([card])

  sorted_cards = []
  for row in rows:
    row.sort(key=lambda item: item['cx'])
    sorted_cards.extend(row)

  card_count = 0
  for item in sorted_cards:
    box = item['contour_pts']
    rect_pts = order_points_precise(box)
    (tl, tr, br, bl) = rect_pts

    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array(
        [
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1],
        ],
        dtype='float32',
    )

    M = cv2.getPerspectiveTransform(rect_pts, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

    inset_px = 8
    if maxWidth > 2 * inset_px and maxHeight > 2 * inset_px:
      warped = warped[
          inset_px : maxHeight - inset_px, inset_px : maxWidth - inset_px
      ]

    warped = trim_background_borders(warped, bg_lower, bg_upper)

    new_h, new_w = warped.shape[:2]
    if new_h > new_w:
      warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)

    card_count += 1
    output_filename = os.path.join(output_dir, f'front_{card_count}.jpg')
    cv2.imwrite(output_filename, warped)
    print(f'成功裁切完整正面名片 第 {card_count} 張：{output_filename}')

  print(f'\n全部處理完成！共成功裁切出 {card_count} 張完整正面名片！')
  input('\n按 Enter 鍵回到主選單...')


# 確保當單獨執行此檔時會呼叫 run()
if __name__ == '__main__':
  run()