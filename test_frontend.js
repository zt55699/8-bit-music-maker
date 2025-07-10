// Simple test to check if frontend processing works
const testResult = {
    "version": "1.0",
    "sequence": [
        {
            "duration": 2.2759410430839004,
            "frequency": 659.25,
            "key": "p",
            "start_time": 0.0
        },
        {
            "duration": 1.0,
            "frequency": 523.25,
            "key": "n",
            "start_time": 2.4816326530612245
        },
        {
            "duration": 1.25,
            "frequency": 659.25,
            "key": "p",
            "start_time": 3.0040816326530613
        },
        {
            "duration": 1.0,
            "frequency": 392.0,
            "key": "c",
            "start_time": 3.9880272108843537
        }
    ],
    "created": "2025-07-09T21:18:53.372594",
    "source": "advanced_audio_analysis",
    "detected_tempo": 120.18531976744185,
    "analysis_params": {
        "algorithm": "demucs+pyin+pentatonic"
    }
};

// Test deserialization directly
console.log('Testing frontend deserialization...');

// Mock BitMusicMaker class methods needed for test
class TestBitMusicMaker {
    constructor() {
        this.currentSequence = [];
        this.cursorPosition = 0;
        this.selectedNoteIndex = -1;
    }
    
    deserializeMusicData(jsonData) {
        try {
            console.log('🔍 deserializeMusicData: parsing JSON...');
            const data = JSON.parse(jsonData);
            console.log('🔍 deserializeMusicData: parsed data:', data);
            console.log('🔍 deserializeMusicData: has sequence?', !!data.sequence);
            console.log('🔍 deserializeMusicData: sequence is array?', Array.isArray(data.sequence));
            console.log('🔍 deserializeMusicData: sequence length:', data.sequence?.length);
            
            if (data.sequence && Array.isArray(data.sequence)) {
                console.log('🔍 deserializeMusicData: processing sequence...');
                this.currentSequence = data.sequence.map(note => {
                    console.log('🔍 Processing note:', note);
                    return {
                        key: note.key,
                        frequency: note.frequency,
                        duration: note.duration || 0.25,  // Default to quarter note for legacy data
                        timestamp: Date.now()
                    };
                });
                console.log('✅ deserializeMusicData: processed sequence:', this.currentSequence);
                return true;
            } else {
                console.error('❌ deserializeMusicData: sequence missing or not array');
                return false;
            }
        } catch (e) {
            console.error('❌ deserializeMusicData: Failed to parse music data:', e);
        }
        return false;
    }
    
    updateDisplay() {
        console.log('🖼️ updateDisplay called');
    }
    
    updateUploadStatus(msg) {
        console.log('📊 updateUploadStatus:', msg);
    }
    
    updateStatus(msg) {
        console.log('📊 updateStatus:', msg);
    }
    
    processAnalysisResult(result, file) {
        try {
            console.log('🔍 Processing analysis result:', result);
            console.log('🔍 Result has sequence:', result.sequence && Array.isArray(result.sequence));
            console.log('🔍 Sequence length:', result.sequence?.length);
            
            // Load the analyzed sequence
            const jsonString = JSON.stringify(result);
            console.log('🔍 Calling deserializeMusicData with:', jsonString.substring(0, 200) + '...');
            
            if (this.deserializeMusicData(jsonString)) {
                console.log('✅ deserializeMusicData succeeded');
                console.log('✅ Current sequence length:', this.currentSequence.length);
                
                this.cursorPosition = this.currentSequence.length;
                this.selectedNoteIndex = -1;
                this.updateDisplay();
                
                // Show improved message based on algorithm used
                const algorithm = result.analysis_params?.algorithm || 'unknown';
                const isAdvanced = algorithm.includes('demucs');
                const algorithmMsg = isAdvanced ? '🎛️ Advanced Demucs analysis' : 'Standard analysis';
                
                this.updateUploadStatus(`✅ ${algorithmMsg} complete! Found ${result.sequence.length} notes. Tempo: ${result.detected_tempo?.toFixed(1) || 'unknown'} BPM`);
                this.updateStatus(`Server audio analysis loaded: ${result.sequence.length} notes`);
                
                console.log(`✅ Analysis complete and music loaded:`, result);
                return true;
            } else {
                console.error('❌ deserializeMusicData failed');
                this.updateUploadStatus('⚠️ Failed to load analyzed sequence');
                return false;
            }
        } catch (error) {
            console.error('❌ Error processing analysis result:', error);
            this.updateUploadStatus('⚠️ Error processing analysis result');
            return false;
        }
    }
}

// Test it
const testMaker = new TestBitMusicMaker();
const success = testMaker.processAnalysisResult(testResult, { name: 'test.wav' });
console.log('Final result:', success ? 'SUCCESS' : 'FAILED');
console.log('Final sequence length:', testMaker.currentSequence.length);