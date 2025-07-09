# 🎵 8-Bit Music Maker

A web-based musical instrument that lets you create 8-bit style music using your keyboard. Simply type keys to generate retro-style square wave sounds and create your own chiptune compositions.

## Features

- **Real-time Music Creation**: Type keyboard keys to instantly generate 8-bit sounds
- **Authentic 8-bit Sound**: Uses Web Audio API with square wave oscillators for genuine retro sound
- **Visual Feedback**: See your music sequence displayed in real-time
- **Playback Controls**: Play, stop, and clear your compositions
- **Save/Load System**: Export music as JSON text format for sharing and persistence
- **Clipboard Support**: Copy and paste music data easily
- **Backspace Support**: Delete the last entered note with backspace

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
- **Backspace**: Delete the last entered note

### Key-to-Frequency Mapping
```
Row 1: Q(261.63) W(293.66) E(329.63) R(349.23) T(392.00) Y(440.00) U(493.88) I(523.25) O(587.33) P(659.25)
Row 2: A(130.81) S(146.83) D(164.81) F(174.61) G(196.00) H(220.00) J(246.94) K(261.63) L(293.66)
Row 3: Z(329.63) X(349.23) C(392.00) V(440.00) B(493.88) N(523.25) M(587.33)
Numbers: 1(65.41) 2(73.42) 3(82.41) 4(87.31) 5(98.00) 6(110.00) 7(123.47) 8(130.81) 9(146.83) 0(164.81)
```

## Interface Controls

- **▶️ Play**: Play your current music sequence
- **⏹️ Stop**: Stop playback
- **🗑️ Clear**: Clear all music data
- **💾 Save**: Export music to text format
- **📁 Load**: Import music from text format
- **📋 Copy to Clipboard**: Copy music data to clipboard
- **📋 Paste from Clipboard**: Paste music data from clipboard

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

1. **Create Melodies**: Use the QWERTY row for a natural musical scale
2. **Add Rhythm**: Use space for pauses and timing
3. **Experiment**: Try different key combinations for unique sounds
4. **Save Your Work**: Use the save/load feature to preserve compositions
5. **Share Music**: Copy the JSON data to share with others

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