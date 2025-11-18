# Add-on Icon Guide

## Required Icon Files

Home Assistant Add-on requires the following icon files:

### 1. icon.png
- **Size**: 256x256 pixels
- **Format**: PNG
- **Usage**: Displayed in Add-on Store
- **Location**: `trash_tracking_addon/icon.png`

### 2. logo.png (Optional)
- **Size**: 256x256 pixels
- **Format**: PNG
- **Usage**: Displayed on Add-on detail page
- **Location**: `trash_tracking_addon/logo.png`

## Design Recommendations

### Icon Theme
Trash tracking system, suggested elements:
- 🚛 Garbage truck icon
- 📍 Location marker
- 🗺️ Map elements
- 🔔 Notification bell

### Color Scheme
- Primary: Green (environmental theme) `#4CAF50`
- Secondary: Blue (tech feel) `#2196F3`
- Accent: Orange/Red (notification) `#FF9800` or `#F44336`

### Style
- Flat design
- Rounded corners
- Clear outlines
- Suitable for both dark/light backgrounds

## Design Tools

### Online Tools
1. **Canva** - https://www.canva.com/
   - Free icon templates
   - Can export PNG

2. **Figma** - https://www.figma.com/
   - Professional design tool
   - Free tier available

3. **GIMP** - https://www.gimp.org/
   - Open source image editor
   - Free

### Icon Resources
- [Font Awesome](https://fontawesome.com/) - Free icons
- [Material Icons](https://fonts.google.com/icons) - Google icons
- [Flaticon](https://www.flaticon.com/) - Flat icons
- [Icons8](https://icons8.com/) - Various style icons

## Quick Creation Steps

### Using Canva (Recommended for Beginners)

1. **Sign up/Login to Canva**
   - Go to https://www.canva.com/

2. **Create Custom Size**
   - Click "Create a design"
   - Select "Custom size": 256 x 256 px

3. **Add Elements**
   - Search "truck" or "garbage truck"
   - Search "location pin"
   - Select appropriate icons

4. **Compose Design**
   - Place truck in center
   - Add location marker
   - Adjust colors to green theme

5. **Export**
   - Click "Share" → "Download"
   - Format: PNG
   - Size: 256x256 px

6. **Save File**
   - Rename file to `icon.png`
   - Copy to `trash_tracking_addon/icon.png`

### Using Font Awesome + GIMP

1. **Download Icons**
   - Go to https://fontawesome.com/
   - Search "truck", "location"
   - Download SVG files

2. **Compose in GIMP**
   - Open GIMP
   - Create new image: 256x256 px
   - Import SVG icons
   - Adjust size and position
   - Add colors

3. **Export**
   - File → Export As
   - Select PNG format
   - Save as `icon.png`

## Temporary Alternative

If you don't have an icon ready, use a simple alternative:

### Using Emoji Generator

Create a simple 256x256 PNG with garbage truck emoji 🚛:

```python
from PIL import Image, ImageDraw, ImageFont

# Create image
img = Image.new('RGBA', (256, 256), color=(76, 175, 80, 255))
draw = ImageDraw.Draw(img)

# Add text (emoji)
try:
    # Try to use system font
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

# Save
img.save('trash_tracking_addon/icon.png')
print("Icon created!")
```

Run:
```bash
pip install Pillow
python generate_icon.py
```

## Checklist

Before publishing, confirm:

- [ ] `icon.png` created
- [ ] Size is 256x256 px
- [ ] Format is PNG
- [ ] File size < 1MB
- [ ] Visible on both dark/light backgrounds
- [ ] Placed in `trash_tracking_addon/icon.png`
- [ ] (Optional) `logo.png` also created

## Example References

Reference icon designs from other Home Assistant Add-ons:
- [Official Add-ons](https://github.com/home-assistant/addons)
- [Community Add-ons](https://github.com/hassio-addons/repository)

## Copyright Notes

- Ensure icons used have appropriate licensing
- Attribute sources (if required)
- Use free/open source icon resources
- Avoid using copyrighted images

---

**Recommendation**: Start with simple emoji alternative for quick testing, then replace with professionally designed icon later.
