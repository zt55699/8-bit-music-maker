# 🎵 8-Bit Music Maker

A web-based musical instrument that lets you create 8-bit style music using your keyboard. Simply type keys to generate retro-style square wave sounds and create your own chiptune compositions.

## Features

- **Real-time Music Creation**: Type keyboard keys to instantly generate 8-bit sounds
- **Authentic 8-bit Sound**: Uses Web Audio API with square wave oscillators for genuine retro sound
- **Visual Note Blocks**: Notes display as interactive colored blocks instead of text
- **Drag & Drop Editing**: Click and drag note blocks to reorder your music sequence
- **Advanced Navigation**: Use arrow keys to move cursor and navigate through notes
- **Visual Playback**: See current note highlighted and played notes dimmed during playback
- **Playback Controls**: Play, stop, and clear your compositions
- **Auto-Load System**: Automatically loads music data when pasted into textarea
- **Demo Song**: Load a pre-composed 8-bit melody to get started quickly
- **Clipboard Support**: Copy and paste music data easily
- **Mobile Responsive**: Optimized interface for mobile devices and tablets

## Quick Start

1. **Launch the application**:
   ```bash
   cd /home/tong/apps/8_bit_music
   python3 -m http.server 8080
   ```

2. **Open your browser** and navigate to `http://localhost:8080`

3. **Start creating music** by pressing keyboard keys!

## Keyboard Controls

### Music Keys
- **A-Z**: Various musical notes (different frequencies)
- **0-9**: Lower octave notes
- **Space**: Pause/rest in the music

### Navigation & Editing
- **Arrow Left/Right**: Move cursor position for inserting notes
- **Arrow Up/Down**: Select previous/next note
- **Backspace**: Delete note before cursor
- **Delete**: Delete selected note
- **Ctrl+D**: Duplicate selected note
- **Escape**: Deselect all notes

### Key-to-Frequency Mapping
```
Row 1: Q(261.63) W(293.66) E(329.63) R(349.23) T(392.00) Y(440.00) U(493.88) I(523.25) O(587.33) P(659.25)
Row 2: A(130.81) S(146.83) D(164.81) F(174.61) G(196.00) H(220.00) J(246.94) K(261.63) L(293.66)
Row 3: Z(329.63) X(349.23) C(392.00) V(440.00) B(493.88) N(523.25) M(587.33)
Numbers: 1(65.41) 2(73.42) 3(82.41) 4(87.31) 5(98.00) 6(110.00) 7(123.47) 8(130.81) 9(146.83) 0(164.81)
```

## Interface Controls

### Main Controls
- **▶️ Play**: Play your current music sequence with visual feedback
- **⏹️ Stop**: Stop playback
- **🗑️ Clear**: Clear all music data
- **💾 Save**: Export music to text format

### Data Management
- **📋 Copy to Clipboard**: Copy music data to clipboard
- **📋 Paste from Clipboard**: Paste and auto-load music data from clipboard
- **🎵 Load Demo Song**: Load a pre-composed 8-bit melody to get started

### Note Block Interactions
- **Click**: Select a note block
- **Double-click**: Play the selected note
- **Drag & Drop**: Reorder notes by dragging them to new positions

## Music Data Format

Music is stored as JSON with the following structure:
```json
{
  "version": "1.0",
  "sequence": [
    {
      "key": "a",
      "frequency": 130.81
    },
    {
      "key": " ",
      "frequency": 0
    }
  ],
  "created": "2025-07-08T08:00:00.000Z"
}
```

## Technical Details

- **Audio Engine**: Web Audio API with square wave oscillators
- **Browser Compatibility**: Modern browsers that support Web Audio API
- **No Dependencies**: Pure HTML, CSS, and JavaScript
- **Real-time Processing**: Low-latency audio generation
- **Responsive Design**: Works on desktop and mobile devices

## File Structure

```
8_bit_music/
├── index.html      # Main application UI
├── script.js       # Core application logic
├── README.md       # This file
├── HANDOFF.md      # Developer handoff documentation
└── server.log      # Server access log
```

## Usage Tips

1. **Get Started**: Click "🎵 Load Demo Song" to see the app in action
2. **Create Melodies**: Use the QWERTY row for a natural musical scale
3. **Navigate Easily**: Use arrow keys to move cursor and select notes
4. **Edit Visually**: Drag and drop note blocks to rearrange your music
5. **Add Rhythm**: Use space for pauses and timing
6. **Watch Playback**: Observe the visual feedback during music playback
7. **Auto-Load**: Simply paste JSON data into the textarea - it loads automatically
8. **Mobile Friendly**: Works great on phones and tablets with responsive design

## Browser Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Web Audio API support
- JavaScript enabled
- No additional plugins required

## Troubleshooting

### No Sound
- Check browser audio permissions
- Ensure volume is turned up
- Try clicking "Play" button first to initialize audio context

### Server Issues
- Make sure port 8080 is available
- Try different port: `python3 -m http.server 3000`
- Check if Python 3 is installed

### Performance
- Use Chrome or Firefox for best performance
- Close other audio applications if experiencing issues
- Refresh page if audio becomes unresponsive

## Contributing

This is a simple educational project. Feel free to:
- Add new sound effects
- Implement different waveforms
- Add visual effects
- Create preset songs
- Improve the UI design

## License

Open source - feel free to use, modify, and distribute.