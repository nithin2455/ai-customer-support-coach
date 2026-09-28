/**
 * Centralized Language Configuration for Multilingual Support.
 * Supported languages: English, Hindi, Tamil, Kannada with Indian locales.
 */

export const SUPPORTED_LANGUAGES = [
  {
    code: 'en',
    locale: 'en-IN',
    name: 'English',
    nativeName: 'English'
  },
  {
    code: 'hi',
    locale: 'hi-IN',
    name: 'Hindi',
    nativeName: 'हिन्दी'
  },
  {
    code: 'ta',
    locale: 'ta-IN',
    name: 'Tamil',
    nativeName: 'தமிழ்'
  },
  {
    code: 'kn',
    locale: 'kn-IN',
    name: 'Kannada',
    nativeName: 'ಕನ್ನಡ'
  }
];

export const DEFAULT_LANGUAGE = SUPPORTED_LANGUAGES[0];

export function getLanguageByCode(code) {
  if (!code) return DEFAULT_LANGUAGE;
  const normalized = code.toLowerCase().split('-')[0].split('_')[0];
  return SUPPORTED_LANGUAGES.find((l) => l.code === normalized) || DEFAULT_LANGUAGE;
}

export function getLanguageByLocale(locale) {
  if (!locale) return DEFAULT_LANGUAGE;
  return SUPPORTED_LANGUAGES.find((l) => l.locale.toLowerCase() === locale.toLowerCase()) || DEFAULT_LANGUAGE;
}

/**
 * Lightweight script detection as secondary signal.
 */
export function detectScriptLanguage(text) {
  if (!text) return null;
  if (/[\u0B80-\u0BFF]/.test(text)) return getLanguageByCode('ta');
  if (/[\u0C80-\u0CFF]/.test(text)) return getLanguageByCode('kn');
  if (/[\u0900-\u097F]/.test(text)) return getLanguageByCode('hi');
  return null;
}
