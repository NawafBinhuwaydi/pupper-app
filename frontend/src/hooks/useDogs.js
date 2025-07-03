import { useQuery, useMutation, useQueryClient } from 'react-query';
import { dogsApi, apiUtils } from '../services/api';
import { toast } from 'react-toastify';
import { useState, useEffect } from 'react';

// Query keys
export const QUERY_KEYS = {
  DOGS: 'dogs',
  DOG: 'dog',
};

// Hook to fetch all dogs with filters
export const useDogs = (filters = {}, options = {}) => {
  return useQuery(
    [QUERY_KEYS.DOGS, filters],
    () => dogsApi.getDogs(filters),
    {
      staleTime: 2 * 60 * 1000, // 2 minutes
      cacheTime: 5 * 60 * 1000, // 5 minutes
      onError: (error) => {
        const errorInfo = apiUtils.handleError(error);
        if (process.env.NODE_ENV === 'development') {
          console.error('Dogs query error:', errorInfo);
        }
        // Only show toast for non-network errors to avoid spam
        if (errorInfo.status !== 0) {
          toast.error(`Failed to load dogs: ${errorInfo.message}`);
        }
      },
      ...options,
    }
  );
};

// Hook to fetch a single dog by ID
export const useDogDetails = (dogId, options = {}) => {
  return useQuery(
    [QUERY_KEYS.DOG, dogId],
    () => dogsApi.getDog(dogId),
    {
      enabled: !!dogId, // Only run query if dogId exists
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      onError: (error) => {
        const errorInfo = apiUtils.handleError(error);
        if (process.env.NODE_ENV === 'development') {
          console.error('Dog query error:', errorInfo);
        }
        if (errorInfo.status !== 0) {
          toast.error(`Failed to load dog details: ${errorInfo.message}`);
        }
      },
      ...options,
    }
  );
};

// Hook to vote on a dog
export const useVoteDog = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ dogId, voteData }) => dogsApi.voteDog(dogId, voteData),
    {
      onSuccess: (data, variables) => {
        // Invalidate and refetch dogs list
        queryClient.invalidateQueries([QUERY_KEYS.DOGS]);
        // Invalidate specific dog query
        queryClient.invalidateQueries([QUERY_KEYS.DOG, variables.dogId]);
        
        const voteType = variables.voteData.vote_type === 'wag' ? '👍' : '👎';
        toast.success(`${voteType} Vote recorded!`);
      },
      onError: (error) => {
        const errorInfo = apiUtils.handleError(error);
        toast.error(`Failed to record vote: ${errorInfo.message}`);
      },
    }
  );
};

// Hook to update a dog
export const useUpdateDog = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ dogId, updates }) => dogsApi.updateDog(dogId, updates),
    {
      onSuccess: (data, variables) => {
        // Invalidate and refetch dogs list
        queryClient.invalidateQueries([QUERY_KEYS.DOGS]);
        // Invalidate specific dog query
        queryClient.invalidateQueries([QUERY_KEYS.DOG, variables.dogId]);
        
        toast.success('Dog updated successfully! 🐕');
      },
      onError: (error) => {
        const errorInfo = apiUtils.handleError(error);
        toast.error(`Failed to update dog: ${errorInfo.message}`);
      },
    }
  );
};

// Hook to delete a dog
export const useDeleteDog = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (dogId) => dogsApi.deleteDog(dogId),
    {
      onSuccess: (data) => {
        // Invalidate and refetch dogs list
        queryClient.invalidateQueries([QUERY_KEYS.DOGS]);
        
        toast.success(`${data.data.dog_name} has been removed from the system`);
      },
      onError: (error) => {
        const errorInfo = apiUtils.handleError(error);
        toast.error(`Failed to delete dog: ${errorInfo.message}`);
      },
    }
  );
};

// Hook to manage favorites (using localStorage)
export const useFavorites = () => {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    const savedFavorites = localStorage.getItem('pupper-favorites');
    if (savedFavorites) {
      try {
        setFavorites(JSON.parse(savedFavorites));
      } catch (error) {
        console.error('Error parsing favorites from localStorage:', error);
        setFavorites([]);
      }
    }
  }, []);

  const toggleFavorite = (dogId) => {
    setFavorites(prev => {
      const newFavorites = prev.includes(dogId)
        ? prev.filter(id => id !== dogId)
        : [...prev, dogId];
      
      localStorage.setItem('pupper-favorites', JSON.stringify(newFavorites));
      return newFavorites;
    });
  };

  const isFavorite = (dogId) => {
    return favorites.includes(dogId);
  };

  const clearFavorites = () => {
    setFavorites([]);
    localStorage.removeItem('pupper-favorites');
  };

  return {
    favorites,
    toggleFavorite,
    isFavorite,
    clearFavorites,
  };
};
