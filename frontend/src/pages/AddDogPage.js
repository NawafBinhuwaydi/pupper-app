import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import AddDogForm from '../components/AddDogForm';
import { useQueryClient } from 'react-query';
import { QUERY_KEYS } from '../hooks/useDogs';

const AddDogPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const handleSuccess = (newDog) => {
    // Invalidate dogs query to refresh the list
    queryClient.invalidateQueries([QUERY_KEYS.DOGS]);
    
    // Navigate back to home page
    navigate('/', { 
      state: { 
        message: `${newDog.dog_name} has been added successfully!` 
      } 
    });
  };

  const handleCancel = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Navigation */}
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="mr-2" size={18} />
            Back to all dogs
          </Link>
        </div>

        {/* Add Dog Form */}
        <AddDogForm 
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
};

export default AddDogPage;
