"""
Clean Translation Service Abstraction.
Supports English, Hindi, Tamil, and Kannada.

Design:
1. Return original text if source == target.
2. Use deterministic multilingual templates when available (0 API calls, instantaneous, zero cost).
3. Use Gemini LLM ONLY when dynamic translation is required.
4. Fall back safely to original text or template if Gemini is unavailable or unconfigured.
5. NO OpenAI dependencies, NO paid cloud speech/translation APIs.
"""
import re
import logging
from typing import Optional, Dict, Any
from app.core.languages import get_language, get_language_name, DEFAULT_LANGUAGE_CODE
from app.services.llm_response_service import (
    is_gemini_configured,
    get_gemini_api_key,
    get_gemini_model,
    _sanitize_error_msg
)

logger = logging.getLogger("translation_service")

# ======================================================================
# Deterministic Multilingual Templates
# ======================================================================

MULTILINGUAL_TEMPLATES = {
    # 1. Greetings
    "greeting": {
        "en": "Hello! Welcome to Customer Support. How can I assist you today? Feel free to ask about delivery times, order status, returns, or account settings.",
        "hi": "नमस्ते! ग्राहक सहायता में आपका स्वागत है। आज मैं आपकी क्या सहायता कर सकता हूँ? आप डिलीवरी समय, ऑर्डर स्थिति, रिटर्न या खाता सेटिंग्स के बारे में पूछ सकते हैं।",
        "ta": "வணக்கம்! வாடிக்கையாளர் ஆதரவிற்கு வரவேற்கிறோம். இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்? டெலிவரி நேரம், ஆர்டர் நிலை, ரிட்டர்ன்கள் அல்லது கணக்கு அமைப்புகள் பற்றி நீங்கள் கேட்கலாம்.",
        "kn": "ನಮಸ್ಕಾರ! ಗ್ರಾಹಕ ಬೆಂಬಲಕ್ಕೆ ಸ್ವಾಗತ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು? ಡೆಲಿವರಿ ಸಮಯ, ಆರ್ಡರ್ ಸ್ಥಿತಿ, ರಿಟರ್ನ್‌ಗಳು ಅಥವಾ ಖಾತೆ ಸೆಟ್ಟಿಂಗ್‌ಗಳ ಬಗ್ಗೆ ನೀವು ಕೇಳಬಹುದು."
    },
    "greeting_short": {
        "en": "Hello! Welcome to Customer Support.",
        "hi": "नमस्ते! ग्राहक सहायता में आपका स्वागत है।",
        "ta": "வணக்கம்! வாடிக்கையாளர் ஆதரவிற்கு வரவேற்கிறோம்.",
        "kn": "ನಮಸ್ಕಾರ! ಗ್ರಾಹಕ ಬೆಂಬಲಕ್ಕೆ ಸ್ವಾಗತ."
    },
    "greeting_hello": {
        "en": "Hello!",
        "hi": "नमस्ते!",
        "ta": "வணக்கம்!",
        "kn": "ನಮಸ್ಕಾರ!"
    },

    # 2. Standard Delivery Info
    "delivery_info": {
        "en": "Standard delivery usually takes 3–5 business days. Express shipping is delivered within 1–2 business days. If you share your order number, I can check the exact status of your specific order.",
        "hi": "मानक डिलीवरी में आमतौर पर 3-5 कार्यदिवस लगते हैं। एक्सप्रेस शिपिंग 1-2 कार्यदिवसों में वितरित की जाती है। यदि आप अपना ऑर्डर नंबर साझा करते हैं, तो मैं आपके विशिष्ट ऑर्डर की सटीक स्थिति देख सकता हूँ।",
        "ta": "வழக்கமான டெலிவரி பொதுவாக 3–5 வேலை நாட்கள் ஆகும். எக்ஸ்பிரஸ் ஷிப்பிங் 1–2 வேலை நாட்களில் டெலிவரி செய்யப்படும். உங்கள் ஆர்டர் எண்ணைப் பகிர்ந்தால், உங்கள் குறிப்பிட்ட ஆர்டரின் துல்லியமான நிலையை என்னால் சரிபார்க்க முடியும்.",
        "kn": "ಸಾಮಾನ್ಯ ಡೆಲಿವರಿ ಸಾಮಾನ್ಯವಾಗಿ 3–5 ವ್ಯವಹಾರ ದಿನಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ. ಎಕ್ಸ್‌ಪ್ರೆಸ್ ಶಿಪ್ಪಿಂಗ್ 1–2 ವ್ಯವಹಾರ ದಿನಗಳಲ್ಲಿ ತಲುಪುತ್ತದೆ. ನಿಮ್ಮ ಆರ್ಡರ್ ಸಂಖ್ಯೆಯನ್ನು ಹಂಚಿಕೊಂಡರೆ, ನಿಮ್ಮ ನಿರ್ದಿಷ್ಟ ಆರ್ಡರ್‌ನ ನಿಖರ ಸ್ಥಿತಿಯನ್ನು ನಾನು ಪರಿಶೀಲಿಸಬಹುದು."
    },

    # 3. Shipping Info
    "shipping_info": {
        "en": "We partner with leading global carriers including FedEx, UPS, and DHL. Standard shipping is free on orders over $50. Once dispatched, you will receive real-time carrier tracking updates via email.",
        "hi": "हम FedEx, UPS और DHL सहित प्रमुख वैश्विक वाहकों के साथ साझेदारी करते हैं। $50 से अधिक के ऑर्डर पर मानक शिपिंग निःशुल्क है। प्रेषण के बाद, आपको ईमेल के माध्यम से रीयल-टाइम ट्रैकिंग अपडेट प्राप्त होंगे।",
        "ta": "நாங்கள் FedEx, UPS மற்றும் DHL உள்ளிட்ட முன்னணி உலகளாவிய கூரியர் நிறுவனங்களுடன் இணைந்துள்ளோம். $50க்கு மேற்பட்ட ஆர்டர்களுக்கு வழக்கமான ஷிப்பிங் இலவசம். அனுப்பப்பட்டதும், மின்னஞ்சல் வழியாக நிகழ்நேர டிராக்கிங் தகவலைப் பெறுவீர்கள்.",
        "kn": "ನಾವು FedEx, UPS ಮತ್ತು DHL ಸೇರಿದಂತೆ ಪ್ರಮುಖ ಗ್ಲೋಬಲ್ ಕ್ಯಾರಿಯರ್‌ಗಳೊಂದಿಗೆ ಪಾಲುದಾರಿಕೆ ಹೊಂದಿದ್ದೇವೆ. $50 ಕ್ಕಿಂತ ಹೆಚ್ಚಿನ ಆರ್ಡರ್‌ಗಳಿಗೆ ಸಾಮಾನ್ಯ ಶಿಪ್ಪಿಂಗ್ ಉಚಿತವಾಗಿದೆ. ಕಳುಹಿಸಿದ ನಂತರ, ನೀವು ಇಮೇಲ್ ಮೂಲಕ ನೈಜ-ಸಮಯದ ಟ್ರ್ಯಾಕಿಂಗ್ ನವೀಕರಣಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತೀರಿ."
    },

    # 4. Return Policy
    "return_policy": {
        "en": "Our return policy allows items to be returned within 30 days of delivery for a full refund or exchange. Items must be in original condition with tags and packaging intact. Prepaid return shipping labels are provided free of charge.",
        "hi": "हमारी वापसी नीति के अनुसार डिलीवरी के 30 दिनों के भीतर पूर्ण धनवापसी या विनिमय के लिए आइटम लौटाए जा सकते हैं। आइटम मूल स्थिति में टैग और पैकेजिंग के साथ होने चाहिए। प्रीपेड रिटर्न शिपिंग लेबल निःशुल्क प्रदान किए जाते हैं।",
        "ta": "எங்கள் ரிட்டர்ன் பாலிசி டெலிவரி செய்யப்பட்ட 30 நாட்களுக்குள் முழு பணத்தைத் திரும்பப்பெற அல்லது பரிமாற்றம் செய்ய அனுமதிக்கிறது. பொருட்கள் அசல் நிலையில் டேக்குகள் மற்றும் பேக்கேஜிங்குடன் இருக்க வேண்டும். ப்ரீபெய்ட் ரிட்டர்ன் ஷிப்பிங் லேபிள்கள் இலவசமாக வழங்கப்படுகின்றன.",
        "kn": "ನಮ್ಮ ರಿಟರ್ನ್ ಪಾಲಿಸಿಯು ಡೆಲಿವರಿ ಆದ 30 ದಿನಗಳೊಳಗೆ ಪೂರ್ಣ ಮರುಪಾವತಿ ಅಥವಾ ವಿನಿಮಯಕ್ಕಾಗಿ ಐಟಂಗಳನ್ನು ಹಿಂತಿರುಗಿಸಲು ಅನುಮತಿಸುತ್ತದೆ. ಐಟಂಗಳು ಟ್ಯಾಗ್‌ಗಳು ಮತ್ತು ಪ್ಯಾಕೇಜಿಂಗ್‌ನೊಂದಿಗೆ ಮೂಲ ಸ್ಥಿತಿಯಲ್ಲಿರಬೇಕು. ಪ್ರಿಪೇಯ್ಡ್ ರಿಟರ್ನ್ ಶಿಪ್ಪಿಂಗ್ ಲೇಬಲ್‌ಗಳನ್ನು ಉಚಿತವಾಗಿ ನೀಡಲಾಗುತ್ತದೆ."
    },

    # 5. Refund Policy
    "refund_policy": {
        "en": "Our refund policy: once a returned item is received and inspected at our fulfillment center, refunds are processed back to the original payment method within 5–7 business days. For items returned in original packaging within 30 days, 100% of the item price is refunded.",
        "hi": "हमारी धनवापसी नीति: पूर्ति केंद्र पर लौटाए गए आइटम के निरीक्षण के बाद, 5-7 कार्यदिवसों के भीतर मूल भुगतान विधि में रिफंड प्रोसेस किया जाता है। 30 दिनों के भीतर मूल पैकेजिंग में लौटाए गए आइटम के लिए 100% मूल्य वापस किया जाता है।",
        "ta": "எங்கள் பணத்தைத் திரும்பப்பெறும் கொள்கை: எங்கள் மையத்தில் திருப்பி அனுப்பப்பட்ட பொருள் பெறப்பட்டு பரிசோதிக்கப்பட்டதும், 5–7 வேலை நாட்களில் அசல் கட்டண முறைக்கு ரீஃபண்ட் செலுத்தப்படும். 30 நாட்களுக்குள் அசல் பேக்கேஜிங்கில் திரும்பும் பொருட்களுக்கு 100% தொகை திரும்பப் பெறப்படும்.",
        "kn": "ನಮ್ಮ ಮರುಪಾವತಿ ನೀತಿ: ನಮ್ಮ ಕೇಂದ್ರದಲ್ಲಿ ಹಿಂತಿರುಗಿಸಿದ ಐಟಂ ಅನ್ನು ಪರಿಶೀಲಿಸಿದ ನಂತರ, 5–7 ವ್ಯವಹಾರ ದಿನಗಳಲ್ಲಿ ಮೂಲ ಪಾವತಿ ವಿಧಾನಕ್ಕೆ ಮರುಪಾವತಿ ಮಾಡಲಾಗುತ್ತದೆ. 30 ದಿನಗಳಲ್ಲಿ ಮೂಲ ಪ್ಯಾಕೇಜಿಂಗ್‌ನಲ್ಲಿ ಹಿಂತಿರುಗಿಸಿದ ಐಟಂಗಳಿಗೆ 100% ಹಣ ಮರುಪಾವತಿಯಾಗುತ್ತದೆ."
    },

    # 6. Cancellation Policy
    "cancellation_policy": {
        "en": "Orders can be cancelled free of charge within 1 hour of placement before they enter warehouse fulfillment. To cancel an order, navigate to Account > Orders and select 'Cancel Order'. If an order has already shipped, it can be returned under our standard 30-day return policy upon arrival.",
        "hi": "वेयरहाउस पूर्ति में जाने से पहले ऑर्डर देने के 1 घंटे के भीतर निःशुल्क रद्द किए जा सकते हैं। रद्द करने के लिए, खाता > ऑर्डर पर जाएं और 'ऑर्डर रद्द करें' चुनें। यदि ऑर्डर पहले ही शिप हो चुका है, तो आगमन पर इसे 30 दिनों की नीति के तहत लौटाया जा सकता है।",
        "ta": "கிடங்கு அனுப்புதலுக்குள் செல்லும் முன், ஆர்டர் செய்த 1 மணி நேரத்திற்குள் இலவசமாக ரத்து செய்யலாம். ஆர்டரை ரத்து செய்ய, கணக்கு > ஆர்டர்கள் என்பதற்குச் சென்று 'ஆர்டரை ரத்து செய்' என்பதைத் தேர்ந்தெடுக்கவும். ஏற்கனவே அனுப்பப்பட்டிருந்தால், வந்தவுடன் எங்கள் 30 நாள் பாலிசியின் கீழ் திருப்பி அனுப்பலாம்.",
        "kn": "ಗೋದಾಮಿನ ಪ್ರಕ್ರಿಯೆಗೆ ಹೋಗುವ ಮೊದಲು ಆರ್ಡರ್ ಮಾಡಿದ 1 ಗಂಟೆಯೊಳಗೆ ಉಚಿತವಾಗಿ ರದ್ದುಗೊಳಿಸಬಹುದು. ಆರ್ಡರ್ ರದ್ದುಮಾಡಲು, ಖಾತೆ > ಆರ್ಡರ್‌ಗಳಿಗೆ ಹೋಗಿ 'ಆರ್ಡರ್ ರದ್ದುಮಾಡಿ' ಆಯ್ಕೆಮಾಡಿ. ಈಗಾಗಲೇ ರವಾನೆಯಾಗಿದ್ದರೆ, ತಲುಪಿದ ನಂತರ ನಮ್ಮ 30 ದಿನಗಳ ರಿಟರ್ನ್ ಪಾಲಿಸಿಯಡಿ ಹಿಂತಿರುಗಿಸಬಹುದು."
    },

    # 7. Payment Methods
    "payment_methods": {
        "en": "We accept all major payment methods including Visa, MasterCard, American Express, Discover, PayPal, Apple Pay, Google Pay, Net Banking, and UPI. All transactions are encrypted with 256-bit SSL security.",
        "hi": "हम Visa, MasterCard, American Express, Discover, PayPal, Apple Pay, Google Pay, Net Banking और UPI सहित सभी प्रमुख भुगतान विधियों को स्वीकार करते हैं। सभी लेनदेन 256-बिट SSL सुरक्षा के साथ एन्क्रिप्ट किए गए हैं।",
        "ta": "நாங்கள் Visa, MasterCard, American Express, Discover, PayPal, Apple Pay, Google Pay, Net Banking மற்றும் UPI உள்ளிட்ட அனைத்து முக்கிய கட்டண முறைகளையும் ஏற்றுக்கொள்கிறோம். அனைத்து பரிவர்த்தனைகளும் 256-பிட் SSL பாதுகாப்புடன் குறியாக்கம் செய்யப்பட்டுள்ளன.",
        "kn": "ನಾವು Visa, MasterCard, American Express, Discover, PayPal, Apple Pay, Google Pay, Net Banking ಮತ್ತು UPI ಸೇರಿದಂತೆ ಎಲ್ಲಾ ಪ್ರಮುಖ ಪಾವತಿ ವಿಧಾನಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತೇವೆ. ಎಲ್ಲಾ ವಹಿವಾಟುಗಳು 256-ಬಿಟ್ SSL ಭದ್ರತೆಯೊಂದಿಗೆ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗಿದೆ."
    },

    # 8. Order prompt / lookup not found
    "order_prompt": {
        "en": "I would be glad to help check your order status. Please provide your order number (e.g., #98213) so I can retrieve the shipment details.",
        "hi": "मुझे आपके ऑर्डर की स्थिति जांचने में खुशी होगी। कृपया अपना ऑर्डर नंबर (उदा. #98213) प्रदान करें ताकि मैं शिपमेंट विवरण प्राप्त कर सकूं।",
        "ta": "உங்கள் ஆர்டர் நிலையைச் சரிபார்க்க நான் மகிழ்ச்சியடைவேன். ஏற்றுமதி விவரங்களைப் பெற தயவுசெய்து உங்கள் ஆர்டர் எண்ணை (எ.கா. #98213) வழங்கவும்.",
        "kn": "ನಿಮ್ಮ ಆರ್ಡರ್ ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಲು ನನಗೆ ಸಂತೋಷವಾಗುತ್ತದೆ. ಶಿಪ್‌ಮೆಂಟ್ ವಿವರಗಳನ್ನು ಪಡೆಯಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆರ್ಡರ್ ಸಂಖ್ಯೆಯನ್ನು (ಉದಾ. #98213) ಒದಗಿಸಿ."
    },

    # 9. Manager Escalation
    "manager_escalation": {
        "en": "I understand you would like to speak with a manager. I have escalated your request to a support supervisor who will review your case and follow up with you directly.",
        "hi": "मैं समझता हूँ कि आप प्रबंधक से बात करना चाहते हैं। मैंने आपके अनुरोध को एक सहायता पर्यवेक्षक तक बढ़ा दिया है जो आपके मामले की समीक्षा करेंगे और सीधे आपसे संपर्क करेंगे।",
        "ta": "நீங்கள் ஒரு மேலாளரிடம் பேச விரும்புகிறீர்கள் என்பதை நான் புரிந்துகொள்கிறேன். உங்கள் வழக்கை மதிப்பாய்வு செய்து உங்களுடன் நேரடியாகத் தொடர்பு கொள்ளும் ஒரு ஆதரவு மேற்பார்வையாளருக்கு உங்கள் கோரிக்கையை நான் அனுப்பியுள்ளேன்.",
        "kn": "ನೀವು ಮ್ಯಾನೇಜರ್ ಅವರೊಂದಿಗೆ ಮಾತನಾಡಲು ಬಯಸುತ್ತೀರಿ ಎಂದು ನಾನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ. ನಿಮ್ಮ ಪ್ರಕರಣವನ್ನು ಪರಿಶೀಲಿಸಿ ನಿಮ್ಮನ್ನು ನೇರವಾಗಿ ಸಂಪರ್ಕಿಸುವ ಬೆಂಬಲ ಮೇಲ್ವಿಚಾರಕರಿಗೆ ನಾನು ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ತಲುಪಿಸಿದ್ದೇನೆ."
    },

    # 10. Security Escalation
    "security_escalation": {
        "en": "I take security concerns very seriously. I have flagged your account for immediate security review and escalated this ticket directly to our Trust & Safety team. A senior security specialist will contact you as a top priority.",
        "hi": "मैं सुरक्षा चिंताओं को बहुत गंभीरता से लेता हूँ। मैंने तत्काल सुरक्षा समीक्षा के लिए आपके खाते को चिह्नित किया है और इस टिकट को सीधे हमारी ट्रस्ट और सुरक्षा टीम को सौंप दिया है। एक वरिष्ठ सुरक्षा विशेषज्ञ आपसे सर्वोच्च प्राथमिकता के रूप में संपर्क करेंगे।",
        "ta": "பாதுகாப்புக் கவலைகளை நான் மிகவும் தீவிரமாக எடுத்துக்கொள்கிறேன். உடனடி பாதுகாப்பாய்வுக்காக உங்கள் கணக்கைக் குறித்துள்ளேன், மேலும் இந்த டிக்கெட்டை நேரடியாக எங்கள் நம்பிக்கை & பாதுகாப்புக் குழுவிற்கு அனுப்பியுள்ளேன். ஒரு மூத்த பாதுகாப்பு நிபுணர் உங்களுக்கு முதன்மை முன்னுரிமையுடன் தொடர்புகொள்வார்.",
        "kn": "ನಾನು ಭದ್ರತಾ ಕಾಳಜಿಗಳನ್ನು ಗಂಭೀರವಾಗಿ ಪರಿಗಣಿಸುತ್ತೇನೆ. ತಕ್ಷಣದ ಭದ್ರತಾ ಪರಿಶೀಲನೆಗಾಗಿ ನಾನು ನಿಮ್ಮ ಖಾತೆಯನ್ನು ಗುರುತಿಸಿದ್ದೇನೆ ಮತ್ತು ಈ ಟಿಕೆಟ್ ಅನ್ನು ನೇರವಾಗಿ ನಮ್ಮ ಟ್ರಸ್ಟ್ ಮತ್ತು ಸುರಕ್ಷತಾ ತಂಡಕ್ಕೆ ವರ್ಗಾಯಿಸಿದ್ದೇನೆ. ಹಿರಿಯ ಭದ್ರತಾ ತಜ್ಞರು ನಿಮಗೆ ಹೆಚ್ಚಿನ ಆದ್ಯತೆಯೊಂದಿಗೆ ಸಂಪರ್ಕಿಸುತ್ತಾರೆ."
    },

    # 11. Legal Escalation
    "legal_escalation": {
        "en": "I understand the seriousness of your inquiry. I have logged your request and transferred your conversation to our designated support escalation desk for official handling.",
        "hi": "मैं आपकी पूछताछ की गंभीरता को समझता हूँ। मैंने आपके अनुरोध को दर्ज कर लिया है और आधिकारिक समाधान के लिए आपकी बातचीत को हमारे सहायता डेस्क पर स्थानांतरित कर दिया है।",
        "ta": "உங்கள் விசாரணையின் தீவிரத்தை நான் புரிந்துகொள்கிறேன். உங்கள் கோரிக்கையைப் பதிவுசெய்து, அதிகாரப்பூர்வ கையாளுதலுக்காக எங்கள் பிரத்யேக ஆதரவுக் குழுவிற்கு மாற்றியுள்ளேன்.",
        "kn": "ನಿಮ್ಮ ವಿಚಾರಣೆಯ ಗಂಭೀರತೆಯನ್ನು ನಾನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ. ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ನಾನು ದಾಖಲಿಸಿದ್ದೇನೆ ಮತ್ತು ಅಧಿಕೃತ ನಿರ್ವಹಣೆಗಾಗಿ ನಮ್ಮ ವಿಶೇಷ ಬೆಂಬಲ ಡೆಸ್ಕ್‌ಗೆ ವರ್ಗಾಯಿಸಿದ್ದೇನೆ."
    },

    # 12. Safe Fallback
    "fallback_response": {
        "en": "I'm sorry, I couldn't complete that request automatically. I've sent your request to a support specialist so you can still get help.",
        "hi": "क्षमा करें, मैं उस अनुरोध को स्वचालित रूप से पूरा नहीं कर सका। मैंने आपका अनुरोध एक सहायता विशेषज्ञ को भेज दिया है ताकि आपको मदद मिल सके।",
        "ta": "மன்னிக்கவும், அந்தக் கோரிக்கையை என்னால் தானாகவே முடிக்க முடியவில்லை. உங்களுக்குத் தேவையான உதவியைப் பெற உங்கள் கோரிக்கையை ஆதரவு நிபுணருக்கு அனுப்பியுள்ளேன்.",
        "kn": "ಕ್ಷಮಿಸಿ, ಆ ವಿನಂತಿಯನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪೂರ್ಣಗೊಳಿಸಲು ನನಗೆ ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ನಿಮಗೆ ಸಹಾಯ ಸಿಗುವಂತೆ ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ನಾನು ಬೆಂಬಲ ತಜ್ಞರಿಗೆ ಕಳುಹಿಸಿದ್ದೇನೆ."
    }
}


def _match_deterministic_template(text: str, target_lang: str) -> Optional[str]:
    """Checks if text matches an existing deterministic template in any known language."""
    clean_text = text.strip()
    clean_lower = clean_text.lower()

    # Exact or near-exact match against any template
    for key, lang_dict in MULTILINGUAL_TEMPLATES.items():
        for lang, t_text in lang_dict.items():
            if clean_text == t_text.strip() or clean_lower == t_text.strip().lower():
                return lang_dict.get(target_lang, lang_dict["en"])

    # Regex slot matching for Dynamic Order Status
    # e.g., "Your order #98213 has been shipped via FedEx (Tracking #TRK-10928) and is expected to arrive Tomorrow by 5:00 PM."
    # or "Your order is expected to arrive tomorrow."
    order_match = re.search(
        r"Your order #?(\w+) has been shipped(?: via ([\w\s]+))?(?: \(Tracking #?([\w\-]+)\))? and is expected to arrive ([^\.]+)\.?",
        clean_text,
        re.IGNORECASE
    )
    if order_match:
        ord_num, carrier, trk_num, eta = order_match.groups()
        carrier = carrier or "Carrier"
        trk_part = f" (Tracking #{trk_num})" if trk_num else ""
        if target_lang == "hi":
            return f"आपका ऑर्डर #{ord_num} {carrier} के माध्यम से भेज दिया गया है{f' (ट्रैकिंग #{trk_num})' if trk_num else ''} और {eta} तक पहुंचने की उम्मीद है।"
        elif target_lang == "ta":
            return f"உங்கள் ஆர்டர் #{ord_num} {carrier} வழியாக அனுப்பப்பட்டது{f' (டிராக்கிங் #{trk_num})' if trk_num else ''} மற்றும் {eta} வந்து சேரும் என எதிர்பார்க்கப்படுகிறது."
        elif target_lang == "kn":
            return f"ನಿಮ್ಮ ಆರ್ಡರ್ #{ord_num} ಅನ್ನು {carrier} ಮೂಲಕ ರವಾನಿಸಲಾಗಿದೆ{f' (ಟ್ರ್ಯಾಕಿಂಗ್ #{trk_num})' if trk_num else ''} ಮತ್ತು {eta} ತಲುಪುವ ನಿರೀಕ್ಷೆಯಿದೆ."
        return clean_text

    # Shorter order delivery phrase e.g. "Your order is expected to arrive tomorrow."
    if "expected to arrive tomorrow" in clean_lower or "arrive tomorrow" in clean_lower:
        if target_lang == "ta":
            return "உங்கள் ஆர்டர் நாளை வந்து சேரும் என எதிர்பார்க்கப்படுகிறது."
        elif target_lang == "hi":
            return "आपका ऑर्डर कल पहुंचने की उम्मीद है।"
        elif target_lang == "kn":
            return "ನಿಮ್ಮ ಆರ್ಡರ್ ನಾಳೆ ತಲುಪುವ ನಿರೀಕ್ಷೆಯಿದೆ."
        return clean_text

    # Order not found e.g. "I couldn't find order #98213. Please verify the order number or contact support."
    not_found_match = re.search(r"I couldn't find order #?(\w+)\. Please verify the order number or contact support\.", clean_text, re.IGNORECASE)
    if not_found_match:
        ord_num = not_found_match.group(1)
        if target_lang == "hi":
            return f"मुझे ऑर्डर #{ord_num} नहीं मिला। कृपया अपना ऑर्डर नंबर सत्यापित करें या सहायता टीम से संपर्क करें।"
        elif target_lang == "ta":
            return f"ஆர்டர் #{ord_num} கண்டுபிடிக்க முடியவில்லை. தயவுசெய்து ஆர்டர் எண்ணை சரிபார்க்கவும் அல்லது ஆதரவைத் தொடர்பு கொள்ளவும்."
        elif target_lang == "kn":
            return f"ಆರ್ಡರ್ #{ord_num} ಕಂಡುಬಂದಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆರ್ಡರ್ ಸಂಖ್ಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ ಅಥವಾ ಬೆಂಬಲವನ್ನು ಸಂಪರ್ಕಿಸಿ."
        return clean_text

    # Sensitive Financial / Refund handoff template matching (Variant A: with specific amount)
    fin_match = re.search(r"I understand you are requesting a refund of ([^\.]+)\. Because this involves a direct financial transaction, I have securely routed your case to a support specialist with financial authorization\. They will review your order details and follow up with you promptly\.", clean_text, re.IGNORECASE)
    if fin_match:
        amt = fin_match.group(1)
        if target_lang == "hi":
            return f"मैं समझता हूँ कि आप {amt} की धनवापसी का अनुरोध कर रहे हैं। चूंकि इसमें प्रत्यक्ष वित्तीय लेनदेन शामिल है, मैंने आपके मामले को वित्तीय प्राधिकरण वाले सहायता विशेषज्ञ को सुरक्षित रूप से भेज दिया है। वे आपके ऑर्डर विवरण की समीक्षा करेंगे और आपसे शीघ्र संपर्क करेंगे।"
        elif target_lang == "ta":
            return f"நீங்கள் {amt} பணத்தைத் திரும்பப்பெறக் கோருகிறீர்கள் என்பதை நான் புரிந்துகொள்கிறேன். இதில் நேரடி நிதி பரிவர்த்தனை உள்ளதால், நிதி அங்கீகாரம் கொண்ட ஒரு ஆதரவு நிபுணருக்கு உங்கள் வழக்கை நான் பாதுகாப்பாக அனுப்பியுள்ளேன். அவர்கள் உங்கள் ஆர்டர் விவரங்களை மதிப்பாய்வு செய்து விரைவாக உங்களுடன் தொடர்புகொள்வார்கள்."
        elif target_lang == "kn":
            return f"ನೀವು {amt} ಮರುಪಾವತಿಯನ್ನು ವಿನಂತಿಸುತ್ತಿದ್ದೀರಿ ಎಂದು ನಾನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ. ಇದರಲ್ಲಿ ನೇರ ಹಣಕಾಸು ವಹಿವಾಟು ಇರುವುದರಿಂದ, ನಾನು ನಿಮ್ಮ ಪ್ರಕರಣವನ್ನು ಹಣಕಾಸು ಅಧಿಕಾರ ಹೊಂದಿರುವ ಬೆಂಬಲ ತಜ್ಞರಿಗೆ ಸುರಕ್ಷಿತವಾಗಿ ಕಳುಹಿಸಿದ್ದೇನೆ. ಅವರು ನಿಮ್ಮ ಆರ್ಡರ್ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಶೀಘ್ರದಲ್ಲೇ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸುತ್ತಾರೆ."
        return clean_text

    # Sensitive Financial / Refund handoff (Variant B: response_engine standard)
    # "I can help you with your refund request. Since this involves a refund of ₹5,000, I need to connect you with a support specialist..."
    fin_match2 = re.search(
        r"I can help you with your (?:refund|transfer) request\. Since this involves a (?:refund|transfer) of ([^,]+(?:,\s*\d+)?|\S+), I need to connect you with a support specialist who can verify the transaction and process the request\. I've sent your request to the support team\.",
        clean_text,
        re.IGNORECASE
    )
    if fin_match2:
        amt = fin_match2.group(1).strip()
        if target_lang == "hi":
            return f"मैं आपके धनवापसी अनुरोध में सहायता कर सकता हूँ। चूंकि इसमें {amt} का रिफंड शामिल है, मुझे आपको एक सहायता विशेषज्ञ से जोड़ना होगा जो लेनदेन को सत्यापित और संसाधित कर सके। मैंने आपका अनुरोध सहायता टीम को भेज दिया है।"
        elif target_lang == "ta":
            return f"உங்கள் பணத்தைத் திரும்பப்பெறும் கோரிக்கைக்கு என்னால் உதவ முடியும். இதில் {amt} ரீஃபண்ட் உள்ளதால், பரிவர்த்தனையைச் சரிபார்த்து கோரிக்கையைச் செயல்படுத்தக்கூடிய ஆதரவு நிபுணருடன் உங்களை இணைக்க வேண்டும். உங்கள் கோரிக்கையை ஆதரவு குழுவிற்கு அனுப்பியுள்ளேன்."
        elif target_lang == "kn":
            return f"ನಿಮ್ಮ ಮರುಪಾವತಿ ವಿನಂತಿಗೆ ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಇದರಲ್ಲಿ {amt} ಮರುಪಾವತಿ ಒಳಗೊಂಡಿರುವುದರಿಂದ, ವಹಿವಾಟನ್ನು ಪರಿಶೀಲಿಸಿ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಬಲ್ಲ ಬೆಂಬಲ ತಜ್ಞರೊಂದಿಗೆ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಬೇಕಾಗಿದೆ. ನಾನು ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಬೆಂಬಲ ತಂಡಕ್ಕೆ ಕಳುಹಿಸಿದ್ದೇನೆ."
        return clean_text

    # Refund request without amount
    if "support specialist with financial authorization" in clean_lower or "requires transaction verification" in clean_lower or "connect you with a support specialist who can verify the transaction" in clean_lower:
        if target_lang == "hi":
            return "मैं समझता हूँ कि आप धनवापसी का अनुरोध कर रहे हैं। चूंकि इसमें प्रत्यक्ष वित्तीय लेनदेन शामिल है, मैंने आपके मामले को वित्तीय प्राधिकरण वाले सहायता विशेषज्ञ को सुरक्षित रूप से भेज दिया है। वे आपके विवरण की समीक्षा करेंगे और आपसे शीघ्र संपर्क करेंगे।"
        elif target_lang == "ta":
            return "நீங்கள் பணத்தைத் திரும்பப்பெறக் கோருகிறீர்கள் என்பதை நான் புரிந்துகொள்கிறேன். இதில் நேரடி நிதி பரிவர்த்தனை உள்ளதால், நிதி அங்கீகாரம் கொண்ட ஒரு ஆதரவு நிபுணருக்கு உங்கள் வழக்கை நான் பாதுகாப்பாக அனுப்பியுள்ளேன். அவர்கள் உங்கள் விவரங்களை மதிப்பாய்வு செய்து விரைவாக உங்களுடன் தொடர்புகொள்வார்கள்."
        elif target_lang == "kn":
            return "ನೀವು ಮರುಪಾವತಿಯನ್ನು ವಿನಂತಿಸುತ್ತಿದ್ದೀರಿ ಎಂದು ನಾನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ. ಇದರಲ್ಲಿ ನೇರ ಹಣಕಾಸು ವಹಿವಾಟು ಇರುವುದರಿಂದ, ನಾನು ನಿಮ್ಮ ಪ್ರಕರಣವನ್ನು ಹಣಕಾಸು ಅಧಿಕಾರ ಹೊಂದಿರುವ ಬೆಂಬಲ ತಜ್ಞರಿಗೆ ಸುರಕ್ಷಿತವಾಗಿ ಕಳುಹಿಸಿದ್ದೇನೆ. ಅವರು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಶೀಘ್ರದಲ್ಲೇ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸುತ್ತಾರೆ."
        return clean_text

    # Security escalation
    if "unauthorized or suspicious account activity" in clean_lower or "trust & safety team" in clean_lower:
        if target_lang == "hi":
            return "मैंने अनधिकृत या संदिग्ध खाता गतिविधि की आपकी रिपोर्ट को चिह्नित किया है और तत्काल समीक्षा के लिए आपकी बातचीत को हमारी सुरक्षा और धोखाधड़ी विशेषज्ञ टीम से जोड़ दिया है।"
        elif target_lang == "ta":
            return "அங்கீகரிக்கப்படாத அல்லது சந்தேகத்திற்கிடமான கணக்குச் செயல்பாட்டின் உங்கள் புகாரைக் குறித்து உடனடியாக எங்கள் பாதுகாப்பு மற்றும் மோசடி நிபுணர் குழுவுடன் இணைத்துள்ளேன்."
        elif target_lang == "kn":
            return "ಅನಧಿಕೃತ ಅಥವಾ ಅನುಮಾನಾಸ್ಪದ ಖಾತೆ ಚಟುವಟಿಕೆಯ ನಿಮ್ಮ ವರದಿಯನ್ನು ನಾನು ಗುರುತಿಸಿದ್ದೇನೆ ಮತ್ತು ತುರ್ತು ಪರಿಶೀಲನೆಗಾಗಿ ನಮ್ಮ ಭದ್ರತೆ ಮತ್ತು ವಂಚನೆ ತಜ್ಞರ ತಂಡಕ್ಕೆ ಸಂಪರ್ಕಿಸಿದ್ದೇನೆ."
        return clean_text

    # Legal escalation
    if "support escalation desk" in clean_lower or "specialist support management and compliance" in clean_lower:
        if target_lang == "hi":
            return "मैंने आपकी पूछताछ को हमारी विशेषज्ञ सहायता प्रबंधन और अनुपालन टीम के लिए चिह्नित किया है। एक विशेषज्ञ को सूचित किया गया है और वे शीघ्र समीक्षा करेंगे।"
        elif target_lang == "ta":
            return "உங்கள் விசாரணையை எங்கள் பிரத்யேக ஆதரவு மேலாண்மை மற்றும் இணக்கக் குழுவிற்காகக் குறித்து வைத்துள்ளேன். ஒரு நிபுணருக்குத் தெரிவிக்கப்பட்டு, விரைவில் மதிப்பாய்வு செய்வார்கள்."
        elif target_lang == "kn":
            return "ನಮ್ಮ ತಜ್ಞರ ಬೆಂಬಲ ನಿರ್ವಹಣೆ ಮತ್ತು ಅನುಸರಣಾ ತಂಡಕ್ಕಾಗಿ ನಾನು ನಿಮ್ಮ ವಿಚಾರಣೆಯನ್ನು ಗುರುತಿಸಿದ್ದೇನೆ. ತಜ್ಞರಿಗೆ ಸೂಚಿಸಲಾಗಿದೆ ಮತ್ತು ಶೀಘ್ರದಲ್ಲೇ ಪರಿಶೀಲಿಸುತ್ತಾರೆ."
        return clean_text

    # Repeated issue
    if "contacted support multiple times" in clean_lower:
        if target_lang == "hi":
            return "मैं देख रहा हूँ कि आपने इस समस्या के संबंध में कई बार समर्थन से संपर्क किया है। मैंने आपके अनुरोध को सीधे एक वरिष्ठ सहायता विशेषज्ञ से जोड़ दिया है ताकि इसे प्राथमिकता से हल किया जा सके।"
        elif target_lang == "ta":
            return "இந்த விவகாரம் தொடர்பாக நீங்கள் பலமுறை ஆதரவைத் தொடர்பு கொண்டுள்ளீர்கள் என்பதை நான் காண்கிறேன். இதை உங்களுக்கு முன்னுரிமையாகத் தீர்க்க ஒரு மூத்த ஆதரவு நிபுணருடன் உங்கள் கோரிக்கையை நேரடியாக இணைத்துள்ளேன்."
        elif target_lang == "kn":
            return "ಈ ಸಮಸ್ಯೆಯ ಬಗ್ಗೆ ನೀವು ಹಲವು ಬಾರಿ ಬೆಂಬಲವನ್ನು ಸಂಪರ್ಕಿಸಿದ್ದೀರಿ ಎಂದು ನಾನು ನೋಡುತ್ತಿದ್ದೇನೆ. ಇದನ್ನು ನಿಮಗೆ ಆದ್ಯತೆಯಾಗಿ ಪರಿಹರಿಸಲು ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ನೇರವಾಗಿ ಹಿರಿಯ ಬೆಂಬಲ ತಜ್ಞರೊಂದಿಗೆ ಸಂಪರ್ಕಿಸಿದ್ದೇನೆ."
        return clean_text

    return None


def _translate_with_gemini(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """
    Translates text between English, Hindi, Tamil, and Kannada using Google Gemini.
    Uses official google-genai SDK with safe error handling and zero OpenAI usage.
    """
    if not is_gemini_configured():
        return None

    src_name = get_language_name(source_lang)
    tgt_name = get_language_name(target_lang)
    api_key = get_gemini_api_key().strip()
    model_name = get_gemini_model()

    prompt = (
        f"You are a professional customer support translator. "
        f"Translate the following text accurately and naturally from {src_name} to {tgt_name}.\n"
        f"Rules:\n"
        f"1. Preserve order numbers (e.g., #98213), tracking numbers, dates, times, currency figures, and product names exactly.\n"
        f"2. Keep a professional, polite, and empathetic customer service tone.\n"
        f"3. Return ONLY the translation, with no explanation, notes, or surrounding quotes.\n\n"
        f"Text to translate:\n{text}"
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=15000)
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=600,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )

        translated = (response.text or "").strip() if response and response.text else ""
        if translated:
            # Strip enclosing quotes if model returned them
            if (translated.startswith('"') and translated.endswith('"')) or (translated.startswith("'") and translated.endswith("'")):
                translated = translated[1:-1].strip()
            return translated

        return None
    except Exception as e:
        safe_err = _sanitize_error_msg(str(e))
        logger.warning(f"[TRANSLATION] Gemini translation failed ({type(e).__name__}: {safe_err}). Using safe fallback.")
        return None


def translate_text(
    text: str,
    source_language: Optional[str] = "en",
    target_language: Optional[str] = "en"
) -> str:
    """
    Main clean translation service abstraction.
    1. Returns original text if source == target or text is empty.
    2. Uses deterministic multilingual templates when available.
    3. Uses Gemini only when dynamic translation is required.
    4. Falls back safely without throwing if Gemini is unavailable.
    """
    if not text or not text.strip():
        return text

    src = (source_language or DEFAULT_LANGUAGE_CODE).lower().split("-")[0].split("_")[0]
    tgt = (target_language or DEFAULT_LANGUAGE_CODE).lower().split("-")[0].split("_")[0]

    # 1. Same language: Return immediately
    if src == tgt:
        return text

    # 2. Check deterministic templates
    matched_template = _match_deterministic_template(text, tgt)
    if matched_template:
        return matched_template

    # 3. Dynamic translation via Gemini if configured
    gemini_result = _translate_with_gemini(text, src, tgt)
    if gemini_result:
        return gemini_result

    # 4. Safe fallback: return original text without breaking
    return text


COMMON_QUERY_PHRASES = {
    # Delivery
    "டெலிவரி நேரம் என்ன?": "What is the delivery time?",
    "டெலிவரி நேரம் என்ன": "What is the delivery time?",
    "டெலிவரி நேரம்": "delivery time",
    "डिलीवरी समय क्या है?": "What is the delivery time?",
    "डिलीवरी समय क्या है": "What is the delivery time?",
    "डिलीवरी समय": "delivery time",
    "ಡೆಲಿವರಿ ಸಮಯ ಎಷ್ಟು?": "What is the delivery time?",
    "ಡೆಲಿವರಿ ಸಮಯ ಎಷ್ಟು": "What is the delivery time?",
    "ಡೆಲಿವರಿ ಸಮಯ": "delivery time",
    "என்னோட ஆர்டர் எப்போ வரும்?": "When will my order arrive?",
    "என் ஆர்டர் எப்போது வரும்?": "When will my order arrive?",
    "मेरा ऑर्डर कब आएगा?": "When will my order arrive?",
    "ನನ್ನ ಆರ್ಡರ್ ಯಾವಾಗ ಬರುತ್ತದೆ?": "When will my order arrive?",

    # Escalation / Manager
    "मुझे प्रबंधक से बात करनी है": "I want to speak with a manager",
    "मैनेजर से बात करनी है": "I want to speak with a manager",
    "मैनेजर से बात कराओ": "I want to speak with a manager",
    "மேலாளரிடம் பேச வேண்டும்": "I want to speak with a manager",
    "மேனேஜரிடம் பேச வேண்டும்": "I want to speak with a manager",
    "ம್ಯಾನೇಜರ್ ಅವರೊಂದಿಗೆ ಮಾತನಾಡಬೇಕು": "I want to speak with a manager",
    "ವ್ಯವಸ್ಥಾಪಕರೊಂದಿಗೆ ಮಾತನಾಡಬೇಕು": "I want to speak with a manager",

    # Sensitive Refund actions
    "எனக்கு ரீஃபண்ட் வேண்டும்": "I need a refund",
    "எனக்கு 5000 ரூபாய் refund வேண்டும்": "I need a refund of ₹5,000",
    "எனக்கு 5000 ரூபாய் ரீஃபண்ட் வேண்டும்": "I need a refund of ₹5,000",
    "எனக்கு ரீபண்ட் வேண்டும்": "I need a refund",
    "मुझे रिफंड चाहिए": "I need a refund",
    "मुझे 5000 रुपये का रिफंड चाहिए": "I need a refund of ₹5,000",
    "मुझे 5000 रुपये का refund चाहिए": "I need a refund of ₹5,000",
    "ನನಗೆ ಮರುಪಾವತಿ ಬೇಕು": "I need a refund",
    "ನನಗೆ 5000 ರೂ ಮರುಪಾವತಿ ಬೇಕು": "I need a refund of ₹5,000",
    "ನನಗೆ 5000 ರೂಪಾಯಿ ಮರುಪಾವತಿ ಬೇಕು": "I need a refund of ₹5,000",
    "ನನಗೆ 5000 refund ಬೇಕು": "I need a refund of ₹5,000"
}


def translate_to_english(text: str, source_language: Optional[str] = None) -> str:
    """Convenience helper to translate any supported language text to English."""
    if not text or not text.strip():
        return text
    if not source_language or source_language.lower().startswith("en"):
        return text

    clean = text.strip()
    if clean in COMMON_QUERY_PHRASES:
        return COMMON_QUERY_PHRASES[clean]
    for phrase, eng in COMMON_QUERY_PHRASES.items():
        if phrase in clean:
            return eng

    return translate_text(text, source_language=source_language, target_language="en")


def translate_from_english(text: str, target_language: Optional[str] = None) -> str:
    """Convenience helper to translate English text into customer's selected language."""
    if not target_language or target_language.lower().startswith("en"):
        return text
    return translate_text(text, source_language="en", target_language=target_language)
