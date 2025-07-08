#!/usr/bin/env node

/**
 * Test script for local Pupper app functionality
 * Tests both frontend accessibility and API functionality through proxy
 */

const axios = require('axios');

const LOCAL_FRONTEND_URL = 'http://localhost:3000';
const API_BASE = `${LOCAL_FRONTEND_URL}/api`;

// Test cases for local app
const tests = [
  {
    name: 'Frontend Accessibility',
    test: async () => {
      const response = await axios.get(LOCAL_FRONTEND_URL);
      return response.status === 200 && response.data.includes('Pupper');
    }
  },
  {
    name: 'API Proxy - Basic Dogs List',
    test: async () => {
      const response = await axios.get(`${API_BASE}/dogs?limit=5`);
      return response.data.success && response.data.data.dogs.length > 0;
    }
  },
  {
    name: 'Search Functionality',
    test: async () => {
      const response = await axios.get(`${API_BASE}/dogs?search=labrador&limit=3`);
      return response.data.success && response.data.data.pagination.total_items > 0;
    }
  },
  {
    name: 'Weight Filter',
    test: async () => {
      const response = await axios.get(`${API_BASE}/dogs?min_weight=30&max_weight=70&limit=3`);
      return response.data.success && response.data.data.filters_applied.min_weight === '30';
    }
  },
  {
    name: 'Sorting Functionality',
    test: async () => {
      const response = await axios.get(`${API_BASE}/dogs?sort_by=dog_weight&sort_order=asc&limit=3`);
      return response.data.success && response.data.data.sort.sort_by === 'dog_weight';
    }
  },
  {
    name: 'Pagination',
    test: async () => {
      const response = await axios.get(`${API_BASE}/dogs?page=2&limit=5`);
      return response.data.success && response.data.data.pagination.current_page === 2;
    }
  }
];

async function runTests() {
  console.log('🐕 Testing Local Pupper App');
  console.log('============================\n');

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      console.log(`Testing: ${test.name}...`);
      const result = await test.test();
      
      if (result) {
        console.log(`✅ ${test.name} - PASSED\n`);
        passed++;
      } else {
        console.log(`❌ ${test.name} - FAILED (returned false)\n`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${test.name} - FAILED`);
      console.log(`   Error: ${error.message}\n`);
      failed++;
    }
  }

  console.log('='.repeat(40));
  console.log(`📊 Test Results:`);
  console.log(`   Passed: ${passed} ✅`);
  console.log(`   Failed: ${failed} ❌`);
  console.log(`   Total:  ${tests.length}`);
  console.log(`   Success Rate: ${((passed / tests.length) * 100).toFixed(1)}%`);

  if (failed === 0) {
    console.log('\n🎉 All tests passed! Your local app is working perfectly!');
    console.log('\n🌐 Access your app at: http://localhost:3000');
    console.log('\n📋 Available features:');
    console.log('   • Homepage with quick search');
    console.log('   • Advanced search page (/search)');
    console.log('   • Comprehensive filtering');
    console.log('   • Sorting and pagination');
    console.log('   • Responsive design');
  } else {
    console.log('\n⚠️  Some tests failed. Check the errors above.');
  }
}

if (require.main === module) {
  runTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
  });
}
