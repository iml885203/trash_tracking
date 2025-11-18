#!/usr/bin/env python3
"""
Simple icon generator for Trash Tracking Add-on
Creates a temporary 256x256 PNG icon with a truck emoji
"""

from PIL import Image, ImageDraw, ImageFont
import sys
from pathlib import Path


def generate_icon(output_path: str = "icon.png"):
    """Generate a simple icon with truck emoji"""

    # Create image with green background
    size = 256
    bg_color = (76, 175, 80, 255)  # Green (#4CAF50)
    img = Image.new('RGBA', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Add circular background
    margin = 20
    circle_bbox = [margin, margin, size - margin, size - margin]
    draw.ellipse(circle_bbox, fill=(255, 255, 255, 255))

    # Try to add truck emoji
    try:
        # macOS emoji font
        font_paths = [
            "/System/Library/Fonts/Apple Color Emoji.ttc",
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
            "C:\\Windows\\Fonts\\seguiemj.ttf",  # Windows
        ]

        font = None
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    font = ImageFont.truetype(font_path, 140)
                    break
                except Exception:
                    continue

        if font is None:
            print("⚠️  Warning: Could not load emoji font, using text instead")
            font = ImageFont.load_default()
            text = "TRUCK"
            color = bg_color
        else:
            text = "🚛"
            color = None  # Use emoji color

    except Exception as e:
        print(f"⚠️  Warning: Font loading failed ({e}), using default")
        font = ImageFont.load_default()
        text = "TRUCK"
        color = bg_color

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 10  # Slight offset

    # Draw text
    if color:
        draw.text((x, y), text, font=font, fill=color)
    else:
        draw.text((x, y), text, font=font, embedded_color=True)

    # Save image
    img.save(output_path)
    print(f"✅ Icon created: {output_path}")
    print(f"   Size: {size}x{size} px")
    print(f"   Format: PNG")

    return output_path


def generate_logo(output_path: str = "logo.png"):
    """Generate logo (same as icon for now)"""
    return generate_icon(output_path)


if __name__ == "__main__":
    try:
        # Get script directory
        script_dir = Path(__file__).parent

        # Generate icon
        icon_path = script_dir / "icon.png"
        generate_icon(str(icon_path))

        # Generate logo
        logo_path = script_dir / "logo.png"
        generate_logo(str(logo_path))

        print("\n📋 Next steps:")
        print("   1. Review the generated icons")
        print("   2. Replace with professional design later")
        print("   3. See ICON_README.md for design guidelines")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
