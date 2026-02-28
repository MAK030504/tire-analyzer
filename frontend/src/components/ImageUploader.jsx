import React, { useState, useRef } from 'react';

const ImageUploader = ({ onImageSelected, isAnalyzing }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [previewUrl, setPreviewUrl] = useState(null);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const processFile = (file) => {
        if (!file || !file.type.startsWith('image/')) {
            alert('Please upload a valid image file.');
            return;
        }

        // Create a preview URL for immediate feedback
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);

        // Pass file up to parent component
        onImageSelected(file);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            processFile(e.dataTransfer.files[0]);
        }
    };

    const handleFileInput = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            processFile(e.target.files[0]);
        }
    };

    const triggerFileInput = () => {
        if (!isAnalyzing) {
            fileInputRef.current.click();
        }
    };

    const clearSelection = (e) => {
        e.stopPropagation();
        setPreviewUrl(null);
        onImageSelected(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    return (
        <div
            className={`glass-panel animate-fade-in ${isDragging ? 'animate-pulse-glow' : ''}`}
            style={{
                padding: '2.5rem',
                width: '100%',
                maxWidth: '600px',
                margin: '0 auto',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '350px',
                border: isDragging ? '2px dashed var(--accent-blue)' : '2px dashed var(--glass-border)',
                cursor: previewUrl || isAnalyzing ? 'default' : 'pointer',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden'
            }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={previewUrl ? undefined : triggerFileInput}
        >
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileInput}
                accept="image/*"
                style={{ display: 'none' }}
                disabled={isAnalyzing}
            />

            {isAnalyzing && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'rgba(15, 23, 42, 0.8)',
                    backdropFilter: 'blur(8px)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10,
                    color: 'white'
                }}>
                    <div className="animate-pulse-glow" style={{
                        width: '60px',
                        height: '60px',
                        borderRadius: '50%',
                        border: '4px solid rgba(255,255,255,0.1)',
                        borderTopColor: 'var(--accent-blue)',
                        animation: 'spin 1s linear infinite'
                    }} />
                    <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
                    <p style={{ marginTop: '1.5rem', fontWeight: '500', letterSpacing: '1px' }}>ANALYZING TIRE...</p>
                </div>
            )}

            {previewUrl ? (
                <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
                    <div style={{ position: 'relative', width: '100%', height: '250px', borderRadius: '1rem', overflow: 'hidden' }}>
                        <img
                            src={previewUrl}
                            alt="Tire Preview"
                            style={{ width: '100%', height: '100%', objectFit: 'contain', background: 'rgba(0,0,0,0.2)' }}
                        />
                        {!isAnalyzing && (
                            <button
                                onClick={clearSelection}
                                style={{
                                    position: 'absolute',
                                    top: '10px',
                                    right: '10px',
                                    background: 'rgba(0,0,0,0.6)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '50%',
                                    width: '32px',
                                    height: '32px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backdropFilter: 'blur(4px)'
                                }}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
            ) : (
                <div style={{ textAlign: 'center', pointerEvents: 'none' }}>
                    <div style={{
                        width: '80px',
                        height: '80px',
                        background: 'rgba(59, 130, 246, 0.1)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 1.5rem',
                        color: 'var(--accent-blue)'
                    }}>
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                    </div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem', color: 'white' }}>
                        Drag & Drop tire photo
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                        or click to browse your files
                    </p>
                    <div className="btn-primary" style={{ display: 'inline-block' }}>
                        Select Image
                    </div>
                </div>
            )}
        </div>
    );
};

export default ImageUploader;
