import axios from 'axios';

// Use proxy in development, direct API in production
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? '/api'  // Use proxy in development
  : (process.env.REACT_APP_API_URL || 'https://bj9jbp1rgf.execute-api.us-east-1.amazonaws.com/prod');

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for error handling
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log errors in development only
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// Dogs API
export const dogsApi = {
  // Get all dogs with optional filters
  getDogs: async (filters = {}) => {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value);
      }
    });
    
    const queryString = params.toString();
    const url = queryString ? `/dogs?${queryString}` : '/dogs';
    
    const response = await api.get(url);
    return response.data;
  },

  // Get single dog by ID
  getDog: async (dogId) => {
    const response = await api.get(`/dogs/${dogId}`);
    return response.data;
  },

  // Create a new dog
  createDog: async (dogData) => {
    const response = await api.post('/dogs', dogData);
    return response.data;
  },

  // Update a dog
  updateDog: async (dogId, updates) => {
    const response = await api.put(`/dogs/${dogId}`, updates);
    return response.data;
  },

  // Delete a dog
  deleteDog: async (dogId) => {
    const response = await api.delete(`/dogs/${dogId}`);
    return response.data;
  },

  // Vote on dog
  voteDog: async (dogId, voteData) => {
    const response = await api.post(`/dogs/${dogId}/vote`, voteData);
    return response.data;
  },
};

// Images API
export const imagesApi = {
  // Upload an image
  uploadImage: async (imageData) => {
    const response = await api.post('/images', imageData);
    return response.data;
  },

  // Get image metadata
  getImage: async (imageId) => {
    const response = await api.get(`/images/${imageId}`);
    return response.data;
  },
};

// Utility functions
export const apiUtils = {
  // Handle API errors
  handleError: (error) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.error || 
                     error.response.data?.message || 
                     `Server error (${error.response.status})`;
      return {
        message,
        status: error.response.status,
        data: error.response.data,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        message: 'Unable to connect to server. Please try again.',
        status: 0,
        data: null,
      };
    } else {
      // Something else happened
      return {
        message: error.message || 'An unexpected error occurred',
        status: 0,
        data: null,
      };
    }
  },

  // Format image URL with fallback
  getImageUrl: (dog, size = '400x400') => {
    if (dog.dog_photo_400x400_url && size === '400x400') {
      return dog.dog_photo_400x400_url;
    }
    if (dog.dog_photo_50x50_url && size === '50x50') {
      return dog.dog_photo_50x50_url;
    }
    if (dog.dog_photo_url) {
      return dog.dog_photo_url;
    }
    return 'https://via.placeholder.com/400x400/e5e7eb/9ca3af?text=Dog+Photo';
  },

  // Format dog age
  formatAge: (ageYears) => {
    if (!ageYears) return 'Unknown age';
    
    const years = Math.floor(ageYears);
    const months = Math.round((ageYears - years) * 12);
    
    if (years === 0) {
      return `${months} month${months !== 1 ? 's' : ''} old`;
    } else if (months === 0) {
      return `${years} year${years !== 1 ? 's' : ''} old`;
    } else {
      return `${years} year${years !== 1 ? 's' : ''}, ${months} month${months !== 1 ? 's' : ''} old`;
    }
  },

  // Format weight
  formatWeight: (weight) => {
    if (!weight) return 'Unknown weight';
    return `${weight} lbs`;
  },

  // Get status badge color
  getStatusColor: (status) => {
    switch (status?.toLowerCase()) {
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'adopted':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  },
};

export default api;
