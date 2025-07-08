#!/usr/bin/env node

/**
 * Demo script showcasing the new search and filtering features
 */

const axios = require('axios');

const API_BASE = 'http://localhost:3000/api';

async function demoSearchFeatures() {
  console.log('🔍 Pupper App - Search & Filter Demo');
  console.log('=====================================\n');

  try {
    // Demo 1: Basic Search
    console.log('1️⃣  Basic Search Demo');
    console.log('   Searching for "labrador"...');
    const searchResponse = await axios.get(`${API_BASE}/dogs?search=labrador&limit=3`);
    console.log(`   ✅ Found ${searchResponse.data.data.pagination.total_items} dogs`);
    console.log(`   📝 Sample: ${searchResponse.data.data.dogs[0]?.dog_name} from ${searchResponse.data.data.dogs[0]?.city}\n`);

    // Demo 2: Advanced Filtering
    console.log('2️⃣  Advanced Filtering Demo');
    console.log('   Filtering: Weight 30-70lbs, Available status...');
    const filterResponse = await axios.get(`${API_BASE}/dogs?min_weight=30&max_weight=70&status=available&limit=3`);
    console.log(`   ✅ Found ${filterResponse.data.data.pagination.total_items} matching dogs`);
    if (filterResponse.data.data.dogs[0]) {
      const dog = filterResponse.data.data.dogs[0];
      console.log(`   📝 Sample: ${dog.dog_name} - ${dog.dog_weight}lbs, ${dog.status}\n`);
    }

    // Demo 3: Sorting
    console.log('3️⃣  Sorting Demo');
    console.log('   Sorting by weight (lightest first)...');
    const sortResponse = await axios.get(`${API_BASE}/dogs?sort_by=dog_weight&sort_order=asc&limit=3`);
    console.log(`   ✅ Sorted ${sortResponse.data.data.pagination.total_items} dogs by weight`);
    sortResponse.data.data.dogs.forEach((dog, i) => {
      console.log(`   ${i + 1}. ${dog.dog_name} - ${dog.dog_weight}lbs`);
    });
    console.log('');

    // Demo 4: Pagination
    console.log('4️⃣  Pagination Demo');
    console.log('   Getting page 2 with 5 results per page...');
    const pageResponse = await axios.get(`${API_BASE}/dogs?page=2&limit=5`);
    const pagination = pageResponse.data.data.pagination;
    console.log(`   ✅ Page ${pagination.current_page} of ${pagination.total_pages}`);
    console.log(`   📊 Showing ${pageResponse.data.data.dogs.length} of ${pagination.total_items} total dogs\n`);

    // Demo 5: Complex Query
    console.log('5️⃣  Complex Query Demo');
    console.log('   Search: "friendly" + Weight: 40-80lbs + Sort by age...');
    const complexResponse = await axios.get(`${API_BASE}/dogs?search=friendly&min_weight=40&max_weight=80&sort_by=dog_age_years&sort_order=desc&limit=3`);
    console.log(`   ✅ Complex query returned ${complexResponse.data.data.pagination.total_items} results`);
    console.log(`   🔧 Applied filters:`, Object.keys(complexResponse.data.data.filters_applied).join(', '));
    console.log(`   📈 Sorted by: ${complexResponse.data.data.sort.sort_by} (${complexResponse.data.data.sort.sort_order})\n`);

    // Summary
    console.log('🎯 Demo Summary');
    console.log('===============');
    console.log('✅ Basic keyword search');
    console.log('✅ Advanced filtering (weight, status, etc.)');
    console.log('✅ Multiple sorting options');
    console.log('✅ Pagination with configurable page sizes');
    console.log('✅ Complex queries with multiple criteria');
    console.log('✅ Real-time results with proper metadata');

    console.log('\n🌐 Try it yourself at: http://localhost:3000');
    console.log('   • Use the quick search on the homepage');
    console.log('   • Visit /search for advanced filtering');
    console.log('   • All searches are shareable via URL!');

  } catch (error) {
    console.error('❌ Demo failed:', error.message);
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Make sure the local app is running:');
      console.log('   cd frontend && npm start');
    }
  }
}

if (require.main === module) {
  demoSearchFeatures();
}
