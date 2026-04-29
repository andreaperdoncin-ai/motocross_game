from PIL import Image
import math
import wave
import struct

# 1. Update coin.png
img = Image.open('assets/coin.png').convert('RGBA')
pixels = img.load()
width, height = img.size

for y in range(height):
    for x in range(width):
        r, g, b, a = pixels[x, y]
        dist = math.sqrt((255-r)**2 + (255-g)**2 + (255-b)**2)
        if dist < 40:
            pixels[x, y] = (r, g, b, 0)
        elif dist < 80:
            alpha = int((dist - 40) * (255 / 40))
            pixels[x, y] = (r, g, b, min(a, alpha))
            
img.save('assets/coin.png')
print("coin.png updated.")

# 2. Generate bg_music.wav
sample_rate = 44100
duration = 8.0 
num_samples = int(duration * sample_rate)
with wave.open('assets/bg_music.wav', 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    for i in range(num_samples):
        t = i / sample_rate
        beat = int(t * 4) % 8
        bass_freq = [55.0, 55.0, 65.41, 65.41, 73.42, 73.42, 49.0, 49.0][beat]
        wave1 = 2.0 * ((t * bass_freq) - math.floor(0.5 + t * bass_freq))
        
        note = int(t * 8) % 16
        melody_freq = [220.0, 0, 261.63, 0, 329.63, 0, 261.63, 220.0,
                       196.0, 0, 261.63, 0, 293.66, 0, 261.63, 196.0][note]
        if melody_freq > 0:
            wave2 = 1.0 if (t * melody_freq * 2.0) % 2.0 < 1.0 else -1.0
            decay = math.exp(-10.0 * (t % 0.125))
            wave2 *= decay
        else:
            wave2 = 0
            
        sample = (wave1 * 0.4 + wave2 * 0.2) * 32767 * 0.4
        wav_file.writeframes(struct.pack('<h', int(sample)))
print("bg_music.wav created.")
