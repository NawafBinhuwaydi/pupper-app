#!/usr/bin/env node

/**
 * Test script for the enhanced search and filtering functionality
 * This script tests the backend API endpoints with various search and filter combinations
 */

const axios = require('axios');

// Configuration
const API_BASE_URL = process.env.API_URL || 'https://bj9jbp1rgf.execute-api.us-east-1.amazonaws.com/prod';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Test cases for search and filtering
const testCases = [
  {
    name: 'Basic search by keyword',
    params: { search: 'labrador' },
    description: 'Search for dogs with "labrador" in any field'
  },
  {
    name: 'Filter by state',
    params: { state: 'VA' },
    description: 'Filter dogs in Virginia'
  },
  {
    name: 'Weight range filter',
    params: { min_weight: 30, max_weight: 70 },
    description: 'Dogs between 30-70 lbs'
  },
  {
    name: 'Age range filter',
    params: { min_age: 1, max_age: 5 },
    description: 'Dogs between 1-5 years old'
  },
  {
    name: 'Color filter',
    params: { color: 'brown' },
    description: 'Brown colored dogs'
  },
  {
    name: 'Status filter',
    params: { status: 'available' },
    description: 'Available dogs only'
  },
  {
    name: 'Combined filters',
    params: { 
      state: 'VA', 
      max_weight: 50, 
      color: 'brown',
      status: 'available'
    },
    description: 'Available brown dogs under 50lbs in Virginia'
  },
  {
    name: 'Search with sorting',
    params: { 
      search: 'good',
      sort_by: 'dog_age_years',
      sort_order: 'asc'
    },
    description: 'Search "good" sorted by age ascending'
  },
  {
    name: 'Pagination test',
    params: { 
      page: 1,
      limit: 5,
      sort_by: 'created_at',
      sort_order: 'desc'
    },
    description: 'First 5 dogs, newest first'
  },
  {
    name: 'Date range filter',
    params: { 
      entry_date_from: '01/01/2020',
      entry_date_to: '12/31/2023'
    },
    description: 'Dogs entered between 2020-2023'
  },
  {
    name: 'Popularity filter',
    params: { 
      min_wag_count: 1,
      max_growl_count: 2
    },
    description: 'Popular dogs (min 1 wag, max 2 growls)'
  },
  {
    name: 'Labrador only filter',
    params: { is_labrador: 'true' },
    description: 'Labrador Retrievers only'
  },
  {
    name: 'Complex search query',
    params: { 
      search: 'friendly playful',
      state: 'VA',
      min_age: 2,
      max_age: 8,
      sort_by: 'wag_count',
      sort_order: 'desc',
      limit: 10
    },
    description: 'Complex search with multiple criteria'
  }
];

// Helper function to format results
function formatResults(data, testCase) {
  const dogs = data.data?.dogs || [];
  const pagination = data.data?.pagination || {};
  const filters = data.data?.filters_applied || {};
  const sort = data.data?.sort || {};

  return {
    test: testCase.name,
    description: testCase.description,
    results: {
      total_found: pagination.total_items || dogs.length,
      returned_count: dogs.length,
      current_page: pagination.current_page || 1,
      total_pages: pagination.total_pages || 1,
      filters_applied: filters,
      sort_info: sort,
      sample_dogs: dogs.slice(0, 3).map(dog => ({
        name: dog.dog_name,
        location: `${dog.city}, ${dog.state}`,
        age: dog.dog_age_years,
        weight: dog.dog_weight,
        color: dog.dog_color,
        status: dog.status,
        wag_count: dog.wag_count,
        growl_count: dog.growl_count
      }))
    }
  };
}

// Main test function
async function runTests() {
  console.log('🔍 Testing Enhanced Search and Filter Functionality\n');
  console.log(`API Base URL: ${API_BASE_URL}\n`);

  const results = [];
  let passedTests = 0;
  let failedTests = 0;

  for (const testCase of testCases) {
    try {
      console.log(`\n📋 Running: ${testCase.name}`);
      console.log(`   ${testCase.description}`);
      
      // Build query string
      const params = new URLSearchParams();
      Object.entries(testCase.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value);
        }
      });
      
      const queryString = params.toString();
      const url = queryString ? `/dogs?${queryString}` : '/dogs';
      
      console.log(`   Query: ${url}`);
      
      // Make API request
      const response = await api.get(url);
      
      if (response.data.success) {
        const result = formatResults(response.data, testCase);
        results.push(result);
        
        console.log(`   ✅ Success: Found ${result.results.total_found} dogs`);
        if (result.results.sample_dogs.length > 0) {
          console.log(`   📝 Sample: ${result.results.sample_dogs[0].name} (${result.results.sample_dogs[0].location})`);
        }
        
        passedTests++;
      } else {
        console.log(`   ❌ API returned success: false`);
        console.log(`   Error: ${response.data.error || 'Unknown error'}`);
        failedTests++;
      }
      
    } catch (error) {
      console.log(`   ❌ Request failed: ${error.message}`);
      if (error.response?.data) {
        console.log(`   Response: ${JSON.stringify(error.response.data, null, 2)}`);
      }
      failedTests++;
    }
    
    // Small delay between requests
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Tests: ${testCases.length}`);
  console.log(`Passed: ${passedTests} ✅`);
  console.log(`Failed: ${failedTests} ❌`);
  console.log(`Success Rate: ${((passedTests / testCases.length) * 100).toFixed(1)}%`);

  // Detailed results
  if (results.length > 0) {
    console.log('\n📋 DETAILED RESULTS');
    console.log('='.repeat(60));
    
    results.forEach((result, index) => {
      console.log(`\n${index + 1}. ${result.test}`);
      console.log(`   Description: ${result.description}`);
      console.log(`   Total Found: ${result.results.total_found}`);
      console.log(`   Returned: ${result.results.returned_count}`);
      console.log(`   Pages: ${result.results.current_page}/${result.results.total_pages}`);
      
      if (Object.keys(result.results.filters_applied).length > 0) {
        console.log(`   Filters: ${JSON.stringify(result.results.filters_applied)}`);
      }
      
      if (result.results.sort_info.sort_by) {
        console.log(`   Sort: ${result.results.sort_info.sort_by} (${result.results.sort_info.sort_order})`);
      }
      
      if (result.results.sample_dogs.length > 0) {
        console.log(`   Sample Dogs:`);
        result.results.sample_dogs.forEach(dog => {
          console.log(`     - ${dog.name} | ${dog.location} | ${dog.age}y, ${dog.weight}lbs | ${dog.color} | ${dog.status}`);
        });
      }
    });
  }

  // Performance insights
  console.log('\n🚀 PERFORMANCE INSIGHTS');
  console.log('='.repeat(60));
  
  const avgResults = results.reduce((sum, r) => sum + r.results.total_found, 0) / results.length;
  console.log(`Average results per query: ${avgResults.toFixed(1)}`);
  
  const filterUsage = {};
  results.forEach(r => {
    Object.keys(r.results.filters_applied).forEach(filter => {
      filterUsage[filter] = (filterUsage[filter] || 0) + 1;
    });
  });
  
  console.log('Most used filters:');
  Object.entries(filterUsage)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .forEach(([filter, count]) => {
      console.log(`  ${filter}: ${count} times`);
    });

  console.log('\n🎉 Testing completed!');
  
  if (failedTests > 0) {
    process.exit(1);
  }
}

// Run the tests
if (require.main === module) {
  runTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = { runTests };
