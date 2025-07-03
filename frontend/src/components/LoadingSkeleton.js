import React from 'react';

const LoadingSkeleton = ({ count = 6 }) => {
  return (
    <div className="dog-grid">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="card">
          {/* Image skeleton */}
          <div className="aspect-square skeleton"></div>
          
          {/* Content skeleton */}
          <div className="p-4 space-y-3">
            {/* Title */}
            <div className="skeleton h-6 w-3/4"></div>
            
            {/* Location */}
            <div className="skeleton h-4 w-1/2"></div>
            
            {/* Details */}
            <div className="space-y-2">
              <div className="skeleton h-4 w-2/3"></div>
              <div className="skeleton h-4 w-1/2"></div>
            </div>
            
            {/* Description */}
            <div className="space-y-2">
              <div className="skeleton h-3 w-full"></div>
              <div className="skeleton h-3 w-4/5"></div>
            </div>
            
            {/* Buttons */}
            <div className="flex justify-between items-center pt-2">
              <div className="flex space-x-2">
                <div className="skeleton h-8 w-16 rounded-full"></div>
                <div className="skeleton h-8 w-16 rounded-full"></div>
              </div>
              <div className="skeleton h-4 w-20"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default LoadingSkeleton;
