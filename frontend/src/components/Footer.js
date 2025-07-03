import React from 'react';
import { Heart } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">🐕</span>
            </div>
            <span className="text-xl font-bold">Pupper</span>
          </div>
          <p className="text-gray-300 mb-4">
            Helping Labrador Retrievers find their forever homes
          </p>
          <div className="flex items-center justify-center space-x-1 text-sm text-gray-400">
            <span>Made with</span>
            <Heart size={16} className="text-red-500 fill-current" />
            <span>for our furry friends</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
