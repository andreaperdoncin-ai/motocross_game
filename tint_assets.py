from PIL import Image
import colorsys
import os

def recolor_image(image_path, output_path, target_color):
    """
    Tints the image towards a target color while preserving luminance and colorkey transparency.
    """
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return

    img = Image.open(image_path).convert('RGBA')
    pixels = img.load()
    width, height = img.size
    
    # Assume pixel at 0,0 is the background color
    bg_color = pixels[0, 0]
    
    tr, tg, tb = target_color
    th, ts, tv = colorsys.rgb_to_hsv(tr/255.0, tg/255.0, tb/255.0)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # Check if it matches background color (with some tolerance for compression artifacts)
            is_bg = False
            if a == 0:
                is_bg = True
            elif abs(r - bg_color[0]) < 10 and abs(g - bg_color[1]) < 10 and abs(b - bg_color[2]) < 10:
                is_bg = True
                
            if is_bg:
                # Make strictly transparent so Pygame doesn't show boxes
                pixels[x, y] = (0, 0, 0, 0)
            else:
                # Convert to HSV
                h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                
                new_h = th
                new_s = min(1.0, s + 0.5)
                new_v = v
                
                r_new, g_new, b_new = colorsys.hsv_to_rgb(new_h, new_s, new_v)
                pixels[x, y] = (int(r_new*255), int(g_new*255), int(b_new*255), 255) # force alpha to 255 for solid parts
                
    img.save(output_path)
    print(f"Saved: {output_path}")

base_dir = "/home/andrea/PythonProjects/motocross_game/assets"

colors = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255)
}

files_to_tint = ["bike.png", "bike_back_view.png"]

for name in files_to_tint:
    path = os.path.join(base_dir, name)
    base_name, ext = os.path.splitext(name)
    for cname, cval in colors.items():
        out_path = os.path.join(base_dir, f"{base_name}_{cname}{ext}")
        recolor_image(path, out_path, cval)

print("Done tinting!")
