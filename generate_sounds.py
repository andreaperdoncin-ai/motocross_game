import wave
import struct
import math
import random

def generate_engine():
    sample_rate = 44100
    duration = 1.0 # 1 secondo in loop
    n_samples = int(sample_rate * duration)
    
    with wave.open("assets/engine.wav", "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2) # 16 bit
        f.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = i / sample_rate
            # Frequenza base motore (bassa)
            freq = 55 + 5 * math.sin(2 * math.pi * 15 * t) # Tremolio
            
            # Generazione onda a dente di sega mista a quadra (retro)
            phase = (t * freq) % 1.0
            if phase < 0.5:
                val = 1.0
            else:
                val = -1.0
                
            # Aggiungi un po' di "rumore" per simulare lo scarico della moto da cross
            noise = (random.random() - 0.5) * 0.5
            val = val * 0.7 + noise
            
            # Clipping morbido
            if val > 1.0: val = 1.0
            if val < -1.0: val = -1.0
            
            sample = int(val * 8000) # Volume non troppo alto
            f.writeframesraw(struct.pack('<h', sample))

def generate_coin():
    sample_rate = 44100
    duration = 0.15
    n_samples = int(sample_rate * duration)
    
    with wave.open("assets/coin.wav", "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = i / sample_rate
            # Arpeggio classico (bip retro)
            if t < 0.05: freq = 987.77 # B5
            else: freq = 1318.51 # E6
            
            val = math.sin(2 * math.pi * freq * t)
            # Onda quadra per effetto 8-bit
            val = 1.0 if val > 0 else -1.0
            
            # Fade out
            envelope = 1.0 - (t / duration)
            
            sample = int(val * envelope * 12000)
            f.writeframesraw(struct.pack('<h', sample))

try:
    generate_engine()
    generate_coin()
    print("Suoni generati con successo in assets/")
except Exception as e:
    print(f"Errore nella generazione dei suoni: {e}")
