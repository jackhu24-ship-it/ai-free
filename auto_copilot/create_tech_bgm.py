import math
import struct
import wave

SAMPLE_RATE = 48000
DURATION = 44.0
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)

# Chord progression in D minor (Techno / Cyberpunk Diagnostic theme)
# Dm -> F -> C -> Bb
CHORDS = [
    [146.83, 174.61, 220.0, 261.63],  # D3, F3, A3, C4 (Dm7)
    [174.61, 220.0, 261.63, 329.63],  # F3, A3, C4, E4 (Fmaj7)
    [130.81, 164.81, 196.0, 246.94],  # C3, E3, G3, B3 (Cmaj7)
    [116.54, 146.83, 174.61, 220.0],  # Bb2, D3, F3, A3 (Bbmaj7)
]

BASS_NOTES = [73.42, 87.31, 65.41, 58.27] # D2, F2, C2, Bb1
CHORD_DURATION = 5.5 # seconds per chord

print("Synthesizing Cyber-Tech Ambient Soundtrack...")

left_channel = []
right_channel = []

for i in range(NUM_SAMPLES):
    t = i / SAMPLE_RATE
    chord_idx = int((t / CHORD_DURATION) % len(CHORDS))
    chord = CHORDS[chord_idx]
    bass_freq = BASS_NOTES[chord_idx]
    
    # 1. Warm Synth Pad (Stereo Detuned Sine + Soft Overtones)
    pad_left = 0.0
    pad_right = 0.0
    for f in chord:
        # Subtle detune for wide stereo imaging
        pad_left += math.sin(2 * math.pi * f * 0.998 * t) * 0.25
        pad_right += math.sin(2 * math.pi * f * 1.002 * t) * 0.25
        # Soft 2nd harmonic
        pad_left += math.sin(2 * math.pi * f * 2.0 * t) * 0.08
        pad_right += math.sin(2 * math.pi * f * 2.0 * t) * 0.08

    # Pad LFO volume swell
    pad_env = 0.6 + 0.4 * math.sin(2 * math.pi * 0.2 * t)
    pad_left *= pad_env
    pad_right *= pad_env

    # 2. Deep Sub-Bass Pulse (Telemetry Heartbeat)
    sub_bass = math.sin(2 * math.pi * bass_freq * t) * 0.45
    sub_bass += math.sin(2 * math.pi * (bass_freq * 2) * t) * 0.15

    # 3. Rhythmic Cyber Pluck / Arpeggio (120 BPM = 2 beats/sec)
    beat_time = (t * 4.0) % 1.0
    pluck_decay = math.exp(-beat_time * 8.0)
    arp_note_idx = int(t * 4.0) % len(chord)
    arp_freq = chord[arp_note_idx] * 2.0 # one octave up
    
    # Ping-pong stereo pan for arpeggio
    pan = math.sin(2 * math.pi * 0.5 * t)
    pan_l = 0.5 - 0.5 * pan
    pan_r = 0.5 + 0.5 * pan
    arp_sound = math.sin(2 * math.pi * arp_freq * t) * pluck_decay * 0.35
    
    # 4. Soft High-Tech Hi-hat Tick (Crisp Rhythmic Sense)
    hat_decay = math.exp(-beat_time * 25.0)
    # White noise pseudo-random tick
    pseudo_noise = (((i * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF) * 2.0 - 1.0
    hat_sound = pseudo_noise * hat_decay * 0.08

    # Combine stems
    mix_l = (pad_left * 0.35) + (sub_bass * 0.4) + (arp_sound * pan_l) + (hat_sound * 0.5)
    mix_r = (pad_right * 0.35) + (sub_bass * 0.4) + (arp_sound * pan_r) + (hat_sound * 0.5)

    # Master Fade In (1.5s) & Fade Out (3.0s)
    master_gain = 1.0
    if t < 1.5:
        master_gain = t / 1.5
    elif t > (DURATION - 3.0):
        master_gain = max(0.0, (DURATION - t) / 3.0)

    # Set BGM master level to sitting comfortably in background (-20dB)
    target_bgm_volume = 0.16 * master_gain
    
    mix_l *= target_bgm_volume
    mix_r *= target_bgm_volume

    left_channel.append(int(max(-1.0, min(1.0, mix_l)) * 32767))
    right_channel.append(int(max(-1.0, min(1.0, mix_r)) * 32767))

# Write WAV file
with wave.open("auto_copilot/tech_ambient_bgm.wav", "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    
    frames = bytearray()
    for l, r in zip(left_channel, right_channel):
        frames.extend(struct.pack("<hh", l, r))
    wf.writeframes(frames)

print("WAV soundtrack generated: auto_copilot/tech_ambient_bgm.wav (Duration: 44s, 48kHz Stereo)")
