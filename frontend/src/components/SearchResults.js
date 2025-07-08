import React from 'react';
import { AlertCircle, Search } from 'lucide-react';
import DogCard from './DogCard';
import LoadingSkeleton from './LoadingSkeleton';

const SearchResults = ({ 
  dogs = [], 
  isLoading = false, 
  error = null, 
  totalResults = 0,
  appliedFilters = {},
  searchQuery = '',
  onRetry = null 
}) => {
  // Loading state
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Something went wrong
        </h3>
        <p className="text-gray-600 mb-4">
          {error.message || 'Failed to load search results'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  // No results state
  if (!dogs || dogs.length === 0) {
    const hasFilters = Object.keys(appliedFilters).length > 0 || searchQuery;
    
    return (
      <div className="text-center py-12">
        <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {hasFilters ? 'No dogs match your search' : 'No dogs available'}
        </h3>
        <p className="text-gray-600 mb-4">
          {hasFilters 
            ? 'Try adjusting your search criteria or filters to find more results.'
            : 'There are currently no dogs in the system.'
          }
        </p>
        {hasFilters && (
          <div className="text-sm text-gray-500">
            <p>Current search criteria:</p>
            <ul className="mt-2 space-y-1">
              {searchQuery && (
                <li>Search: "{searchQuery}"</li>
              )}
              {Object.entries(appliedFilters).map(([key, value]) => {
                if (!value || key === 'sort_by' || key === 'sort_order') return null;
                
                const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                return (
                  <li key={key}>
                    {displayKey}: {value}
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // Results found
  return (
    <div>
      {/* Results summary */}
      <div className="mb-6 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          {totalResults === 1 
            ? '1 dog found'
            : `${totalResults.toLocaleString()} dogs found`
          }
          {searchQuery && (
            <span> for "{searchQuery}"</span>
          )}
        </div>
        
        {/* Active filters summary */}
        {Object.keys(appliedFilters).length > 0 && (
          <div className="text-sm text-gray-500">
            {Object.keys(appliedFilters).filter(key => 
              appliedFilters[key] && key !== 'sort_by' && key !== 'sort_order'
            ).length} filter{Object.keys(appliedFilters).filter(key => 
              appliedFilters[key] && key !== 'sort_by' && key !== 'sort_order'
            ).length !== 1 ? 's' : ''} applied
          </div>
        )}
      </div>

      {/* Results grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {dogs.map((dog) => (
          <DogCard 
            key={dog.dog_id} 
            dog={dog}
            searchQuery={searchQuery}
          />
        ))}
      </div>
    </div>
  );
};

export default SearchResults;
