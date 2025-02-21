import streamlit as st
import midiutil
import io
import base64
# import pyperclip
from midiutil import MIDIFile
import matplotlib.pyplot as plt

# Configuration
st.set_page_config(
    page_title="Modal Harmony Composer",
    page_icon="🎼",
    layout="centered",
    initial_sidebar_state="expanded"
)
def midi_to_bytes(midi_file):
    with io.BytesIO() as output_file:
        midi_file.writeFile(output_file)
        output_file.seek(0)
        return output_file.read()

def plot_piano_roll(notes):
    fig, ax = plt.subplots(figsize=(10, 4))
    for note, start, duration in notes:
        ax.barh(note, duration, left=start, height=0.8)
    ax.set_yticks(range(48, 84))
    ax.set_yticklabels([midi_number_to_name(n) for n in range(48, 84)])
    ax.set_xlabel('Time (beats)')
    ax.set_ylabel('Pitch')
    ax.set_title('Piano Roll Visualization')
    return fig

def midi_number_to_name(number):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (number // 12) - 1
    note = notes[number % 12]
    return f"{note}{octave}"

def get_characteristic_progressions(mode):
    progressions = {
        'ionian': "I-IV-V-I",
        'dorian': "i-IV-v",
        'phrygian': "i-II-III",
        'lydian': "I-II-I",
        'mixolydian': "I-bVII-IV",
        'aeolian': "i-VI-III-VII",
        'locrian': "i°-IV-vii°"
    }
    return progressions.get(mode, "I-IV-V-I")
SCALES = {
    'ionian': [0, 2, 4, 5, 7, 9, 11],       # Major scale
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'aeolian': [0, 2, 3, 5, 7, 8, 10],      # Natural Minor
    'locrian': [0, 1, 3, 5, 6, 8, 10]
}
# Music theory configurations
MODAL_HARMONY = {
    'ionian': ['maj', 'min', 'min', 'maj', 'maj', 'min', 'dim'],
    'dorian': ['min', 'min', 'maj', 'maj', 'min', 'dim', 'maj'],
    'phrygian': ['min', 'maj', 'maj', 'min', 'dim', 'maj', 'min'],
    'lydian': ['maj', 'maj', 'min', 'dim', 'maj', 'min', 'min'],
    'mixolydian': ['maj', 'min', 'dim', 'maj', 'min', 'min', 'maj'],
    'aeolian': ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj'],
    'locrian': ['dim', 'maj', 'min', 'min', 'maj', 'maj', 'min']
}

CHORD_QUALITIES = {
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    '7': [0, 4, 7, 10],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10]
}

NOTE_OFFSET = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 
              'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}

def get_mode_quality(mode, degree):
    """Get the characteristic chord quality for a mode's scale degree"""
    degrees = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
    index = degrees.index(degree)
    return MODAL_HARMONY[mode][index]

def parse_chord(chord_str, mode):
    """Parse chord input with mode-appropriate qualities"""
    parts = chord_str.split(':')
    numeral = parts[0].strip().upper()
    default_quality = get_mode_quality(mode, numeral)
    quality = parts[1].strip().lower() if len(parts) > 1 else default_quality
    
    degree_map = {'I':0, 'II':1, 'III':2, 'IV':3,
                 'V':4, 'VI':5, 'VII':6}
    
    if numeral not in degree_map:
        return 0, 'maj', CHORD_QUALITIES['maj']
    
    quality = quality if quality in CHORD_QUALITIES else default_quality
    return degree_map[numeral], quality, CHORD_QUALITIES[quality]

def generate_midi(key, mode, phrases):
    midi = MIDIFile(1)
    track = 0
    time = 0
    midi.addTrackName(track, time, "Modal Composition")
    midi.addTempo(track, time, 120)

    key_offset = NOTE_OFFSET[key]
    scale = SCALES[mode]
    notes = []

    for phrase in phrases:
        degree, quality, intervals = parse_chord(phrase['chord'], mode)
        rhythm_pattern = [float(r.strip()) for r in phrase['rhythm'].split(',')]
        length = phrase['length']
        
        root = key_offset + 60 + scale[degree % len(scale)]
        
        for i in range(length):
            duration = rhythm_pattern[i % len(rhythm_pattern)]
            for offset in intervals:
                note = root + offset
                midi.addNote(track, 0, note, time, duration, 80)
                notes.append((note, time, duration))
            time += duration

    return midi, notes

# ... (Keep midi_to_bytes, plot_piano_roll, midi_number_to_name functions same as previous version) ...

# Initialize session state
if 'phrases' not in st.session_state:
    st.session_state.phrases = [{'chord': 'I', 'length': 4, 'rhythm': '1.0'}]

# Sidebar Configuration
with st.sidebar:
    st.header("Modal Setup")
    key = st.selectbox("Tonic", list(NOTE_OFFSET.keys()), index=7)
    mode = st.selectbox("Mode", options=list(MODAL_HARMONY.keys()), 
                       format_func=lambda x: x.capitalize(), index=0)
    
    num_phrases = st.number_input("Number of Phrases", 1, 8, len(st.session_state.phrases))
    
    # Adjust phrases list length
    while len(st.session_state.phrases) < num_phrases:
        st.session_state.phrases.append({'chord': 'I', 'length': 4, 'rhythm': '1.0'})
    while len(st.session_state.phrases) > num_phrases:
        st.session_state.phrases.pop()
    
    st.header("Phrase Parameters")
    for i, phrase in enumerate(st.session_state.phrases):
        st.subheader(f"Phrase {i+1}")
        
        current_chord = phrase['chord'].split(':')[0]
        default_quality = get_mode_quality(mode, current_chord)
        
        col1, col2 = st.columns([2, 3])
        with col1:
            numeral = st.selectbox(
                f"Degree {i+1}", 
                ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'],
                index=['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'].index(current_chord)
            )
        with col2:
            quality = st.selectbox(
                f"Quality {i+1}",
                list(CHORD_QUALITIES.keys()),
                index=list(CHORD_QUALITIES.keys()).index(default_quality),
                help=f"Default {default_quality} for {mode.capitalize()}"
            )
        
        chord = f"{numeral}:{quality}" if quality != default_quality else numeral
        
        length = st.slider(f"Length {i+1}", 1, 16, phrase['length'])
        rhythm = st.text_input(
            f"Rhythm {i+1}", 
            phrase['rhythm'],
            help="Comma-separated durations (e.g., '0.5, 0.5, 1.0')"
        )
        
        st.session_state.phrases[i] = {
            'chord': chord,
            'length': length,
            'rhythm': rhythm
        }

# Main Interface
st.title("🎶 Modal Harmony Composer")
st.caption("Create compositions with mode-appropriate chord progressions")

if st.button("Generate Composition", type="primary"):
    with st.spinner("Crafting modal harmony..."):
        midi, notes = generate_midi(key, mode, st.session_state.phrases)
        midi_bytes = midi_to_bytes(midi)
        b64 = base64.b64encode(midi_bytes).decode()
        
        st.session_state.midi_data = {
            'bytes': midi_bytes,
            'base64': b64,
            'notes': notes,
            'phrases': st.session_state.phrases.copy(),
            'mode': mode
        }

if 'midi_data' in st.session_state:
    midi_data = st.session_state.midi_data
    
    # Audio Preview
    st.audio(midi_data['bytes'], format='audio/midi')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.download_button(
            label="⬇️ Download MIDI",
            data=midi_data['bytes'],
            file_name=f"{midi_data['mode']}_composition.mid",
            mime="audio/midi"
        )
        
        if st.button("📋 Copy MIDI Data"):
            try:
                # pyperclip.copy(midi_data['base64'])
                st.success("Base64 copied to clipboard!")
            except Exception as e:
                st.warning(f"Clipboard error: {str(e)}")
                st.code(midi_data['base64'][:100] + "...")
    
    with col2:
        st.pyplot(plot_piano_roll(midi_data['notes']))
    
    with st.expander("Modal Analysis"):
        st.markdown(f"""
        ### {midi_data['mode'].capitalize()} Mode Characteristics
        **[Diatonic Chords](pplx://action/followup):** `{MODAL_HARMONY[midi_data['mode']]}`  
        **[Characteristic Progressions](pplx://action/followup):** {get_characteristic_progressions(midi_data['mode'])}
        
        ### Phrase Breakdown
        """)
        for i, phrase in enumerate(midi_data['phrases']):
            degree, quality, _ = parse_chord(phrase['chord'], midi_data['mode'])
            st.markdown(f"""
            **[Phrase {i+1}](pplx://action/followup)**
            - Scale Degree: `{degree+1} ({quality})`
            - Duration: `{phrase['length']} beats`
            - Rhythm: `{phrase['rhythm']}`
            """)

def get_characteristic_progressions(mode):
    progressions = {
        'ionian': "I-IV-V-I",
        'dorian': "i-IV-v",
        'phrygian': "i-II-III",
        'lydian': "I-II-I",
        'mixolydian': "I-bVII-IV",
        'aeolian': "i-VI-III-VII",
        'locrian': "i°-IV-vii°"
    }
    return progressions.get(mode, "I-IV-V-I")

