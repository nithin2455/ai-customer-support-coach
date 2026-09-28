import React, { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, AlertCircle } from 'lucide-react';
import { getLanguageByCode } from '../config/languages';

/**
 * Reusable VoiceOutputButton Component
 * Uses the browser-native SpeechSynthesis API.
 * Free, client-side, zero paid APIs, zero OpenAI TTS dependencies.
 *
 * Reads assistant messages aloud in the customer's selected language.
 */
export default function VoiceOutputButton({
  text,
  selectedLanguage,
  className = '',
  showLabel = false,
  label = 'Voice Output',
  activeLabel = 'Stop'
}) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [notice, setNotice] = useState(null);
  const noticeTimerRef = useRef(null);

  // Check browser support
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  const showNotice = (msg) => {
    setNotice(msg);
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => {
      setNotice(null);
    }, 4000);
  };

  useEffect(() => {
    return () => {
      if (isSupported && isSpeaking) {
        try {
          window.speechSynthesis.cancel();
        } catch (e) {
          // ignore cleanup
        }
      }
      if (noticeTimerRef.current) {
        clearTimeout(noticeTimerRef.current);
      }
    };
  }, [isSpeaking, isSupported]);

  const handleToggleSpeak = () => {
    if (!text || !text.trim()) return;

    if (!isSupported) {
      showNotice("Text-to-speech is not supported in this browser.");
      return;
    }

    // If already speaking, stop and cancel
    if (isSpeaking) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        // ignore
      }
      setIsSpeaking(false);
      return;
    }

    try {
      // 1. Cancel any active speech
      window.speechSynthesis.cancel();

      // Resolve language object
      const langObj = typeof selectedLanguage === 'object'
        ? selectedLanguage
        : getLanguageByCode(selectedLanguage);
      const targetLocale = langObj?.locale || 'en-IN';
      const langName = langObj?.name || 'Selected language';

      // 2. Create SpeechSynthesisUtterance
      const utterance = new SpeechSynthesisUtterance(text.trim());
      utterance.lang = targetLocale;
      utterance.rate = 0.95; // Slightly measured for natural clarity

      // 3. Inspect available voices
      const voices = window.speechSynthesis.getVoices() || [];
      const prefix = targetLocale.split('-')[0].toLowerCase();

      // Match exact locale (e.g., 'ta-IN') or language prefix ('ta')
      const matchingVoice = voices.find(
        (v) => v.lang.toLowerCase() === targetLocale.toLowerCase() ||
               v.lang.replace('_', '-').toLowerCase() === targetLocale.toLowerCase()
      ) || voices.find(
        (v) => v.lang.toLowerCase().startsWith(prefix)
      );

      if (matchingVoice) {
        utterance.voice = matchingVoice;
      } else if (voices.length > 0 && prefix !== 'en') {
        // Inform user gracefully if OS/browser lacks Indian voice pack
        showNotice(`${langName} voice is not available in this browser.`);
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (e) => {
        console.warn('SpeechSynthesis error:', e);
        setIsSpeaking(false);
      };

      // 4. Speak
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error('Failed to trigger speech synthesis:', err);
      setIsSpeaking(false);
      showNotice("Audio playback failed. Please try again.");
    }
  };

  const getAriaLabel = () => {
    if (isSpeaking) return "Stop listening";
    return "Listen to response";
  };

  const getTitle = () => {
    if (!isSupported) return "Audio output not supported in this browser";
    if (isSpeaking) return "Click to stop speaking";
    return "Listen to this response";
  };

  return (
    <div className="relative inline-flex items-center">
      <button
        type="button"
        onClick={handleToggleSpeak}
        aria-label={getAriaLabel()}
        title={getTitle()}
        className={`rounded-lg font-medium flex items-center justify-center transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 ${
          showLabel ? 'px-3 py-2 text-xs gap-1.5' : 'p-1.5 rounded-md text-[11px] gap-1'
        } ${
          isSpeaking
            ? 'bg-indigo-100 text-indigo-700 border border-indigo-300'
            : 'bg-white hover:bg-slate-100 text-slate-700 hover:text-slate-900 border border-slate-300 shadow-2xs'
        } ${className}`}
      >
        {isSpeaking ? (
          <>
            <VolumeX className="w-3.5 h-3.5 text-indigo-700 animate-pulse" />
            <span className={showLabel ? "font-semibold text-indigo-700" : ""}>{activeLabel}</span>
          </>
        ) : (
          <>
            <Volume2 className="w-3.5 h-3.5" />
            <span>{label}</span>
          </>
        )}
      </button>

      {/* Floating notice if voice unavailable or speech unsupported */}
      {notice && (
        <div
          role="status"
          className="absolute -bottom-8 left-0 whitespace-nowrap bg-slate-900 text-white text-[10px] font-normal px-2 py-0.5 rounded shadow-md flex items-center gap-1 z-30 animate-fade-in"
        >
          <AlertCircle className="w-3 h-3 text-amber-400 shrink-0" />
          <span>{notice}</span>
          <button
            type="button"
            onClick={() => setNotice(null)}
            className="text-[10px] text-slate-400 hover:text-white ml-1 underline"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
