#!/usr/bin/env python3
"""
Generate PNG icons from SVG for SMTPy
This script creates PNG icons in various sizes from the SVG source
"""
import json
from pathlib import Path
from io import BytesIO

try:
    import cairosvg
    from PIL import Image
    has_image_support = True
except ImportError:
    has_image_support = False
    print("Warning: cairosvg or PIL not available. Install with: pip install cairosvg pillow")

# Create the PNG files directory
public_dir = Path(__file__).parent / "public"
public_dir.mkdir(exist_ok=True)

# Icon sizes to generate
icon_sizes = [
    (16, "favicon-16x16.png"),
    (32, "favicon-32x32.png"),
    (48, "favicon-48x48.png"),
    (180, "apple-touch-icon.png"),
    (192, "icon-192.png"),
    (512, "icon-512.png"),
]

if has_image_support:
    # Read the SVG source
    svg_path = public_dir / "favicon.svg"

    if svg_path.exists():
        with open(svg_path, "r") as f:
            svg_data = f.read()

        # Generate PNG icons at different sizes
        for size, filename in icon_sizes:
            png_data = cairosvg.svg2png(
                bytestring=svg_data.encode('utf-8'),
                output_width=size,
                output_height=size
            )

            output_path = public_dir / filename
            with open(output_path, 'wb') as f:
                f.write(png_data)

            print(f"✓ Generated {filename} ({size}x{size})")

        # Generate favicon.ico (multi-size ICO file)
        ico_sizes = [16, 32, 48]
        images = []
        for size in ico_sizes:
            png_data = cairosvg.svg2png(
                bytestring=svg_data.encode('utf-8'),
                output_width=size,
                output_height=size
            )
            img = Image.open(BytesIO(png_data))
            images.append(img)

        # Save as ICO
        ico_path = public_dir / "favicon.ico"
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(s, s) for s in ico_sizes],
            append_images=images[1:]
        )
        print(f"✓ Generated favicon.ico (multi-size)")
    else:
        print(f"Error: {svg_path} not found")
else:
    print("⚠ Skipping PNG generation (missing dependencies)")

# Create manifest file
manifest = {
    "name": "SMTPy",
    "short_name": "SMTPy",
    "description": "Self-hosted email aliasing service",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#4F46E5",
    "icons": []
}

# Add icon references if we generated them
if has_image_support:
    manifest["icons"] = [
        {
            "src": "/favicon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any"
        },
        {
            "src": "/icon-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": "/icon-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": "/apple-touch-icon.png",
            "sizes": "180x180",
            "type": "image/png",
            "purpose": "any"
        }
    ]
else:
    manifest["icons"] = [
        {
            "src": "/favicon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any maskable"
        }
    ]

with open(public_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print("✓ Manifest created")
print("\n✅ Icon generation complete!")
