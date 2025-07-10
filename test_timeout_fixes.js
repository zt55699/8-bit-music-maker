#!/usr/bin/env node

import { readFileSync } from 'fs';
import fetch from 'node-fetch';
import FormData from 'form-data';

console.log('🧪 Testing improved analyzer with timeout fixes...');

async function testWithMockFile() {
    try {
        // Create a FormData with a simple test file
        const formData = new FormData();
        formData.append('file', Buffer.from('mock audio data'), {
            filename: 'test_mario.wav',
            contentType: 'audio/wav'
        });
        formData.append('bpm_hint', '120');
        
        console.log('🚀 Starting analysis...');
        
        const response = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const startResult = await response.json();
        const jobId = startResult.job_id;
        
        console.log(`📋 Got job ID: ${jobId}`);
        
        // Monitor progress with shorter intervals to test timeout handling
        let attempts = 0;
        const maxAttempts = 10;
        
        while (attempts < maxAttempts) {
            attempts++;
            console.log(`🕐 Checking progress (attempt ${attempts}/${maxAttempts})...`);
            
            try {
                const resultResponse = await fetch(`http://localhost:5000/result/${jobId}`);
                console.log(`   Status: ${resultResponse.status}`);
                
                if (resultResponse.status === 200) {
                    const result = await resultResponse.json();
                    console.log(`✅ Analysis completed successfully!`);
                    console.log(`   Notes detected: ${result.sequence?.length || 0}`);
                    console.log(`   Tempo: ${result.detected_tempo || 'unknown'} BPM`);
                    return result;
                } else if (resultResponse.status === 202) {
                    console.log(`   Still processing... waiting 2 seconds`);
                    await new Promise(resolve => setTimeout(resolve, 2000));
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
        
        console.log(`⏰ Timeout after ${maxAttempts} attempts`);
        return null;
        
    } catch (error) {
        console.error(`💥 Test failed: ${error.message}`);
        return null;
    }
}

// Run the test
testWithMockFile().then(result => {
    if (result) {
        console.log('🎉 Test completed successfully with timeout protection!');
    } else {
        console.log('💔 Test failed or timed out');
    }
    process.exit(result ? 0 : 1);
});