import React, { useEffect, useRef } from 'react';

const DashcamView = ({ playbackRate, showBoundingBox }) => {
  const videoRef = useRef(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  return (
    <div className="dashcam-container">
      {/* Fallback to a placeholder if no local video is available */}
      <video 
        ref={videoRef}
        className="dashcam-video" 
        autoPlay 
        loop 
        muted 
        playsInline
        src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
      />
      
      <div className="webcam-pip">
        <img 
          src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=400" 
          alt="Driver Webcam Feed" 
          className="webcam-feed" 
        />
        {showBoundingBox && <div className="bounding-box"></div>}
      </div>
    </div>
  );
};

export default DashcamView;
