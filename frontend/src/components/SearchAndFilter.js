import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, X, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';

const SearchAndFilter = ({ onFiltersChange, initialFilters = {}, isLoading = false }) => {
  const [searchQuery, setSearchQuery] = useState(initialFilters.search || '');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState({
    state: initialFilters.state || '',
    city: initialFilters.city || '',
    minWeight: initialFilters.min_weight || '',
    maxWeight: initialFilters.max_weight || '',
    minAge: initialFilters.min_age || '',
    maxAge: initialFilters.max_age || '',
    color: initialFilters.color || '',
    status: initialFilters.status || 'available',
    species: initialFilters.species || '',
    shelter: initialFilters.shelter || '',
    entryDateFrom: initialFilters.entry_date_from || '',
    entryDateTo: initialFilters.entry_date_to || '',
    minWagCount: initialFilters.min_wag_count || '',
    maxGrowlCount: initialFilters.max_growl_count || '',
    isLabrador: initialFilters.is_labrador || '',
    tags: initialFilters.tags || '',
    sortBy: initialFilters.sort_by || 'created_at',
    sortOrder: initialFilters.sort_order || 'desc'
  });

  const handleFiltersChange = useCallback(() => {
    const activeFilters = {
      search: searchQuery || undefined,
      state: filters.state || undefined,
      city: filters.city || undefined,
      min_weight: filters.minWeight || undefined,
      max_weight: filters.maxWeight || undefined,
      min_age: filters.minAge || undefined,
      max_age: filters.maxAge || undefined,
      color: filters.color || undefined,
      status: filters.status || undefined,
      species: filters.species || undefined,
      shelter: filters.shelter || undefined,
      entry_date_from: filters.entryDateFrom || undefined,
      entry_date_to: filters.entryDateTo || undefined,
      min_wag_count: filters.minWagCount || undefined,
      max_growl_count: filters.maxGrowlCount || undefined,
      is_labrador: filters.isLabrador || undefined,
      tags: filters.tags || undefined,
      sort_by: filters.sortBy,
      sort_order: filters.sortOrder
    };

    // Remove undefined values
    Object.keys(activeFilters).forEach(key => {
      if (activeFilters[key] === undefined) {
        delete activeFilters[key];
      }
    });

    onFiltersChange(activeFilters);
  }, [searchQuery, filters, onFiltersChange]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      handleFiltersChange();
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, handleFiltersChange]);

  useEffect(() => {
    handleFiltersChange();
  }, [filters, handleFiltersChange]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearAllFilters = () => {
    setSearchQuery('');
    setFilters({
      state: '',
      city: '',
      minWeight: '',
      maxWeight: '',
      minAge: '',
      maxAge: '',
      color: '',
      status: 'available',
      species: '',
      shelter: '',
      entryDateFrom: '',
      entryDateTo: '',
      minWagCount: '',
      maxGrowlCount: '',
      isLabrador: '',
      tags: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    });
  };

  const hasActiveFilters = searchQuery || Object.values(filters).some(value => 
    value && value !== 'available' && value !== 'created_at' && value !== 'desc'
  );

  const stateOptions = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
  ];

  const colorOptions = [
    'black', 'brown', 'white', 'golden', 'yellow', 'chocolate', 
    'cream', 'silver', 'gray', 'mixed', 'other'
  ];

  const statusOptions = [
    { value: 'available', label: 'Available' },
    { value: 'adopted', label: 'Adopted' },
    { value: 'pending', label: 'Pending' }
  ];

  const sortOptions = [
    { value: 'created_at', label: 'Date Added' },
    { value: 'dog_name', label: 'Name' },
    { value: 'dog_age_years', label: 'Age' },
    { value: 'dog_weight', label: 'Weight' },
    { value: 'wag_count', label: 'Wag Count' },
    { value: 'shelter_entry_date', label: 'Shelter Entry Date' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      {/* Search Bar */}
      <div className="relative mb-4">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search dogs by name, breed, description, shelter, location..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
          disabled={isLoading}
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {/* Filter Toggle and Clear */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          disabled={isLoading}
        >
          <Filter className="h-4 w-4" />
          <span>Advanced Filters</span>
          {showAdvancedFilters ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
            disabled={isLoading}
          >
            <RotateCcw className="h-4 w-4" />
            <span>Clear All</span>
          </button>
        )}
      </div>

      {/* Advanced Filters */}
      {showAdvancedFilters && (
        <div className="space-y-6 pt-4 border-t border-gray-200">
          {/* Location Filters */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Location</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <select
                  value={filters.state}
                  onChange={(e) => handleFilterChange('state', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                >
                  <option value="">All States</option>
                  {stateOptions.map(state => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <input
                  type="text"
                  placeholder="Enter city name"
                  value={filters.city}
                  onChange={(e) => handleFilterChange('city', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* Physical Characteristics */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Physical Characteristics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Weight (lbs)</label>
                <input
                  type="number"
                  placeholder="0"
                  value={filters.minWeight}
                  onChange={(e) => handleFilterChange('minWeight', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Weight (lbs)</label>
                <input
                  type="number"
                  placeholder="100"
                  value={filters.maxWeight}
                  onChange={(e) => handleFilterChange('maxWeight', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Age (years)</label>
                <input
                  type="number"
                  placeholder="0"
                  value={filters.minAge}
                  onChange={(e) => handleFilterChange('minAge', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Age (years)</label>
                <input
                  type="number"
                  placeholder="20"
                  value={filters.maxAge}
                  onChange={(e) => handleFilterChange('maxAge', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* Dog Details */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Dog Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                <select
                  value={filters.color}
                  onChange={(e) => handleFilterChange('color', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                >
                  <option value="">All Colors</option>
                  {colorOptions.map(color => (
                    <option key={color} value={color}>
                      {color.charAt(0).toUpperCase() + color.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                >
                  <option value="">All Statuses</option>
                  {statusOptions.map(status => (
                    <option key={status.value} value={status.value}>
                      {status.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Labrador Only</label>
                <select
                  value={filters.isLabrador}
                  onChange={(e) => handleFilterChange('isLabrador', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                >
                  <option value="">All Dogs</option>
                  <option value="true">Labradors Only</option>
                  <option value="false">Non-Labradors</option>
                </select>
              </div>
            </div>
          </div>

          {/* Shelter Information */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Shelter Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Shelter Name</label>
                <input
                  type="text"
                  placeholder="Enter shelter name"
                  value={filters.shelter}
                  onChange={(e) => handleFilterChange('shelter', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                <input
                  type="text"
                  placeholder="Enter tags (comma-separated)"
                  value={filters.tags}
                  onChange={(e) => handleFilterChange('tags', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* Date Filters */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Date Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entry Date From</label>
                <input
                  type="date"
                  value={filters.entryDateFrom}
                  onChange={(e) => handleFilterChange('entryDateFrom', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entry Date To</label>
                <input
                  type="date"
                  value={filters.entryDateTo}
                  onChange={(e) => handleFilterChange('entryDateTo', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* Popularity Filters */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Popularity</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Wag Count</label>
                <input
                  type="number"
                  placeholder="0"
                  value={filters.minWagCount}
                  onChange={(e) => handleFilterChange('minWagCount', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Growl Count</label>
                <input
                  type="number"
                  placeholder="10"
                  value={filters.maxGrowlCount}
                  onChange={(e) => handleFilterChange('maxGrowlCount', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* Sorting */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Sort Results</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
                <select
                  value={filters.sortBy}
                  onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                >
                  {sortOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
                <select
                  value={filters.sortOrder}
                  onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchAndFilter;
