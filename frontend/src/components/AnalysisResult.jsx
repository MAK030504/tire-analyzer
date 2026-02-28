import React from 'react';

const AnalysisResult = ({ result }) => {
    if (!result) return null;

    // Expecting shape from backend matching the _to_decision output.
    const { decision, message, label, confidence, probabilities } = result;

    const isOk = decision === "OK";
    const statusColor = isOk ? 'var(--status-ok)' : 'var(--status-replace)';
    const statusGlow = isOk ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';

    // Format probabilities for display if available
    const probEntries = probabilities
        ? Object.entries(probabilities)
            .sort((a, b) => b[1] - a[1]) // Sort high to low
            .slice(0, 3) // Take top 3
        : [];

    return (
        <div className="glass-panel animate-fade-in" style={{
            width: '100%',
            maxWidth: '600px',
            margin: '2rem auto 0',
            overflow: 'hidden',
            position: 'relative'
        }}>
            {/* Dynamic top Border based on Status */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '4px',
                background: statusColor,
                boxShadow: `0 0 20px ${statusGlow}`
            }} />

            <div style={{ padding: '2.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '2rem' }}>
                    <div>
                        <h2 style={{ fontSize: '1rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>
                            Analysis Result
                        </h2>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <span style={{
                                fontSize: '2.5rem',
                                fontWeight: '700',
                                color: statusColor,
                                textShadow: `0 0 30px ${statusGlow}`
                            }}>
                                {decision}
                            </span>
                            {confidence && (
                                <span style={{
                                    background: 'rgba(255,255,255,0.05)',
                                    padding: '4px 10px',
                                    borderRadius: '1rem',
                                    fontSize: '0.875rem',
                                    border: '1px solid var(--glass-border)'
                                }}>
                                    {(confidence * 100).toFixed(1)}% Confidence
                                </span>
                            )}
                        </div>
                    </div>
                    <div style={{
                        width: '60px',
                        height: '60px',
                        borderRadius: '50%',
                        background: `rgba(${isOk ? '16, 185, 129' : '239, 68, 68'}, 0.1)`,
                        color: statusColor,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        {isOk ? (
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                <polyline points="22 4 12 14.01 9 11.01"></polyline>
                            </svg>
                        ) : (
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                        )}
                    </div>
                </div>

                <div style={{
                    background: 'rgba(0,0,0,0.2)',
                    padding: '1.25rem',
                    borderRadius: '0.75rem',
                    marginBottom: probEntries.length > 0 ? '2rem' : '0',
                    borderLeft: `4px solid ${statusColor}`
                }}>
                    <p style={{ fontSize: '1.1rem', lineHeight: '1.6', color: 'white' }}>
                        {message}
                    </p>
                    {label && label !== "unknown" && (
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                            Detected primary signature: <span style={{ color: 'white' }}>{label}</span>
                        </p>
                    )}
                </div>

                {probEntries.length > 0 && (
                    <div>
                        <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>
                            Signature Breakdown
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {probEntries.map(([cls, prob]) => {
                                const percent = Math.round(prob * 100);
                                return (
                                    <div key={cls} style={{ display: 'grid', gridTemplateColumns: '120px 1fr 40px', alignItems: 'center', gap: '1rem' }}>
                                        <span style={{ fontSize: '0.875rem', color: 'white', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {cls}
                                        </span>
                                        <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                                            <div style={{
                                                height: '100%',
                                                width: `${Math.max(2, percent)}%`, // min 2% so dot shows
                                                background: 'var(--accent-blue)',
                                                borderRadius: '3px',
                                                transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)'
                                            }} />
                                        </div>
                                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textAlign: 'right' }}>
                                            {percent}%
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AnalysisResult;
