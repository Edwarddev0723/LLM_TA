/**
 * VoiceInput component for speech input with real-time transcription
 * Requirements: 5.1, 5.2 - 語音輸入與即時字幕顯示
 */

import { useState, useCallback } from 'react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import './VoiceInput.css';

interface VoiceInputProps {
  onTranscription: (text: string, audioBlob: Blob | null) => void;
  onReset?: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function VoiceInput({
  onTranscription,
  onReset,
  disabled = false,
  placeholder = '點擊麥克風開始錄音，或直接輸入文字...',
}: VoiceInputProps) {
  const { state, startRecording, stopRecording, resetRecording } = useAudioRecorder();
  const [transcription, setTranscription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartRecording = useCallback(async () => {
    setTranscription('');
    await startRecording();
  }, [startRecording]);

  const handleStopRecording = useCallback(async () => {
    setIsProcessing(true);
    const audioBlob = await stopRecording();
    
    if (audioBlob) {
      try {
        // Send audio to ASR backend for transcription
        const formData = new FormData();
        
        // Determine file extension based on blob type
        let filename = 'recording.webm';
        if (audioBlob.type.includes('mp4') || audioBlob.type.includes('m4a')) {
          filename = 'recording.mp4';
        } else if (audioBlob.type.includes('ogg')) {
          filename = 'recording.ogg';
        }
        
        formData.append('audio', audioBlob, filename);
        
        console.log('Sending audio to ASR:', {
          size: audioBlob.size,
          type: audioBlob.type,
          filename: filename,
        });
        
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/asr/transcribe`,
          {
            method: 'POST',
            body: formData,
          }
        );
        
        console.log('ASR response status:', response.status);
        
        if (response.ok) {
          const result = await response.json();
          console.log('ASR result:', result);
          if (result.text && result.text.trim()) {
            setTranscription(result.text);
          } else {
            // Empty transcription - this is normal for silence or unclear audio
            // Don't show error message, just leave the field empty for user to type
            setTranscription('');
          }
        } else {
          // If ASR fails, show placeholder to prompt text input
          const errorData = await response.json().catch(() => ({}));
          console.warn('ASR transcription failed:', response.status, errorData);
          setTranscription('（語音辨識失敗，請直接輸入文字）');
        }
      } catch (error) {
        console.error('ASR error:', error);
        // ASR service might not be available, user can still type
        setTranscription('（語音辨識暫不可用，請直接輸入文字）');
      }
    }
    setIsProcessing(false);
  }, [stopRecording]);

  const handleReset = useCallback(() => {
    resetRecording();
    setTranscription('');
    onReset?.();
  }, [resetRecording, onReset]);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTranscription(e.target.value);
  };

  const handleSubmit = useCallback(async () => {
    if (!transcription.trim() && !state.isRecording) return;

    if (state.isRecording) {
      const audioBlob = await stopRecording();
      onTranscription(transcription, audioBlob);
    } else {
      onTranscription(transcription, null);
    }
    setTranscription('');
  }, [transcription, state.isRecording, stopRecording, onTranscription]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={`voice-input ${disabled ? 'disabled' : ''}`}>
      <div className="input-area">
        <textarea
          value={transcription}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isProcessing}
          rows={3}
          className="transcription-input"
        />
        
        {state.isRecording && (
          <div className="recording-indicator">
            <span className="recording-dot" />
            <span className="recording-time">{formatDuration(state.duration)}</span>
          </div>
        )}
      </div>

      <div className="input-controls">
        <div className="control-group">
          {!state.isRecording ? (
            <button
              type="button"
              className="btn-mic"
              onClick={handleStartRecording}
              disabled={disabled || isProcessing}
              title="開始錄音"
            >
              <span className="mic-icon">🎤</span>
            </button>
          ) : (
            <button
              type="button"
              className="btn-mic recording"
              onClick={handleStopRecording}
              disabled={disabled}
              title="停止錄音"
            >
              <span className="mic-icon">⏹️</span>
            </button>
          )}

          <button
            type="button"
            className="btn-reset"
            onClick={handleReset}
            disabled={disabled || (!transcription && !state.isRecording)}
            title="重說一次"
          >
            重說一次
          </button>
        </div>

        <button
          type="button"
          className="btn-submit"
          onClick={handleSubmit}
          disabled={disabled || isProcessing || (!transcription.trim() && !state.isRecording)}
        >
          {isProcessing ? '處理中...' : '送出'}
        </button>
      </div>

      {state.error && (
        <div className="input-error">
          <span className="error-icon">⚠️</span>
          <span>{state.error}</span>
        </div>
      )}

      {isProcessing && (
        <div className="processing-indicator">
          <span className="spinner" />
          <span>正在處理語音...</span>
        </div>
      )}
    </div>
  );
}
