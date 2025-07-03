import React, { useState, useRef } from 'react';
import { Upload, X, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { imagesApi, apiUtils } from '../services/api';
import { toast } from 'react-toastify';

const ImageUpload = ({ onImageUploaded, dogId = '', className = '' }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleFile = (file) => {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please select a valid image file (JPEG, PNG, or WebP)');
      return;
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      toast.error('Image size must be less than 50MB');
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
    };
    reader.readAsDataURL(file);

    // Upload the file
    uploadFile(file);
  };

  const uploadFile = async (file) => {
    setIsUploading(true);
    
    try {
      // Convert file to base64
      const base64 = await fileToBase64(file);
      
      // Prepare upload data
      const uploadData = {
        image_data: base64,
        content_type: file.type,
        dog_id: dogId,
        description: `Uploaded image for ${dogId ? 'dog' : 'new dog'}`
      };

      // Upload to API
      const response = await imagesApi.uploadImage(uploadData);
      
      setUploadedImage(response.data);
      toast.success('Image uploaded successfully! 📸');
      
      // Notify parent component
      if (onImageUploaded) {
        onImageUploaded(response.data);
      }
      
    } catch (error) {
      const errorInfo = apiUtils.handleError(error);
      toast.error(`Failed to upload image: ${errorInfo.message}`);
      setPreview(null);
    } finally {
      setIsUploading(false);
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const clearImage = () => {
    setPreview(null);
    setUploadedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (onImageUploaded) {
      onImageUploaded(null);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Dog Photo
      </label>
      
      {!preview && !uploadedImage ? (
        // Upload area
        <div
          onClick={openFileDialog}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-400 hover:bg-primary-50 transition-colors"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          {isUploading ? (
            <div className="space-y-2">
              <div className="spinner w-8 h-8 mx-auto"></div>
              <p className="text-gray-600">Uploading image...</p>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-gray-600 font-medium">Click to upload or drag and drop</p>
                <p className="text-gray-500 text-sm">PNG, JPG, WebP up to 50MB</p>
              </div>
            </div>
          )}
        </div>
      ) : (
        // Preview area
        <div className="relative">
          <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
            <div className="flex items-start space-x-4">
              {/* Image preview */}
              <div className="flex-shrink-0">
                {preview ? (
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-24 h-24 object-cover rounded-lg border border-gray-200"
                  />
                ) : (
                  <div className="w-24 h-24 bg-gray-200 rounded-lg flex items-center justify-center">
                    <ImageIcon className="w-8 h-8 text-gray-400" />
                  </div>
                )}
              </div>
              
              {/* Image info */}
              <div className="flex-1 min-w-0">
                {uploadedImage ? (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-green-700 flex items-center">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                      Upload successful
                    </p>
                    <p className="text-xs text-gray-600">
                      Size: {(uploadedImage.size_bytes / 1024).toFixed(1)} KB
                    </p>
                    <p className="text-xs text-gray-600">
                      Type: {uploadedImage.content_type}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      ID: {uploadedImage.image_id}
                    </p>
                  </div>
                ) : isUploading ? (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-blue-700 flex items-center">
                      <div className="spinner w-3 h-3 mr-2"></div>
                      Uploading...
                    </p>
                    <p className="text-xs text-gray-600">Please wait</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-gray-700">Ready to upload</p>
                    <p className="text-xs text-gray-600">Image selected</p>
                  </div>
                )}
              </div>
              
              {/* Remove button */}
              <button
                onClick={clearImage}
                disabled={isUploading}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                title="Remove image"
              >
                <X size={16} />
              </button>
            </div>
          </div>
          
          {/* Upload again button */}
          {uploadedImage && (
            <button
              onClick={openFileDialog}
              className="mt-2 text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Upload different image
            </button>
          )}
        </div>
      )}
      
      {/* Help text */}
      <div className="flex items-start space-x-2 text-xs text-gray-500">
        <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
        <p>
          Images are automatically resized and optimized. Supported formats: JPEG, PNG, WebP. 
          Maximum file size: 50MB.
        </p>
      </div>
      
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};

export default ImageUpload;
