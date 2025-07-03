import React from 'react';
import { Heart, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useFavorites } from '../hooks/useDogs';

const FavoritesPage = () => {
  const { favorites } = useFavorites();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Heart className="text-red-500 mr-3" size={32} />
            <h1 className="text-3xl font-bold text-gray-900">My Favorites</h1>
          </div>
          <p className="text-gray-600">
            Dogs you've marked as favorites will appear here
          </p>
        </div>

        {favorites.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-6">💔</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              No favorites yet
            </h2>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Start browsing dogs and click the heart icon to add them to your favorites.
            </p>
            <Link to="/" className="btn-primary inline-flex items-center">
              Browse Dogs
              <ArrowRight className="ml-2" size={18} />
            </Link>
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">❤️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {favorites.length} Favorite{favorites.length !== 1 ? 's' : ''}
            </h2>
            <p className="text-gray-600">
              Your favorite dogs will be displayed here when the backend is fully functional.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FavoritesPage;
