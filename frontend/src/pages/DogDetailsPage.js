import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Heart, 
  MapPin, 
  Calendar, 
  Scale, 
  Palette, 
  Home,
  ThumbsUp,
  ThumbsDown,
  Share2,
  Edit,
  Trash2,
  AlertCircle
} from 'lucide-react';
import { useDogDetails, useVoteDog, useDeleteDog } from '../hooks/useDogs';
import { apiUtils } from '../services/api';
import { toast } from 'react-toastify';
import EditDogModal from '../components/EditDogModal';

const DogDetailsPage = () => {
  const { dogId } = useParams();
  const navigate = useNavigate();
  const [userId] = useState('demo-user-' + Math.random().toString(36).substr(2, 9));
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  const { data: dogData, isLoading, error, refetch } = useDogDetails(dogId);
  const voteMutation = useVoteDog();
  const deleteMutation = useDeleteDog();

  const dog = dogData?.data;

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(dogId);
      navigate('/'); // Redirect to home page after deletion
    } catch (error) {
      // Error handling is done in the mutation
    }
  };

  const handleVote = async (voteType) => {
    try {
      await voteMutation.mutateAsync({
        dogId,
        voteData: {
          user_id: userId,
          vote_type: voteType
        }
      });
    } catch (error) {
      // Error handling is done in the mutation
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Meet ${dog.dog_name}!`,
          text: `Check out this adorable ${dog.dog_species} looking for a home!`,
          url: window.location.href,
        });
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <Link
              to="/"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="mr-2" size={18} />
              Back to all dogs
            </Link>
          </div>
          
          {/* Loading skeleton */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="animate-pulse">
              <div className="aspect-video bg-gray-200"></div>
              <div className="p-8 space-y-4">
                <div className="bg-gray-200 h-8 w-1/3 rounded"></div>
                <div className="bg-gray-200 h-4 w-2/3 rounded"></div>
                <div className="bg-gray-200 h-4 w-1/2 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <Link
              to="/"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="mr-2" size={18} />
              Back to all dogs
            </Link>
          </div>
          
          <div className="text-center py-16">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Dog Not Found</h2>
            <p className="text-gray-600 mb-6">
              The dog you're looking for doesn't exist or may have been removed.
            </p>
            <button onClick={() => refetch()} className="btn-primary mr-4">
              Try Again
            </button>
            <Link to="/" className="btn-ghost">
              Browse All Dogs
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!dog) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Data Available</h2>
            <Link to="/" className="btn-primary">
              Back to Dogs
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const imageUrl = apiUtils.getImageUrl(dog, '400x400');
  const age = apiUtils.formatAge(dog.dog_age_years);
  const weight = apiUtils.formatWeight(dog.dog_weight);
  const statusColor = apiUtils.getStatusColor(dog.status);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="mr-2" size={18} />
            Back to all dogs
          </Link>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Image and Actions */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden sticky top-8">
              {/* Dog Image */}
              <div className="aspect-square relative">
                <img
                  src={imageUrl}
                  alt={dog.dog_name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.src = 'https://via.placeholder.com/400x400/e5e7eb/9ca3af?text=Dog+Photo';
                  }}
                />
                
                {/* Status Badge */}
                <div className="absolute top-4 left-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
                    {dog.status || 'Available'}
                  </span>
                </div>

                {/* Favorite Button */}
                <button className="absolute top-4 right-4 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-sm hover:bg-white transition-colors">
                  <Heart size={20} className="text-gray-600 hover:text-red-500" />
                </button>
              </div>

              {/* Action Buttons */}
              <div className="p-6 space-y-4">
                {/* Vote Buttons */}
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => handleVote('wag')}
                    disabled={voteMutation.isLoading}
                    className="btn-primary flex items-center justify-center"
                  >
                    <ThumbsUp size={18} className="mr-2" />
                    Wag ({dog.wag_count || 0})
                  </button>
                  <button
                    onClick={() => handleVote('growl')}
                    disabled={voteMutation.isLoading}
                    className="btn-ghost flex items-center justify-center"
                  >
                    <ThumbsDown size={18} className="mr-2" />
                    Growl ({dog.growl_count || 0})
                  </button>
                </div>

                {/* Share Button */}
                <button
                  onClick={handleShare}
                  className="w-full btn-outline flex items-center justify-center"
                >
                  <Share2 size={18} className="mr-2" />
                  Share {dog.dog_name}
                </button>

                {/* Admin Actions */}
                <div className="pt-4 border-t border-gray-200 space-y-2">
                  <button 
                    onClick={() => setShowEditModal(true)}
                    className="w-full btn-ghost text-left flex items-center"
                  >
                    <Edit size={16} className="mr-2" />
                    Edit Details
                  </button>
                  <button 
                    onClick={() => setShowDeleteConfirm(true)}
                    className="w-full btn-ghost text-left flex items-center text-red-600 hover:text-red-700"
                  >
                    <Trash2 size={16} className="mr-2" />
                    Remove Dog
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-4xl font-bold text-gray-900 mb-2">{dog.dog_name}</h1>
                  <p className="text-xl text-gray-600">{dog.dog_species}</p>
                </div>
                {dog.is_labrador && (
                  <span className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm font-medium">
                    Certified Lab 🐕
                  </span>
                )}
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Calendar className="w-5 h-5 text-gray-500 mx-auto mb-1" />
                  <p className="text-sm text-gray-600">Age</p>
                  <p className="font-semibold">{age}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Scale className="w-5 h-5 text-gray-500 mx-auto mb-1" />
                  <p className="text-sm text-gray-600">Weight</p>
                  <p className="font-semibold">{weight}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Palette className="w-5 h-5 text-gray-500 mx-auto mb-1" />
                  <p className="text-sm text-gray-600">Color</p>
                  <p className="font-semibold capitalize">{dog.dog_color}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Home className="w-5 h-5 text-gray-500 mx-auto mb-1" />
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="font-semibold capitalize">{dog.status || 'Available'}</p>
                </div>
              </div>

              {/* Location */}
              <div className="flex items-center text-gray-600 mb-4">
                <MapPin size={18} className="mr-2" />
                <span>{dog.city}, {dog.state}</span>
              </div>
            </div>

            {/* Description */}
            {dog.dog_description && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">About {dog.dog_name}</h2>
                <p className="text-gray-700 leading-relaxed">{dog.dog_description}</p>
              </div>
            )}

            {/* Shelter Information */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Shelter Information</h2>
              <div className="space-y-3">
                <div>
                  <span className="font-medium text-gray-900">Shelter:</span>
                  <span className="ml-2 text-gray-700">{dog.shelter_name}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-900">Location:</span>
                  <span className="ml-2 text-gray-700">{dog.city}, {dog.state}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-900">Entry Date:</span>
                  <span className="ml-2 text-gray-700">{dog.shelter_entry_date}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-900">Birthday:</span>
                  <span className="ml-2 text-gray-700">{dog.dog_birthday}</span>
                </div>
              </div>
            </div>

            {/* Additional Details */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Additional Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Physical Traits</h3>
                  <ul className="space-y-1 text-gray-700">
                    <li>Species: {dog.dog_species}</li>
                    <li>Color: {dog.dog_color}</li>
                    <li>Weight: {weight}</li>
                    <li>Age: {age}</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Adoption Info</h3>
                  <ul className="space-y-1 text-gray-700">
                    <li>Status: {dog.status || 'Available'}</li>
                    <li>Wag Count: {dog.wag_count || 0}</li>
                    <li>Growl Count: {dog.growl_count || 0}</li>
                    <li>Added: {new Date(dog.created_at).toLocaleDateString()}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <EditDogModal
        dog={dog}
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Delete {dog.dog_name}?</h2>
              <p className="text-gray-600 mb-6">
                This action cannot be undone. {dog.dog_name} will be permanently removed from the system.
              </p>
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 btn-ghost"
                  disabled={deleteMutation.isLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center"
                  disabled={deleteMutation.isLoading}
                >
                  {deleteMutation.isLoading ? (
                    <>
                      <div className="spinner w-4 h-4 mr-2"></div>
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 size={16} className="mr-2" />
                      Delete
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DogDetailsPage;
