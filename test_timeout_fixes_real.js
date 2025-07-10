#!/usr/bin/env node

import { readFileSync } from 'fs';
import fetch from 'node-fetch';
import FormData from 'form-data';

console.log('🧪 Testing improved analyzer with real audio file...');

async function testWithRealFile() {
    try {
        // Use the existing test audio file
        const audioBuffer = readFileSync('./test_mario_stereo.wav');
        
        const formData = new FormData();
        formData.append('file', audioBuffer, {
            filename: 'test_mario_stereo.wav',
            contentType: 'audio/wav'
        });
        formData.append('bpm_hint', '120');
        
        console.log('🚀 Starting analysis with real audio file...');
        console.log(`   File size: ${audioBuffer.length} bytes`);
        
        const response = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const startResult = await response.json();
        const jobId = startResult.job_id;
        
        console.log(`📋 Got job ID: ${jobId}`);
        console.log(`   Status: ${startResult.status}`);
        
        // Monitor progress with reasonable intervals
        let attempts = 0;
        const maxAttempts = 60; // 2 minutes max
        
        while (attempts < maxAttempts) {
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
            
            console.log(`🕐 Checking progress (attempt ${attempts}/${maxAttempts})...`);
            
            try {
                const resultResponse = await fetch(`http://localhost:5000/result/${jobId}`);
                
                if (resultResponse.status === 200) {
                    const result = await resultResponse.json();
                    console.log(`✅ Analysis completed successfully!`);
                    console.log(`   Notes detected: ${result.sequence?.length || 0}`);
                    console.log(`   Tempo: ${result.detected_tempo || 'unknown'} BPM`);
                    console.log(`   Algorithm: ${result.analysis_params?.algorithm || 'unknown'}`);
                    console.log(`   Total frames processed: ${result.analysis_params?.total_frames || 'unknown'}`);
                    return result;
                } else if (resultResponse.status === 202) {
                    const progressData = await resultResponse.json();
                    console.log(`   Progress: ${progressData.progress || 0}% - ${progressData.message || 'Processing...'}`);
                    if (progressData.debug) {
                        console.log(`   Debug: ${progressData.debug}`);
                    }
                    continue;
                } else {
                    const error = await resultResponse.json();
                    console.error(`❌ Error: ${error.error || 'Unknown error'}`);
                    break;
                }
            } catch (error) {
                console.error(`❌ Network error: ${error.message}`);
                await new Promise(resolve => setTimeout(resolve, 2000));
                continue;
            }
        }
        
        console.log(`⏰ Timeout after ${maxAttempts} attempts (${maxAttempts * 2} seconds)`);
        return null;
        
    } catch (error) {
        console.error(`💥 Test failed: ${error.message}`);
        return null;
    }
}

// Run the test
testWithRealFile().then(result => {
    if (result) {
        console.log('🎉 Test completed successfully with timeout protection!');
        console.log('✅ Timeout fixes appear to be working correctly');
    } else {
        console.log('💔 Test failed or timed out');
    }
    process.exit(result ? 0 : 1);
}).catch(error => {
    console.error('💥 Unhandled error:', error);
    process.exit(1);
});