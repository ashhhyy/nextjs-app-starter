import React, { useState, useEffect } from 'react';

const App: React.FC = () => {
  const [motionRunning, setMotionRunning] = useState(false);
  const [images, setImages] = useState<string[]>([]);

  useEffect(() => {
    fetchStatus();
    fetchImages();
    const interval = setInterval(() => {
      fetchStatus();
      fetchImages();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:5000/status');
      const data = await res.json();
      setMotionRunning(data.motion_running);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const fetchImages = async () => {
    try {
      const res = await fetch('http://localhost:5000/images');
      const data = await res.json();
      setImages(data.images);
    } catch (error) {
      console.error('Error fetching images:', error);
    }
  };

  const startMotion = async () => {
    await fetch('http://localhost:5000/start', { method: 'POST' });
    setMotionRunning(true);
  };

  const stopMotion = async () => {
    await fetch('http://localhost:5000/stop', { method: 'POST' });
    setMotionRunning(false);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Autonomous Underwater Robot Dashboard</h1>
      <div className="mb-4">
        <button
          onClick={startMotion}
          disabled={motionRunning}
          className="bg-green-500 text-white px-4 py-2 rounded mr-2 disabled:opacity-50"
        >
          Start Motion
        </button>
        <button
          onClick={stopMotion}
          disabled={!motionRunning}
          className="bg-red-500 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          Stop Motion
        </button>
      </div>
      <div>
        <h2 className="text-xl font-semibold mb-2">Latest Images</h2>
        <div className="grid grid-cols-5 gap-4">
          {images.map((img, idx) => (
            <img key={idx} src={img} alt={`Captured ${idx}`} className="w-full h-auto rounded" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default App;
