import React, { useState, useEffect } from 'react';
import { X, Save, Upload } from 'lucide-react';
import { useUpdateDog } from '../hooks/useDogs';
import ImageUpload from './ImageUpload';

const EditDogModal = ({ dog, isOpen, onClose }) => {
  const [formData, setFormData] = useState({
    shelter_name: '',
    city: '',
    state: '',
    dog_name: '',
    dog_species: 'Labrador Retriever',
    shelter_entry_date: '',
    dog_description: '',
    dog_birthday: '',
    dog_weight: '',
    dog_color: '',
    dog_photo_url: '',
    status: 'available'
  });
  
  const [uploadedImage, setUploadedImage] = useState(null);
  const updateMutation = useUpdateDog();

  // Populate form when dog data changes
  useEffect(() => {
    if (dog) {
      setFormData({
        shelter_name: dog.shelter_name || '',
        city: dog.city || '',
        state: dog.state || '',
        dog_name: dog.dog_name || '',
        dog_species: dog.dog_species || 'Labrador Retriever',
        shelter_entry_date: dog.shelter_entry_date || '',
        dog_description: dog.dog_description || '',
        dog_birthday: dog.dog_birthday || '',
        dog_weight: dog.dog_weight || '',
        dog_color: dog.dog_color || '',
        dog_photo_url: dog.dog_photo_url || '',
        status: dog.status || 'available'
      });
    }
  }, [dog]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleImageUploaded = (imageData) => {
    setUploadedImage(imageData);
    if (imageData) {
      setFormData(prev => ({
        ...prev,
        dog_photo_url: imageData.original_url
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await updateMutation.mutateAsync({
        dogId: dog.dog_id,
        updates: formData
      });
      onClose();
    } catch (error) {
      // Error handling is done in the mutation
    }
  };

  if (!isOpen || !dog) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Edit {dog.dog_name}</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-8">
          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dog Name *
                </label>
                <input
                  type="text"
                  name="dog_name"
                  value={formData.dog_name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Species *
                </label>
                <select
                  name="dog_species"
                  value={formData.dog_species}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="Labrador Retriever">Labrador Retriever</option>
                  <option value="Labrador Mix">Labrador Mix</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color *
                </label>
                <input
                  type="text"
                  name="dog_color"
                  value={formData.dog_color}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., golden, black, chocolate"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Weight (lbs) *
                </label>
                <input
                  type="number"
                  name="dog_weight"
                  value={formData.dog_weight}
                  onChange={handleInputChange}
                  required
                  min="1"
                  max="200"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Birthday (MM/DD/YYYY) *
                </label>
                <input
                  type="text"
                  name="dog_birthday"
                  value={formData.dog_birthday}
                  onChange={handleInputChange}
                  required
                  placeholder="MM/DD/YYYY"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="available">Available</option>
                  <option value="pending">Pending</option>
                  <option value="adopted">Adopted</option>
                </select>
              </div>
            </div>
          </div>

          {/* Shelter Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Shelter Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Shelter Name *
                </label>
                <input
                  type="text"
                  name="shelter_name"
                  value={formData.shelter_name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Entry Date (MM/DD/YYYY) *
                </label>
                <input
                  type="text"
                  name="shelter_entry_date"
                  value={formData.shelter_entry_date}
                  onChange={handleInputChange}
                  required
                  placeholder="MM/DD/YYYY"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  City *
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  State *
                </label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  required
                  maxLength="2"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., CA, NY, TX"
                />
              </div>
            </div>
          </div>

          {/* Description and Photo */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Details</h3>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="dog_description"
                  value={formData.dog_description}
                  onChange={handleInputChange}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Tell us about this dog's personality, behavior, and what makes them special..."
                />
              </div>

              {/* Image Upload Component */}
              <ImageUpload
                onImageUploaded={handleImageUploaded}
                dogId={dog.dog_id}
              />

              {/* Manual URL input (optional fallback) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Or enter photo URL manually
                </label>
                <input
                  type="url"
                  name="dog_photo_url"
                  value={formData.dog_photo_url}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="https://example.com/dog-photo.jpg"
                  disabled={!!uploadedImage}
                />
                {uploadedImage && (
                  <p className="text-xs text-gray-500 mt-1">
                    URL automatically filled from uploaded image
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="btn-ghost"
              disabled={updateMutation.isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center"
              disabled={updateMutation.isLoading}
            >
              {updateMutation.isLoading ? (
                <>
                  <div className="spinner w-4 h-4 mr-2"></div>
                  Updating...
                </>
              ) : (
                <>
                  <Save size={18} className="mr-2" />
                  Update Dog
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditDogModal;
