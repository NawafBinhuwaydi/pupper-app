import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const [quickSearch, setQuickSearch] = useState('');
  const [filters, setFilters] = useState({ status: 'available', limit: 12 });
  const [showFilters, setShowFilters] = useState(false);
  
  const { data, isLoading, error, refetch, isFetching } = useDogs(filters);

  const handleQuickSearch = (e) => {
    e.preventDefault();
    if (quickSearch.trim()) {
      navigate(`/search?search=${encodeURIComponent(quickSearch.trim())}`);
    } else {
      navigate('/search');
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const clearFilters = () => {
    setFilters({ status: 'available', limit: 12 });
  };

  const hasActiveFilters = Object.keys(filters).some(key => 
    filters[key] && key !== 'status' && key !== 'limit'
  );

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
            
            {/* Quick Search Bar */}
            <div className="max-w-2xl mx-auto mb-8">
              <form onSubmit={handleQuickSearch} className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Quick search: dog names, breeds, locations..."
                  value={quickSearch}
                  onChange={(e) => setQuickSearch(e.target.value)}
                  className="block w-full pl-10 pr-20 py-4 border border-transparent rounded-lg focus:ring-2 focus:ring-white focus:border-white text-gray-900 text-lg placeholder-gray-500"
                />
                <div className="absolute inset-y-0 right-0 flex items-center">
                  <button
                    type="submit"
                    className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-r-lg transition-colors font-medium"
                  >
                    Search
                  </button>
                </div>
              </form>
            </div>
            
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
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Filter size={16} />
                  Quick Filters
                </button>
                
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    <RefreshCw size={16} />
                    Clear
                  </button>
                )}
              </div>
              
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">
                  {data?.data?.pagination?.total_items || 0} dogs available
                </span>
                <button
                  onClick={() => refetch()}
                  disabled={isFetching}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50"
                >
                  <RefreshCw size={16} className={isFetching ? 'animate-spin' : ''} />
                  Refresh
                </button>
              </div>
            </div>
            
            {/* Quick Filters */}
            {showFilters && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                    <select
                      value={filters.state || ''}
                      onChange={(e) => handleFilterChange('state', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">All States</option>
                      <option value="CA">California</option>
                      <option value="TX">Texas</option>
                      <option value="FL">Florida</option>
                      <option value="NY">New York</option>
                      <option value="VA">Virginia</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Weight</label>
                    <select
                      value={filters.max_weight || ''}
                      onChange={(e) => handleFilterChange('max_weight', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">Any Weight</option>
                      <option value="30">Under 30 lbs</option>
                      <option value="50">Under 50 lbs</option>
                      <option value="70">Under 70 lbs</option>
                      <option value="100">Under 100 lbs</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Age Range</label>
                    <select
                      value={filters.max_age || ''}
                      onChange={(e) => handleFilterChange('max_age', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">Any Age</option>
                      <option value="1">Puppies (Under 1 year)</option>
                      <option value="3">Young (Under 3 years)</option>
                      <option value="7">Adult (Under 7 years)</option>
                      <option value="15">Senior (Under 15 years)</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                    <select
                      value={filters.color || ''}
                      onChange={(e) => handleFilterChange('color', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">All Colors</option>
                      <option value="black">Black</option>
                      <option value="brown">Brown</option>
                      <option value="yellow">Yellow</option>
                      <option value="chocolate">Chocolate</option>
                      <option value="golden">Golden</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Dogs Grid */}
        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {data?.data?.dogs?.map((dog) => (
                <DogCard key={dog.dog_id} dog={dog} />
              ))}
            </div>
            
            {/* Show More Button */}
            {data?.data?.dogs?.length > 0 && data?.data?.pagination?.has_next && (
              <div className="text-center">
                <Link
                  to="/search"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 transition-colors"
                >
                  View All Dogs
                  <Search className="ml-2" size={20} />
                </Link>
              </div>
            )}
            
            {data?.data?.dogs?.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🐕</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No dogs match your criteria</h3>
                <p className="text-gray-600 mb-4">
                  Try adjusting your filters or check back later for new arrivals.
                </p>
                <Link to="/search" className="btn-primary">
                  <Search className="mr-2" size={18} />
                  Advanced Search
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default HomePage;
