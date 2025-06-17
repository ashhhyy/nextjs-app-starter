import React, { useState, useEffect } from 'react';
import { Play, StopCircle, Image } from 'lucide-react';

// Main App Component
const App = () => {
  const [motionRunning, setMotionRunning] = useState(false);
  const [images, setImages] = useState([]);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingImages, setLoadingImages] = useState(true);
  const [errorStatus, setErrorStatus] = useState(null);
  const [errorImages, setErrorImages] = useState(null);

  // IMPORTANT: Replace YOUR_RASPBERRY_PI_IP with your Pi's actual IP address (e.g., 192.168.100.216)
  // Ensure your Flask API is running on this IP and port (5000).
  const API_BASE_URL = 'http://YOUR_RASPBERRY_PI_IP:5000'; 

  // Fetches robot motion status
  const fetchStatus = async () => {
    setLoadingStatus(true);
    setErrorStatus(null);
    try {
      const res = await fetch(`${API_BASE_URL}/status`);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setMotionRunning(data.motion_running);
    } catch (error) {
      console.error('Error fetching status:', error);
      setErrorStatus(`Failed to fetch status: ${error.message}`);
      setMotionRunning(false);
    } finally {
      setLoadingStatus(false);
    }
  };

  // Fetches latest images
  const fetchImages = async () => {
    setLoadingImages(true);
    setErrorImages(null);
    try {
      const res = await fetch(`${API_BASE_URL}/images`);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setImages(data.images || []);
    } catch (error) {
      console.error('Error fetching images:', error);
      setErrorImages(`Failed to fetch images: ${error.message}`);
      setImages([]);
    } finally {
      setLoadingImages(false);
    }
  };

  // Starts motion control
  const startMotion = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/start`, { method: 'POST' });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      setMotionRunning(true);
      console.log('Motion started successfully.');
    } catch (error) {
      console.error('Error starting motion:', error);
    }
  };

  // Stops motion control
  const stopMotion = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/stop`, { method: 'POST' });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      setMotionRunning(false);
      console.log('Motion stopped successfully.');
    } catch (error) {
      console.error('Error stopping motion:', error);
    }
  };

  // Setup initial data fetch and periodic updates
  useEffect(() => {
    fetchStatus();
    fetchImages();
    const statusInterval = setInterval(fetchStatus, 5000);
    const imageInterval = setInterval(fetchImages, 10000); 

    return () => {
      clearInterval(statusInterval);
      clearInterval(imageInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-inter p-4 sm:p-6 lg:p-8 rounded-lg shadow-lg">
      <header className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-blue-400">
          Autonomous Underwater Robot Dashboard
        </h1>
        <p className="text-gray-400 mt-2 text-md sm:text-lg">Monitor and control your aquatic explorer</p>
      </header>

      <section className="mb-8 p-4 bg-gray-800 rounded-lg shadow-md flex flex-col sm:flex-row items-center justify-between">
        <div className="mb-4 sm:mb-0 sm:mr-4">
          <h2 className="text-xl sm:text-2xl font-semibold text-white">Motion Control</h2>
          {loadingStatus ? (
            <p className="text-yellow-400">Loading status...</p>
          ) : errorStatus ? (
            <p className="text-red-500">Error: {errorStatus}</p>
          ) : (
            <p className={`font-medium ${motionRunning ? 'text-green-400' : 'text-red-400'}`}>
              Status: {motionRunning ? 'Running' : 'Stopped'}
            </p>
          )}
        </div>
        <div className="flex space-x-3">
          <button
            onClick={startMotion}
            disabled={motionRunning || loadingStatus}
            className="flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-green-700 text-white font-semibold rounded-full shadow-lg hover:from-green-600 hover:to-green-800 transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="mr-2 h-5 w-5" /> Start Motion
          </button>
          <button
            onClick={stopMotion}
            disabled={!motionRunning || loadingStatus}
            className="flex items-center px-6 py-3 bg-gradient-to-r from-red-500 to-red-700 text-white font-semibold rounded-full shadow-lg hover:from-red-600 hover:to-red-800 transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <StopCircle className="mr-2 h-5 w-5" /> Stop Motion
          </button>
        </div>
      </section>

      <section className="p-4 bg-gray-800 rounded-lg shadow-md">
        <h2 className="text-xl sm:text-2xl font-semibold text-white mb-4 flex items-center">
          <Image className="mr-2 h-6 w-6 text-purple-400" /> Latest Images
        </h2>
        {loadingImages ? (
          <p className="text-yellow-400 text-center">Loading images...</p>
        ) : errorImages ? (
          <p className="text-red-500 text-center">Error: {errorImages}</p>
        ) : images.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {images.map((imgUrl, idx) => (
              <div key={idx} className="relative aspect-video rounded-lg overflow-hidden shadow-md group">
                <img
                  src={imgUrl}
                  alt={`Captured ${idx}`}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = `https://placehold.co/400x300/374151/FFFFFF?text=Image+Error`;
                  }}
                />
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <span className="text-white text-sm font-medium">Image {idx + 1}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center">No images available. Ensure ESP32-CAM is active and API is running.</p>
        )}
      </section>
    </div>
