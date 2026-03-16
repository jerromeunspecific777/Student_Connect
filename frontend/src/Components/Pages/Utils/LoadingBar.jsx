import React, { createContext, useContext, useState } from "react";
import LoadingBar from "react-top-loading-bar";

// Create a context
const LoadingBarContext = createContext();

const LoadingBarProvider = ({ children }) => {
  const [loadingBarColor, setLoadingBarColor] = useState("white");
  const [progress, setProgress] = useState(0);
  const intervalRef = React.useRef(null);

  // Function to start the loading bar
  const startLoading = (estimatedDuration = 3000) => {
    // Clear any existing interval before starting a new one
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null; // Ensure it's nullified
    }

    setProgress(0);
    setLoadingBarColor("white");

    const intervalTime = 150;
    const trickleScale = Math.max(estimatedDuration / 5000, 1);

    intervalRef.current = setInterval(() => {
      setProgress((prevProgress) => {
        if (prevProgress >= 98.5) { // Changed from 99 to 98.5 for earlier stop
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          return 99;
        }

        const remaining = 99 - prevProgress;
        const increment = Math.max(remaining / (20 * trickleScale), 0.2);
        const nextProgress = prevProgress + increment;

        return nextProgress > 99 ? 99 : nextProgress;
      });
    }, intervalTime);
  };

  // Function to stop the loading bar
  const stopLoading = (isError = false) => {
    // Kill the interval immediately
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (isError) {
      setLoadingBarColor("#ff4d4d"); // Brighter, cleaner red
      setProgress(100);
      // Wait for the bar to finish animation before hiding it
      setTimeout(() => {
        setProgress(0);
      }, 800);
    } else {
      setProgress(100);
      setTimeout(() => {
        setProgress(0);
      }, 800);
    }
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <LoadingBarContext.Provider value={{ startLoading, stopLoading }}>
      <LoadingBar
        color={loadingBarColor}
        progress={progress}
        height={3}
        shadow={false}
        className="custom-top-loading-bar"
        containerStyle={{
          zIndex: 9999,
          display: progress > 0 ? 'block' : 'none',
          boxShadow: progress > 0
            ? (loadingBarColor === 'white'
              ? '0 0 10px rgba(255, 255, 255, 0.5)'
              : '0 0 10px rgba(255, 77, 77, 0.5)')
            : 'none'
        }}
      />
      {children}
    </LoadingBarContext.Provider>
  );
};

// Custom hook to access the context
const useLoadingBar = () => useContext(LoadingBarContext);

export { LoadingBarProvider, useLoadingBar };
