const fs = require('fs');
const path = require('path');

// Create a simple test image (1x1 pixel PNG)
const testImageBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==';

// Test data
const testData = {
  image_data: testImageBase64,
  content_type: 'image/png',
  dog_id: 'test-dog-456',
  description: 'Test image for dog upload functionality'
};

console.log('🐕 Testing Image Upload API');
console.log('============================');
console.log('');
console.log('Test Data:');
console.log('- Image size:', Buffer.from(testImageBase64, 'base64').length, 'bytes');
console.log('- Content type:', testData.content_type);
console.log('- Dog ID:', testData.dog_id);
console.log('');

// Create curl command
const curlCommand = `curl -X POST "https://bj9jbp1rgf.execute-api.us-east-1.amazonaws.com/prod/images" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(testData)}' | jq .`;

console.log('Curl command:');
console.log(curlCommand);
console.log('');

// Execute the test
const { exec } = require('child_process');
exec(curlCommand, (error, stdout, stderr) => {
  if (error) {
    console.error('❌ Error:', error);
    return;
  }
  
  console.log('✅ Response:');
  console.log(stdout);
  
  if (stderr) {
    console.log('⚠️  Stderr:', stderr);
  }
});

console.log('🚀 Running test...');
