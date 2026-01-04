import os
import cairosvg

def convert_svg_to_png():
    base_path = "src-tauri/icons"
    svg_path = os.path.join(base_path, "icon.svg")
    
    if not os.path.exists(svg_path):
        print(f"Error: {svg_path} not found.")
        return

    sizes = [
        (32, "32x32.png"),
        (128, "128x128.png"),
        (256, "128x128@2x.png"),
        (512, "icon.png")
    ]
    
    for size, name in sizes:
        output_path = os.path.join(base_path, name)
        try:
            cairosvg.svg2png(url=svg_path, write_to=output_path, output_width=size, output_height=size)
            print(f"Generated {output_path}")
        except Exception as e:
            print(f"Failed to generate {output_path}: {e}")

if __name__ == "__main__":
    convert_svg_to_png()
