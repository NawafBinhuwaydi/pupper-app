import React, { useState } from 'react';
import { Plus, Save, X } from 'lucide-react';
import { dogsApi, apiUtils } from '../services/api';
import { toast } from 'react-toastify';
import ImageUpload from './ImageUpload';

const AddDogForm = ({ onSuccess, onCancel }) => {
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
    dog_photo_url: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const [uploadedImage, setUploadedImage] = useState(null);

  const validateForm = () => {
    const newErrors = {};
    
    // Required fields
    const requiredFields = [
      'shelter_name', 'city', 'state', 'dog_name', 
      'shelter_entry_date', 'dog_birthday', 'dog_weight', 'dog_color'
    ];
    
    requiredFields.forEach(field => {
      if (!formData[field]?.trim()) {
        newErrors[field] = 'This field is required';
      }
    });
    
    // Validate weight
    if (formData.dog_weight && (isNaN(formData.dog_weight) || formData.dog_weight <= 0)) {
      newErrors.dog_weight = 'Weight must be a positive number';
    }
    
    // Validate dates
    if (formData.dog_birthday) {
      const dateRegex = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
      if (!dateRegex.test(formData.dog_birthday)) {
        newErrors.dog_birthday = 'Date must be in MM/DD/YYYY format';
      }
    }
    
    if (formData.shelter_entry_date) {
      const dateRegex = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
      if (!dateRegex.test(formData.shelter_entry_date)) {
        newErrors.shelter_entry_date = 'Date must be in MM/DD/YYYY format';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleImageUploaded = (imageData) => {
    setUploadedImage(imageData);
    if (imageData) {
      setFormData(prev => ({
        ...prev,
        dog_photo_url: imageData.original_url
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        dog_photo_url: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Convert weight to number
      const submitData = {
        ...formData,
        dog_weight: parseInt(formData.dog_weight),
        state: formData.state.toUpperCase()
      };
      
      const response = await dogsApi.createDog(submitData);
      
      toast.success(`${formData.dog_name} has been added successfully! 🐕`);
      
      if (onSuccess) {
        onSuccess(response.data);
      }
      
      // Reset form
      setFormData({
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
        dog_photo_url: ''
      });
      setUploadedImage(null);
      
    } catch (error) {
      const errorInfo = apiUtils.handleError(error);
      toast.error(`Failed to add dog: ${errorInfo.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
  ];

  const colors = [
    'black', 'brown', 'chocolate', 'yellow', 'golden', 'cream', 'white', 'silver'
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Plus className="text-primary-500 mr-3" size={24} />
          <h2 className="text-2xl font-bold text-gray-900">Add New Dog</h2>
        </div>
        {onCancel && (
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
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
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.dog_name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., Buddy"
              />
              {errors.dog_name && <p className="text-red-500 text-sm mt-1">{errors.dog_name}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Species
              </label>
              <select
                name="dog_species"
                value={formData.dog_species}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="Labrador Retriever">Labrador Retriever</option>
                <option value="Labrador Mix">Labrador Mix</option>
              </select>
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
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.dog_weight ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., 65"
                min="1"
              />
              {errors.dog_weight && <p className="text-red-500 text-sm mt-1">{errors.dog_weight}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Color *
              </label>
              <select
                name="dog_color"
                value={formData.dog_color}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.dog_color ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select color</option>
                {colors.map(color => (
                  <option key={color} value={color}>
                    {color.charAt(0).toUpperCase() + color.slice(1)}
                  </option>
                ))}
              </select>
              {errors.dog_color && <p className="text-red-500 text-sm mt-1">{errors.dog_color}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Birthday *
              </label>
              <input
                type="text"
                name="dog_birthday"
                value={formData.dog_birthday}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.dog_birthday ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="MM/DD/YYYY"
              />
              {errors.dog_birthday && <p className="text-red-500 text-sm mt-1">{errors.dog_birthday}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Shelter Entry Date *
              </label>
              <input
                type="text"
                name="shelter_entry_date"
                value={formData.shelter_entry_date}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.shelter_entry_date ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="MM/DD/YYYY"
              />
              {errors.shelter_entry_date && <p className="text-red-500 text-sm mt-1">{errors.shelter_entry_date}</p>}
            </div>
          </div>
        </div>

        {/* Shelter Information */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Shelter Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Shelter Name *
              </label>
              <input
                type="text"
                name="shelter_name"
                value={formData.shelter_name}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.shelter_name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., Happy Tails Shelter"
              />
              {errors.shelter_name && <p className="text-red-500 text-sm mt-1">{errors.shelter_name}</p>}
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
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.city ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., San Francisco"
              />
              {errors.city && <p className="text-red-500 text-sm mt-1">{errors.city}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                State *
              </label>
              <select
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.state ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select state</option>
                {states.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
              {errors.state && <p className="text-red-500 text-sm mt-1">{errors.state}</p>}
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
              dogId={formData.dog_name ? `new-${formData.dog_name.toLowerCase().replace(/\s+/g, '-')}` : ''}
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

        {/* Submit Button */}
        <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn-ghost"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary inline-flex items-center"
          >
            {isSubmitting ? (
              <>
                <div className="spinner w-4 h-4 mr-2"></div>
                Adding Dog...
              </>
            ) : (
              <>
                <Save className="mr-2" size={18} />
                Add Dog
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AddDogForm;
