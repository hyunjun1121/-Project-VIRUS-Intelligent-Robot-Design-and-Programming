import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

# Audio settings
SAMPLE_RATE = 16000  # Sampling rate
WINDOW_SIZE = 1000   # Visualization window size (number of samples)
CHANNELS = 1         # Mono channel

# Decibel threshold settings
THRESHOLD_DB = -35    # Recording start threshold
SILENCE_THRESHOLD_DB = -45  # Recording end threshold

# Data buffers
audio_data = np.zeros(WINDOW_SIZE)
times = np.linspace(0, WINDOW_SIZE / SAMPLE_RATE, WINDOW_SIZE)
db_levels = np.zeros(WINDOW_SIZE)
current_db = -100  # Initial dB value

# Decibel calculation function
def calculate_db(audio_data):
    """Calculate decibel level of audio data"""
    if len(audio_data) == 0:
        return -np.inf
    # Calculate RMS value
    rms = np.sqrt(np.mean(np.square(audio_data)))
    # Convert RMS to dB (0 dB reference is maximum possible amplitude 1.0)
    if rms > 0:
        db = 20 * np.log10(rms)
    else:
        db = -np.inf
    return db

# Audio callback function
def audio_callback(indata, frames, time_info, status):
    global audio_data, current_db
    if status:
        print(f"⚠️ Audio status: {status}")
    
    # Calculate dB of current frame
    current_frame = indata[:, 0] if CHANNELS > 1 else indata.flatten()
    current_db = calculate_db(current_frame)
    
    # Update buffer (FIFO method)
    audio_data = np.roll(audio_data, -len(current_frame))
    audio_data[-len(current_frame):] = current_frame

# Graph update function
def update_plot(frame):
    global audio_data, db_levels, current_db
    
    # Update dB level buffer
    db_levels = np.roll(db_levels, -1)
    db_levels[-1] = current_db
    
    # Update waveform graph
    waveform_line.set_ydata(audio_data)
    
    # Update dB level graph
    db_line.set_ydata(db_levels)
    
    # Update current dB display
    db_text.set_text(f'Current dB: {current_db:.1f}')
    
    # Update recording status display
    if current_db > THRESHOLD_DB:
        status_text.set_text('Status: Recording')
        status_text.set_color('red')
    elif current_db < SILENCE_THRESHOLD_DB:
        status_text.set_text('Status: Silence')
        status_text.set_color('blue')
    else:
        status_text.set_text('Status: Standby')
        status_text.set_color('black')
    
    return waveform_line, db_line, db_text, status_text, threshold_line, silence_line

# Main function
def main():
    global waveform_line, db_line, db_text, status_text, threshold_line, silence_line
    
    # Window setup
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Real-time Audio Decibel Monitor', fontsize=16)
    
    # Waveform graph setup
    ax1.set_ylim(-1, 1)
    ax1.set_xlim(0, WINDOW_SIZE / SAMPLE_RATE)
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Amplitude')
    ax1.set_title('Audio Waveform')
    ax1.grid(True)
    waveform_line, = ax1.plot(times, audio_data, lw=1)
    
    # Decibel level graph setup
    ax2.set_ylim(-80, 0)  # dB range
    ax2.set_xlim(0, WINDOW_SIZE)
    ax2.set_xlabel('Samples')
    ax2.set_ylabel('Decibel (dB)')
    ax2.set_title('Decibel Level')
    ax2.grid(True)
    db_line, = ax2.plot(np.arange(WINDOW_SIZE), db_levels, lw=2)
    
    # Add threshold lines
    threshold_line = ax2.axhline(y=THRESHOLD_DB, color='r', linestyle='-', alpha=0.7, label=f'Recording Start Threshold: {THRESHOLD_DB} dB')
    silence_line = ax2.axhline(y=SILENCE_THRESHOLD_DB, color='b', linestyle='--', alpha=0.7, label=f'Recording End Threshold: {SILENCE_THRESHOLD_DB} dB')
    ax2.legend(loc='lower right')
    
    # Add text information
    db_text = ax2.text(0.02, 0.95, f'Current dB: {current_db:.1f}', transform=ax2.transAxes, fontsize=12)
    status_text = ax2.text(0.02, 0.90, 'Status: Standby', transform=ax2.transAxes, fontsize=12)
    
    # Start audio stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        callback=audio_callback
    )
    stream.start()
    print("🎤 Starting audio monitoring through microphone...")
    
    # Start animation
    try:
        ani = FuncAnimation(fig, update_plot, interval=30, blit=True)
        plt.tight_layout()
        plt.show()
    finally:
        stream.stop()
        stream.close()
        print("🛑 Audio monitoring stopped.")

if __name__ == "__main__":
    print("=" * 50)
    print("Decibel Monitoring Tool")
    print("=" * 50)
    print(f"Recording start threshold: {THRESHOLD_DB} dB")
    print(f"Recording end threshold: {SILENCE_THRESHOLD_DB} dB")
    print("Close the graph window to exit the program.")
    print("=" * 50)
    main() 