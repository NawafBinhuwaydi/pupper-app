import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import SearchAndFilter from '../components/SearchAndFilter';
import SearchResults from '../components/SearchResults';
import Pagination from '../components/Pagination';
import { useDogs } from '../hooks/useDogs';

const SearchPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Parse URL parameters
  const urlParams = new URLSearchParams(location.search);
  const initialFilters = Object.fromEntries(urlParams.entries());
  
  const [currentPage, setCurrentPage] = useState(parseInt(initialFilters.page) || 1);
  const [itemsPerPage, setItemsPerPage] = useState(parseInt(initialFilters.limit) || 20);
  const [filters, setFilters] = useState(initialFilters);

  // Fetch dogs with current filters
  const { data, isLoading, error, refetch } = useDogs({
    ...filters,
    page: currentPage,
    limit: itemsPerPage
  });

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== '') {
        params.set(key, value);
      }
    });
    
    if (currentPage > 1) {
      params.set('page', currentPage.toString());
    }
    
    if (itemsPerPage !== 20) {
      params.set('limit', itemsPerPage.toString());
    }

    const newSearch = params.toString();
    const newUrl = newSearch ? `${location.pathname}?${newSearch}` : location.pathname;
    
    if (newUrl !== `${location.pathname}${location.search}`) {
      navigate(newUrl, { replace: true });
    }
  }, [filters, currentPage, itemsPerPage, location.pathname, location.search, navigate]);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (newLimit) => {
    setItemsPerPage(newLimit);
    setCurrentPage(1); // Reset to first page when limit changes
  };

  const dogs = data?.data?.dogs || [];
  const pagination = data?.data?.pagination || {};
  const appliedFilters = data?.data?.filters_applied || {};
  const sortInfo = data?.data?.sort || {};

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Find Your Perfect Companion
          </h1>
          <p className="text-gray-600">
            Search and filter through our available dogs to find your new best friend.
          </p>
        </div>

        {/* Search and Filter Component */}
        <SearchAndFilter
          onFiltersChange={handleFiltersChange}
          initialFilters={filters}
          isLoading={isLoading}
        />

        {/* Search Results */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <SearchResults
            dogs={dogs}
            isLoading={isLoading}
            error={error}
            totalResults={pagination.total_items || 0}
            appliedFilters={appliedFilters}
            searchQuery={filters.search || ''}
            onRetry={refetch}
          />

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="mt-8">
              <Pagination
                currentPage={pagination.current_page || 1}
                totalPages={pagination.total_pages || 1}
                totalItems={pagination.total_items || 0}
                itemsPerPage={pagination.per_page || itemsPerPage}
                onPageChange={handlePageChange}
                onItemsPerPageChange={handleItemsPerPageChange}
                isLoading={isLoading}
              />
            </div>
          )}
        </div>

        {/* Search Tips */}
        {!isLoading && dogs.length === 0 && !error && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-blue-900 mb-3">
              Search Tips
            </h3>
            <ul className="text-blue-800 space-y-2 text-sm">
              <li>• Use keywords like dog names, breeds, colors, or shelter names</li>
              <li>• Try broader search terms if you're not finding results</li>
              <li>• Use the advanced filters to narrow down by specific criteria</li>
              <li>• Check different status options (available, adopted, pending)</li>
              <li>• Adjust age and weight ranges to see more options</li>
            </ul>
          </div>
        )}

        {/* Debug Info (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 bg-gray-100 border border-gray-300 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Debug Info</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Current Page: {currentPage}</div>
              <div>Items Per Page: {itemsPerPage}</div>
              <div>Total Results: {pagination.total_items || 0}</div>
              <div>Total Pages: {pagination.total_pages || 0}</div>
              <div>Applied Filters: {JSON.stringify(appliedFilters, null, 2)}</div>
              <div>Sort: {JSON.stringify(sortInfo, null, 2)}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
