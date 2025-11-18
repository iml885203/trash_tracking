# Add-on Icon 圖示說明

## 必要圖示檔案

Home Assistant Add-on 需要以下圖示檔案：

### 1. icon.png
- **尺寸**: 256x256 像素
- **格式**: PNG
- **用途**: 在 Add-on Store 中顯示
- **位置**: `trash_tracking_addon/icon.png`

### 2. logo.png (可選)
- **尺寸**: 256x256 像素
- **格式**: PNG
- **用途**: 在 Add-on 詳細頁面顯示
- **位置**: `trash_tracking_addon/logo.png`

## 設計建議

### 圖示主題
垃圾車追蹤系統，建議包含以下元素：
- 🚛 垃圾車圖示
- 📍 位置標記
- 🗺️ 地圖元素
- 🔔 通知鈴鐺

### 顏色方案
- 主色：綠色（環保主題）`#4CAF50`
- 輔色：藍色（科技感）`#2196F3`
- 強調色：橙色/紅色（通知）`#FF9800` 或 `#F44336`

### 風格
- 扁平化設計
- 圓角圖示
- 清晰的輪廓
- 適合深色/淺色背景

## 製作工具

### 線上工具
1. **Canva** - https://www.canva.com/
   - 提供免費圖示模板
   - 可匯出 PNG

2. **Figma** - https://www.figma.com/
   - 專業設計工具
   - 免費方案

3. **GIMP** - https://www.gimp.org/
   - 開源圖像編輯器
   - 免費

### 圖示資源
- [Font Awesome](https://fontawesome.com/) - 免費圖示
- [Material Icons](https://fonts.google.com/icons) - Google 圖示
- [Flaticon](https://www.flaticon.com/) - 扁平化圖示
- [Icons8](https://icons8.com/) - 多種風格圖示

## 快速製作步驟

### 使用 Canva（推薦新手）

1. **註冊/登入 Canva**
   - 前往 https://www.canva.com/

2. **建立自訂尺寸**
   - 點擊 "Create a design"
   - 選擇 "Custom size": 256 x 256 px

3. **新增元素**
   - 搜尋 "truck" 或"垃圾車"
   - 搜尋 "location pin"
   - 選擇合適的圖示

4. **組合設計**
   - 放置垃圾車在中央
   - 加入位置標記
   - 調整顏色為綠色系

5. **匯出**
   - 點擊 "Share" → "Download"
   - 格式：PNG
   - 尺寸：256x256 px

6. **儲存檔案**
   - 將檔案重新命名為 `icon.png`
   - 複製到 `trash_tracking_addon/icon.png`

### 使用 Font Awesome + GIMP

1. **下載圖示**
   - 前往 https://fontawesome.com/
   - 搜尋 "truck"、"location"
   - 下載 SVG 檔案

2. **在 GIMP 中組合**
   - 開啟 GIMP
   - 建立新圖片：256x256 px
   - 匯入 SVG 圖示
   - 調整大小和位置
   - 加入顏色

3. **匯出**
   - File → Export As
   - 選擇 PNG 格式
   - 儲存為 `icon.png`

## 暫時替代方案

如果暫時沒有圖示，可以使用簡單的替代方案：

### 使用 Emoji 生成器

創建一個簡單的 256x256 PNG，內容為垃圾車 emoji 🚛：

```python
from PIL import Image, ImageDraw, ImageFont

# 建立圖片
img = Image.new('RGBA', (256, 256), color=(76, 175, 80, 255))
draw = ImageDraw.Draw(img)

# 加入文字（emoji）
try:
    # 嘗試使用系統字體
    font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 180)
except:
    font = ImageFont.load_default()

text = "🚛"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (256 - text_width) // 2
y = (256 - text_height) // 2
draw.text((x, y), text, font=font, embedded_color=True)

# 儲存
img.save('trash_tracking_addon/icon.png')
print("Icon created!")
```

運行：
```bash
pip install Pillow
python generate_icon.py
```

## 檢查清單

發布前確認：

- [ ] `icon.png` 已建立
- [ ] 尺寸為 256x256 px
- [ ] 格式為 PNG
- [ ] 檔案大小 < 1MB
- [ ] 在深色/淺色背景都清晰可見
- [ ] 放置在 `trash_tracking_addon/icon.png`
- [ ] （可選）`logo.png` 也已建立

## 範例參考

參考其他 Home Assistant Add-ons 的圖示設計：
- [Official Add-ons](https://github.com/home-assistant/addons)
- [Community Add-ons](https://github.com/hassio-addons/repository)

## 版權注意事項

- 確保使用的圖示有適當授權
- 標註來源（如需要）
- 使用免費/開源圖示資源
- 避免使用受版權保護的圖片

---

**建議**: 先用簡單的 emoji 替代方案快速測試 Add-on，之後再替換成專業設計的圖示。
