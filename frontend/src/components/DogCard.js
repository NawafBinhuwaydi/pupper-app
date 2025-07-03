import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, MapPin, Calendar, Scale, ThumbsUp, ThumbsDown, Edit } from 'lucide-react';
import { apiUtils } from '../services/api';
import { useFavorites, useVoteDog } from '../hooks/useDogs';
import EditDogModal from './EditDogModal';

const DogCard = ({ dog }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const { isFavorite, toggleFavorite } = useFavorites();
  const voteMutation = useVoteDog();

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(true);
  };

  const handleFavoriteClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleFavorite(dog.dog_id);
  };

  const handleVote = (e, voteType) => {
    e.preventDefault();
    e.stopPropagation();
    
    const userId = 'demo-user-123';
    
    voteMutation.mutate({
      dogId: dog.dog_id,
      voteData: {
        user_id: userId,
        vote_type: voteType,
      },
    });
  };

  const thumbnailUrl = apiUtils.getImageUrl(dog, '400x400');
  const isLiked = isFavorite(dog.dog_id);

  return (
    <div className="card card-hover group">
      <Link to={`/dogs/${dog.dog_id}`} className="block">
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden">
          {!imageLoaded && (
            <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
              <div className="text-gray-400 text-4xl">🐕</div>
            </div>
          )}
          
          {!imageError ? (
            <img
              src={thumbnailUrl}
              alt={`${dog.dog_name || 'Dog'} - Available for adoption`}
              className={`w-full h-full object-cover transition-all duration-300 group-hover:scale-105 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={handleImageLoad}
              onError={handleImageError}
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full bg-gray-200 flex items-center justify-center">
              <div className="text-gray-400 text-6xl">🐕</div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="absolute top-3 right-3 flex space-x-2">
            {/* Quick Edit Button */}
            <button
              onClick={(e) => {
                e.preventDefault();
                setShowEditModal(true);
              }}
              className="p-2 bg-white/80 text-gray-600 hover:bg-white hover:text-blue-500 rounded-full transition-all duration-200 backdrop-blur-sm"
              title="Quick Edit"
            >
              <Edit size={16} />
            </button>

            {/* Favorite Button */}
            <button
              onClick={handleFavoriteClick}
              className={`p-2 rounded-full transition-all duration-200 ${
                isLiked
                  ? 'bg-red-500 text-white shadow-lg'
                  : 'bg-white/80 text-gray-600 hover:bg-white hover:text-red-500'
              } backdrop-blur-sm`}
              aria-label={isLiked ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart
                size={18}
                className={`transition-all duration-200 ${
                  isLiked ? 'fill-current heart-bounce' : ''
                }`}
              />
            </button>
          </div>

          {/* Status Badge */}
          <div className="absolute top-3 left-3">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${apiUtils.getStatusColor(dog.status)}`}>
              {dog.status || 'Available'}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Name and Location */}
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
              {dog.dog_name || 'Adorable Labrador'}
            </h3>
            <div className="flex items-center text-sm text-gray-600">
              <MapPin size={14} className="mr-1" />
              <span>{dog.city}, {dog.state}</span>
            </div>
          </div>

          {/* Details */}
          <div className="space-y-2 mb-4">
            <div className="flex items-center text-sm text-gray-600">
              <Calendar size={14} className="mr-2" />
              <span>{apiUtils.formatAge(dog.dog_age_years)}</span>
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <Scale size={14} className="mr-2" />
              <span>{apiUtils.formatWeight(dog.dog_weight)}</span>
            </div>
          </div>

          {/* Description */}
          {dog.dog_description && (
            <p className="text-sm text-gray-600 mb-4 line-clamp-2">
              {dog.dog_description}
            </p>
          )}

          {/* Vote Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <button
                onClick={(e) => handleVote(e, 'wag')}
                disabled={voteMutation.isLoading}
                className="flex items-center justify-center p-2 rounded-full bg-green-100 text-green-600 hover:bg-green-200 transition-colors"
                aria-label="Give this dog a wag"
              >
                <ThumbsUp size={16} />
                <span className="ml-1 text-sm font-medium">
                  {dog.wag_count || 0}
                </span>
              </button>
              
              <button
                onClick={(e) => handleVote(e, 'growl')}
                disabled={voteMutation.isLoading}
                className="flex items-center justify-center p-2 rounded-full bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                aria-label="Give this dog a growl"
              >
                <ThumbsDown size={16} />
                <span className="ml-1 text-sm font-medium">
                  {dog.growl_count || 0}
                </span>
              </button>
            </div>

            {/* Shelter Info */}
            <div className="text-xs text-gray-500">
              {dog.shelter_name}
            </div>
          </div>
        </div>
      </Link>

      {/* Edit Modal */}
      <EditDogModal
        dog={dog}
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
      />
    </div>
  );
};

export default DogCard;
