# Enhanced Search and Filter Features

This document describes the comprehensive search and filtering functionality added to the Pupper dog adoption application.

## Overview

The enhanced search system provides users with powerful tools to find their perfect canine companion through:
- **Keyword Search**: Full-text search across multiple fields
- **Advanced Filters**: Combinable filters for precise results
- **Smart Sorting**: Multiple sorting options
- **Pagination**: Efficient handling of large result sets
- **Real-time Updates**: Responsive search with debounced input

## Backend Enhancements

### Enhanced API Endpoint: GET /dogs

The `/dogs` endpoint now supports comprehensive query parameters for search and filtering:

#### Search Parameters
- `search`: Keyword search across name, breed, description, shelter, location, and status
- `page`: Page number for pagination (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `sort_by`: Field to sort by (default: created_at)
- `sort_order`: Sort direction - 'asc' or 'desc' (default: desc)

#### Filter Parameters

**Location Filters:**
- `state`: Filter by state (exact match, case-insensitive)
- `city`: Filter by city (partial match, case-insensitive)

**Physical Characteristics:**
- `min_weight`: Minimum weight in pounds
- `max_weight`: Maximum weight in pounds
- `min_age`: Minimum age in years
- `max_age`: Maximum age in years
- `color`: Filter by color (partial match, case-insensitive)

**Dog Details:**
- `status`: Filter by adoption status (available, adopted, pending)
- `species`: Filter by species (partial match)
- `shelter`: Filter by shelter name (partial match)
- `is_labrador`: Filter for Labrador Retrievers only (true/false)
- `tags`: Filter by tags (comma-separated, partial match)

**Date Filters:**
- `entry_date_from`: Shelter entry date from (MM/DD/YYYY format)
- `entry_date_to`: Shelter entry date to (MM/DD/YYYY format)

**Popularity Filters:**
- `min_wag_count`: Minimum number of wag votes
- `max_growl_count`: Maximum number of growl votes

### Response Format

```json
{
  "success": true,
  "message": "Dogs retrieved successfully",
  "data": {
    "dogs": [...],
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    },
    "filters_applied": {
      "state": "VA",
      "max_weight": "50"
    },
    "sort": {
      "sort_by": "created_at",
      "sort_order": "desc"
    }
  }
}
```

## Frontend Components

### 1. SearchAndFilter Component

**Location:** `/frontend/src/components/SearchAndFilter.js`

**Features:**
- Debounced search input (300ms delay)
- Collapsible advanced filters
- Real-time filter application
- Clear all filters functionality
- Responsive design

**Props:**
- `onFiltersChange`: Callback when filters change
- `initialFilters`: Initial filter values
- `isLoading`: Loading state

### 2. SearchResults Component

**Location:** `/frontend/src/components/SearchResults.js`

**Features:**
- Loading skeleton during searches
- Error handling with retry option
- No results state with helpful suggestions
- Results summary with count
- Search term highlighting in results

**Props:**
- `dogs`: Array of dog results
- `isLoading`: Loading state
- `error`: Error object
- `totalResults`: Total number of results
- `appliedFilters`: Currently applied filters
- `searchQuery`: Current search query
- `onRetry`: Retry callback

### 3. Pagination Component

**Location:** `/frontend/src/components/Pagination.js`

**Features:**
- Smart page number display
- First/last page navigation
- Items per page selector
- Mobile-responsive design
- Disabled states during loading

**Props:**
- `currentPage`: Current page number
- `totalPages`: Total number of pages
- `totalItems`: Total number of items
- `itemsPerPage`: Items per page
- `onPageChange`: Page change callback
- `onItemsPerPageChange`: Items per page change callback
- `isLoading`: Loading state

### 4. SearchHighlight Component

**Location:** `/frontend/src/components/SearchHighlight.js`

**Features:**
- Highlights search terms in text
- Case-insensitive matching
- Regex-safe search term handling
- Customizable styling

**Props:**
- `text`: Text to highlight
- `searchQuery`: Search term to highlight
- `className`: Additional CSS classes

## Page Implementations

### 1. Enhanced SearchPage

**Location:** `/frontend/src/pages/SearchPage.js`

**Features:**
- URL-based filter state management
- Browser back/forward support
- Comprehensive search interface
- Real-time results updates
- Search tips for users
- Debug information (development mode)

### 2. Enhanced HomePage

**Location:** `/frontend/src/pages/HomePage.js`

**Features:**
- Quick search bar in hero section
- Basic filter controls
- Featured dogs display
- Direct navigation to advanced search

## Search Algorithm

### Keyword Search Logic

The search functionality performs case-insensitive partial matching across:

1. **Dog Information:**
   - Dog name (decrypted)
   - Dog species/breed
   - Dog description
   - Dog color
   - Status

2. **Location Information:**
   - Shelter name
   - City
   - State

3. **Additional Fields:**
   - Tags (if present)

### Filter Combination

All filters are combined using AND logic:
- Dogs must match ALL specified criteria
- Empty/undefined filters are ignored
- Partial matches are used for text fields
- Exact matches for categorical fields
- Range filters for numerical fields

### Sorting Options

Available sort fields:
- `created_at`: Date added to system
- `dog_name`: Alphabetical by name
- `dog_age_years`: By age
- `dog_weight`: By weight
- `wag_count`: By popularity (wag votes)
- `shelter_entry_date`: By shelter entry date

## Performance Considerations

### Backend Optimizations

1. **Efficient Filtering**: Filters are applied in memory after DynamoDB scan
2. **Pagination**: Reduces response size and improves load times
3. **Caching**: Query results are cached on the frontend
4. **Debouncing**: Prevents excessive API calls during typing

### Frontend Optimizations

1. **React Query**: Intelligent caching and background updates
2. **Debounced Search**: 300ms delay prevents excessive requests
3. **Skeleton Loading**: Improves perceived performance
4. **URL State Management**: Preserves search state across navigation

## Usage Examples

### Basic Search
```
GET /dogs?search=friendly labrador
```

### Advanced Filtering
```
GET /dogs?state=VA&min_weight=30&max_weight=70&color=brown&status=available&sort_by=dog_age_years&sort_order=asc
```

### Pagination
```
GET /dogs?page=2&limit=50&sort_by=created_at&sort_order=desc
```

### Complex Query
```
GET /dogs?search=playful&state=VA&min_age=2&max_age=8&max_weight=60&sort_by=wag_count&sort_order=desc&page=1&limit=20
```

## Testing

### Automated Testing

Run the comprehensive test suite:

```bash
node test-search-functionality.js
```

This tests:
- Basic keyword searches
- Individual filter functionality
- Filter combinations
- Sorting options
- Pagination
- Edge cases and error handling

### Manual Testing Checklist

- [ ] Search by dog name
- [ ] Search by location
- [ ] Search by description keywords
- [ ] Apply single filters
- [ ] Combine multiple filters
- [ ] Test all sorting options
- [ ] Navigate through pages
- [ ] Change items per page
- [ ] Clear all filters
- [ ] Test responsive design
- [ ] Verify URL state management
- [ ] Test error handling

## Future Enhancements

### Planned Features

1. **Saved Searches**: Allow users to save and reuse search criteria
2. **Search History**: Track recent searches
3. **Smart Suggestions**: Auto-complete and search suggestions
4. **Geolocation Search**: Find dogs near user's location
5. **Advanced Matching**: AI-powered dog matching based on preferences
6. **Faceted Search**: Show available filter options with counts
7. **Search Analytics**: Track popular searches and filters

### Performance Improvements

1. **Elasticsearch Integration**: For more advanced search capabilities
2. **Database Indexing**: Optimize DynamoDB queries
3. **CDN Caching**: Cache search results at edge locations
4. **Search Result Prefetching**: Preload likely next pages

## Troubleshooting

### Common Issues

1. **No Results Found**
   - Check filter combinations aren't too restrictive
   - Verify search terms are spelled correctly
   - Try broader search terms

2. **Slow Search Performance**
   - Check network connectivity
   - Verify API endpoint is responding
   - Consider reducing result limit

3. **Filters Not Working**
   - Ensure filter values are in correct format
   - Check for JavaScript errors in console
   - Verify API is receiving correct parameters

### Debug Information

In development mode, the SearchPage displays debug information including:
- Current page and pagination details
- Applied filters
- Sort configuration
- API response structure

This helps developers troubleshoot search issues and verify correct functionality.
