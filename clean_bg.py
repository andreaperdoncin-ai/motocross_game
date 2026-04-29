from PIL import Image

def remove_background(img_path):
    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    bg_color = datas[0]
    
    for item in datas:
        # Calcola distanza cromatica dal pixel in alto a sinistra
        dist = sum(abs(a - b) for a, b in zip(item[:3], bg_color[:3]))
        
        # Considera trasparenti anche i grigi molto chiari o bianchi (alone antialiasing)
        is_light = item[0] > 200 and item[1] > 200 and item[2] > 200
        
        if dist < 60 or is_light:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(img_path)

try:
    remove_background("assets/bike_back_view.png")
    print("Background rimosso con successo.")
except Exception as e:
    print(f"Errore: {e}")
