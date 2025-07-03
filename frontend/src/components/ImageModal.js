import React, { useState, useEffect } from 'react';
import { X, Download, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';
import { apiUtils } from '../services/api';

const ImageModal = ({ isOpen, onClose, dog, initialImageSize = 'original' }) => {
  const [currentImageSize, setCurrentImageSize] = useState(initialImageSize);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setImageLoaded(false);
      setImageError(false);
      setZoom(1);
      setRotation(0);
      setCurrentImageSize(initialImageSize);
    }
  }, [isOpen, initialImageSize]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !dog) return null;

  const availableSizes = apiUtils.getImageSizes(dog);
  const currentImageUrl = availableSizes[currentImageSize] || availableSizes.original || apiUtils.getImageUrl(dog);

  const handleImageLoad = () => {
    setImageLoaded(true);
    setImageError(false);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(true);
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(currentImageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${dog.dog_name || 'dog'}-${currentImageSize}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleBackdropClick}>
      <div className="modal-content w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {dog.dog_name || 'Dog Photo'}
            </h2>
            <p className="text-sm text-gray-600">
              {dog.shelter_name} • {dog.city}, {dog.state}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Size Selector */}
            {Object.keys(availableSizes).length > 1 && (
              <select
                value={currentImageSize}
                onChange={(e) => setCurrentImageSize(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {Object.entries(availableSizes).map(([size, url]) => (
                  <option key={size} value={size}>
                    {size === 'original' ? 'Original' : size}
                  </option>
                ))}
              </select>
            )}

            {/* Controls */}
            <button
              onClick={handleZoomOut}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Zoom out"
            >
              <ZoomOut size={18} />
            </button>
            
            <span className="text-sm text-gray-600 min-w-[3rem] text-center">
              {Math.round(zoom * 100)}%
            </span>
            
            <button
              onClick={handleZoomIn}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Zoom in"
            >
              <ZoomIn size={18} />
            </button>
            
            <button
              onClick={handleRotate}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Rotate image"
            >
              <RotateCw size={18} />
            </button>
            
            <button
              onClick={handleDownload}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Download image"
            >
              <Download size={18} />
            </button>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Close modal"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Image Container */}
        <div className="flex-1 overflow-auto bg-gray-50 flex items-center justify-center p-4">
          <div className="relative max-w-full max-h-full">
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="spinner w-8 h-8"></div>
              </div>
            )}
            
            {!imageError ? (
              <img
                src={currentImageUrl}
                alt={`${dog.dog_name || 'Dog'} - Full size`}
                className={`max-w-full max-h-full object-contain transition-all duration-300 ${
                  imageLoaded ? 'opacity-100' : 'opacity-0'
                }`}
                style={{
                  transform: `scale(${zoom}) rotate(${rotation}deg)`,
                  transformOrigin: 'center',
                }}
                onLoad={handleImageLoad}
                onError={handleImageError}
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-gray-500">
                <div className="text-6xl mb-4">🐕</div>
                <p>Image could not be loaded</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer with Image Info */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-medium">Size:</span> {currentImageSize}
              {currentImageSize !== 'original' && (
                <span className="ml-2">
                  <span className="font-medium">Dimensions:</span> {currentImageSize}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <span>
                <span className="font-medium">Age:</span> {apiUtils.formatAge(dog.dog_age_years)}
              </span>
              <span>
                <span className="font-medium">Weight:</span> {apiUtils.formatWeight(dog.dog_weight)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageModal;
