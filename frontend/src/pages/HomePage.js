import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Heart, Filter, RefreshCw, Plus } from 'lucide-react';
import { useDogs } from '../hooks/useDogs';
import DogCard from '../components/DogCard';

const LoadingSkeleton = () => (
  <div className="dog-grid">
    {Array.from({ length: 6 }).map((_, index) => (
      <div key={index} className="card animate-pulse">
        <div className="aspect-square bg-gray-200"></div>
        <div className="p-4 space-y-3">
          <div className="bg-gray-200 h-6 w-3/4 rounded"></div>
          <div className="bg-gray-200 h-4 w-1/2 rounded"></div>
          <div className="space-y-2">
            <div className="bg-gray-200 h-4 w-2/3 rounded"></div>
            <div className="bg-gray-200 h-4 w-1/2 rounded"></div>
          </div>
          <div className="flex justify-between">
            <div className="bg-gray-200 h-8 w-16 rounded-full"></div>
            <div className="bg-gray-200 h-8 w-16 rounded-full"></div>
          </div>
        </div>
      </div>
    ))}
  </div>
);

const HomePage = () => {
  const [filters, setFilters] = useState({});
  const [showFilters, setShowFilters] = useState(false);
  
  const { data, isLoading, error, refetch, isFetching } = useDogs(filters);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const hasActiveFilters = Object.keys(filters).some(key => filters[key]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-6xl mb-4">😢</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Unable to load dogs</h2>
          <p className="text-gray-600 mb-6">
            We're having trouble connecting to our database. Please try again in a moment.
          </p>
          <button onClick={() => refetch()} className="btn-primary">
            <RefreshCw className="mr-2" size={18} />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-4">
              Find Your Perfect
              <span className="block text-yellow-300">Labrador Companion</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              Discover amazing Labrador Retrievers looking for their forever homes
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/search" className="btn-secondary">
                <Search className="mr-2" size={20} />
                Advanced Search
              </Link>
              <Link to="/add-dog" className="btn-primary">
                <Plus className="mr-2" size={20} />
                Add Dog
              </Link>
              <Link to="/favorites" className="btn-outline bg-white/10 border-white text-white hover:bg-white hover:text-primary-600">
                <Heart className="mr-2" size={20} />
                View Favorites
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters Bar */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center space-x-4">
              <h2 className="text-2xl font-bold text-gray-900">
                Available Dogs
              </h2>
              {data?.data && (
                <span className="text-gray-600">
                  ({data.data.count} {data.data.count === 1 ? 'dog' : 'dogs'})
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <Link to="/add-dog" className="btn-primary">
                <Plus size={18} className="mr-2" />
                Add Dog
              </Link>
              
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`btn-ghost ${showFilters ? 'bg-gray-100' : ''}`}
              >
                <Filter size={18} className="mr-2" />
                Filters
                {hasActiveFilters && (
                  <span className="ml-2 bg-primary-500 text-white text-xs px-2 py-1 rounded-full">
                    {Object.keys(filters).filter(key => filters[key]).length}
                  </span>
                )}
              </button>
              
              <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="btn-ghost"
              >
                <RefreshCw size={18} className={`mr-2 ${isFetching ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="mt-4 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State
                  </label>
                  <select
                    value={filters.state || ''}
                    onChange={(e) => handleFilterChange('state', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All States</option>
                    <option value="CA">California</option>
                    <option value="TX">Texas</option>
                    <option value="FL">Florida</option>
                    <option value="NY">New York</option>
                    <option value="VA">Virginia</option>
                    <option value="WA">Washington</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Weight (lbs)
                  </label>
                  <input
                    type="number"
                    value={filters.max_weight || ''}
                    onChange={(e) => handleFilterChange('max_weight', e.target.value)}
                    placeholder="e.g. 80"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Color
                  </label>
                  <select
                    value={filters.color || ''}
                    onChange={(e) => handleFilterChange('color', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All Colors</option>
                    <option value="black">Black</option>
                    <option value="brown">Brown</option>
                    <option value="yellow">Yellow</option>
                    <option value="chocolate">Chocolate</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Age (years)
                  </label>
                  <input
                    type="number"
                    value={filters.max_age || ''}
                    onChange={(e) => handleFilterChange('max_age', e.target.value)}
                    placeholder="e.g. 5"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              {hasActiveFilters && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={clearFilters}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Clear all filters
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Dogs Grid */}
        {isLoading ? (
          <LoadingSkeleton />
        ) : data?.data?.dogs?.length > 0 ? (
          <div className="dog-grid">
            {data.data.dogs.map((dog) => (
              <DogCard key={dog.dog_id} dog={dog} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🐕</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No dogs found</h3>
            <p className="text-gray-600 mb-4">
              {hasActiveFilters 
                ? "Try adjusting your filters to see more results."
                : "We're working on adding adorable Labradors to our database. Check back soon!"
              }
            </p>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="btn-primary">
                Clear Filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
