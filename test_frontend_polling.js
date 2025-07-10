#!/usr/bin/env node

// Test the frontend polling logic directly
async function testWaitForResult(jobId) {
    console.log('🕐 waitForResult: Starting to wait for job:', jobId);
    let attempts = 0;
    while (true) {
        attempts++;
        console.log(`🕐 waitForResult: Attempt ${attempts} for job ${jobId}`);
        try {
            const fetch = (await import('node-fetch')).default;
            const response = await fetch(`http://localhost:5000/result/${jobId}`);
            console.log(`🕐 waitForResult: Got response status ${response.status}`);
            
            if (response.status === 200) {
                // Analysis completed successfully - this is the final result
                const result = await response.json();
                console.log('✅ waitForResult: Got final result with', result.sequence?.length || 0, 'notes');
                return result;
            } else if (response.status === 202) {
                // Analysis still in progress, wait and retry
                console.log('🕐 waitForResult: Still in progress (202), waiting...');
                await new Promise(resolve => setTimeout(resolve, 1000));
                continue;
            } else {
                // Error occurred
                const error = await response.json();
                console.error('❌ waitForResult: API error:', error);
                throw new Error(error.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('❌ waitForResult: Error in attempt', attempts, ':', error.message);
            if (error.message.includes('fetch')) {
                // Network error, wait and retry
                console.log('🕐 waitForResult: Network error, retrying...');
                await new Promise(resolve => setTimeout(resolve, 2000));
                continue;
            } else {
                console.error('❌ waitForResult: Non-network error, throwing:', error);
                throw error;
            }
        }
        
        if (attempts > 5) {
            console.log('🛑 Stopping test after 5 attempts');
            break;
        }
    }
}

// Test with the job ID that was stuck
const jobId = '1d4fde05-b815-4978-9b66-822e096b782b';
testWaitForResult(jobId).then(result => {
    console.log('🎉 Test completed successfully!');
    console.log('Result:', result ? 'Found' : 'Not found');
}).catch(error => {
    console.log('💥 Test failed:', error.message);
});