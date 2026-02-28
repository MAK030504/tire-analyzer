import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ImageUploader from './components/ImageUploader';
import AnalysisResult from './components/AnalysisResult';
import { analyzeTire, checkHealth } from './api';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [backendHealthy, setBackendHealthy] = useState(true);

  // Check backend health on load
  useEffect(() => {
    const verifyBackend = async () => {
      const isHealthy = await checkHealth();
      setBackendHealthy(isHealthy);
    };
    verifyBackend();
  }, []);

  const handleImageSelected = async (file) => {
    setSelectedImage(file);
    setAnalysisResult(null);
    setError(null);

    if (file) {
      await processImage(file);
    }
  };

  const processImage = async (file) => {
    setIsAnalyzing(true);
    try {
      // Small artificial delay to show off the loading animation
      // since local inference might be too fast to see it
      await new Promise(resolve => setTimeout(resolve, 800));

      const response = await analyzeTire(file);
      setAnalysisResult(response.analysis);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to analyze tire');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <>
      <Header />

      <main style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '2rem'
      }}>
        {!backendHealthy && (
          <div className="glass-panel animate-fade-in" style={{
            background: 'rgba(239, 68, 68, 0.1)',
            borderColor: 'rgba(239, 68, 68, 0.3)',
            color: 'var(--status-replace)',
            padding: '1rem 2rem',
            width: '100%',
            maxWidth: '600px',
            textAlign: 'center',
            fontWeight: '500'
          }}>
            Warning: Could not connect to the backend server at localhost:8000
          </div>
        )}

        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <h2 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            marginBottom: '1rem',
            background: 'linear-gradient(to right, #fff, #94a3b8)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '-0.025em'
          }}>
            Check your tire condition
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem', maxWidth: '600px', margin: '0 auto' }}>
            Upload a clear photo of your car's tire tread or sidewall for an instant, AI-powered safety assessment.
          </p>
        </div>

        <ImageUploader
          onImageSelected={handleImageSelected}
          isAnalyzing={isAnalyzing}
        />

        {error && (
          <div className="glass-panel animate-fade-in" style={{
            background: 'rgba(239, 68, 68, 0.1)',
            borderColor: 'rgba(239, 68, 68, 0.3)',
            color: 'var(--status-replace)',
            padding: '1rem 2rem',
            width: '100%',
            maxWidth: '600px',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        <AnalysisResult result={analysisResult} />

      </main>

      <footer style={{
        textAlign: 'center',
        padding: '3rem 0',
        color: 'var(--text-secondary)',
        fontSize: '0.875rem'
      }}>
        <p>A prototype by the Tire Analyzer Team</p>
        <p style={{ marginTop: '0.5rem', opacity: 0.7 }}>Demo purposes only. Always consult a professional mechanic.</p>
      </footer>
    </>
  );
}

export default App;
