import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Loader2, AlertCircle } from 'lucide-react';

/**
 * Reusable VoiceInputButton Component
 * Uses the browser-native Web Speech API / SpeechRecognition API.
 * Free, client-side, zero paid APIs, zero OpenAI dependencies.
 *
 * Populates message input for customer review and editing before sending.
 * Does NOT auto-send messages.
 */
export default function VoiceInputButton({
  selectedLanguage,
  onTranscript,
  disabled = false,
  className = '',
  showLabel = false,
  label = 'Voice'
}) {
  const [status, setStatus] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'error'
  const [errorMessage, setErrorMessage] = useState(null);
  const recognitionRef = useRef(null);
  const errorTimerRef = useRef(null);

  // Check browser support for SpeechRecognition
  const isSupported = typeof window !== 'undefined' && Boolean(
    window.SpeechRecognition || window.webkitSpeechRecognition
  );

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // ignore cleanup errors
        }
      }
      if (errorTimerRef.current) {
        clearTimeout(errorTimerRef.current);
      }
    };
  }, []);

  const triggerError = (msg) => {
    setStatus('error');
    setErrorMessage(msg);
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    errorTimerRef.current = setTimeout(() => {
      setStatus('idle');
      setErrorMessage(null);
    }, 4500);
  };

  const handleToggleVoice = () => {
    if (disabled) return;

    if (!isSupported) {
      triggerError("Voice input is not supported in this browser. You can type your message instead.");
      return;
    }

    // If currently listening, stop recognition
    if (status === 'listening' || status === 'processing') {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // ignore
        }
      }
      setStatus('idle');
      return;
    }

    // Start recognition
    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = selectedLanguage?.locale || 'en-IN';

      recognition.onstart = () => {
        setStatus('listening');
        setErrorMessage(null);
      };

      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcriptSegment = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcriptSegment;
          } else {
            interimTranscript += transcriptSegment;
          }
        }

        const textToEmit = finalTranscript || interimTranscript;
        if (textToEmit && onTranscript) {
          onTranscript(textToEmit);
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error event:', event.error);
        let friendlyMsg = "Voice input error. Please try again.";

        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
          friendlyMsg = "Microphone access was denied. Please allow microphone permissions in your browser settings.";
        } else if (event.error === 'no-speech') {
          friendlyMsg = "No speech detected. Please try speaking again.";
        } else if (event.error === 'audio-capture') {
          friendlyMsg = "Microphone is unavailable or not detected.";
        } else if (event.error === 'language-not-supported') {
          friendlyMsg = `${selectedLanguage?.name || 'Selected'} voice input is not supported in this browser.`;
        } else if (event.error === 'network') {
          friendlyMsg = "Speech recognition network timeout. Please type your message.";
        }

        triggerError(friendlyMsg);
      };

      recognition.onend = () => {
        // Guarantee state returns to idle even after silence or completion
        if (status !== 'error') {
          setStatus('idle');
        }
      };

      recognition.start();
    } catch (err) {
      console.error('Failed to initialize speech recognition:', err);
      triggerError("Could not start speech recognition. Please try typing instead.");
    }
  };

  const getButtonTitle = () => {
    if (!isSupported) return "Voice input not supported in this browser";
    if (status === 'listening') return "Listening... Click to stop";
    if (status === 'processing') return "Processing speech...";
    if (status === 'error') return errorMessage || "Voice input error";
    return `Click to speak in ${selectedLanguage?.name || 'English'}`;
  };

  const getAriaLabel = () => {
    if (status === 'listening') return "Stop voice input";
    return `Start voice input in ${selectedLanguage?.name || 'English'}`;
  };

  return (
    <div className="relative inline-flex items-center">
      <button
        type="button"
        onClick={handleToggleVoice}
        disabled={disabled}
        aria-label={getAriaLabel()}
        title={getButtonTitle()}
        className={`relative ${showLabel ? 'px-3 py-2 gap-1.5' : 'p-2'} rounded-lg text-xs font-medium flex items-center justify-center transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 ${
          status === 'listening'
            ? 'bg-rose-50 text-rose-600 border border-rose-300 ring-2 ring-rose-400 animate-pulse'
            : status === 'processing'
            ? 'bg-amber-50 text-amber-600 border border-amber-300'
            : status === 'error'
            ? 'bg-rose-50 text-rose-500 border border-rose-200'
            : 'bg-white hover:bg-slate-100 text-slate-700 hover:text-slate-900 border border-slate-300 shadow-2xs'
        } ${className}`}
      >
        {status === 'listening' ? (
          <>
            <Mic className="w-4 h-4 text-rose-600 animate-bounce" />
            <span className={showLabel ? "font-semibold text-rose-700" : "sr-only"}>
              Listening...
            </span>
          </>
        ) : status === 'processing' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
            <span className={showLabel ? "text-amber-700 font-medium" : "sr-only"}>
              Processing...
            </span>
          </>
        ) : status === 'error' ? (
          <>
            <AlertCircle className="w-4 h-4 text-rose-500" />
            <span className={showLabel ? "text-rose-600 font-medium" : "sr-only"}>
              Error
            </span>
          </>
        ) : (
          <>
            <Mic className="w-4 h-4 text-slate-700" />
            <span className={showLabel ? "text-slate-700 font-medium" : "sr-only"}>
              {label}
            </span>
          </>
        )}
      </button>

      {/* Live status badge when listening or processing */}
      {status === 'listening' && (
        <span className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap bg-rose-600 text-white text-[10px] font-semibold px-2 py-0.5 rounded shadow-sm flex items-center gap-1 z-30">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
          Listening ({selectedLanguage?.name || 'Voice'})...
        </span>
      )}

      {/* Floating friendly error notification */}
      {errorMessage && (
        <div
          role="alert"
          className="absolute -top-12 left-1/2 -translate-x-1/2 whitespace-nowrap bg-slate-900 text-white text-[11px] font-normal px-2.5 py-1 rounded shadow-lg flex items-center gap-1.5 z-40 animate-fade-in"
        >
          <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>{errorMessage}</span>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-[10px] text-slate-400 hover:text-white ml-1 underline"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
