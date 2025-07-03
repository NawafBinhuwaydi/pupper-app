import React from 'react';
import { Link } from 'react-router-dom';
import { Home, Search, ArrowLeft } from 'lucide-react';

const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center px-4">
        <div className="mb-8">
          <div className="text-9xl mb-4">🐕</div>
          <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
          <h2 className="text-3xl font-bold text-gray-700 mb-2">
            Oops! This page went to the dog park
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
            The page you're looking for doesn't exist.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/" className="btn-primary inline-flex items-center">
            <Home className="mr-2" size={18} />
            Go Home
          </Link>
          
          <Link to="/search" className="btn-outline inline-flex items-center">
            <Search className="mr-2" size={18} />
            Search Dogs
          </Link>
          
          <button 
            onClick={() => window.history.back()} 
            className="btn-ghost inline-flex items-center"
          >
            <ArrowLeft className="mr-2" size={18} />
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
