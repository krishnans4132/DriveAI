const chooseVoice = (voices) => (
  voices.find((voice) => voice.lang?.toLowerCase().startsWith('en-in'))
  || voices.find((voice) => voice.lang?.toLowerCase().startsWith('en-gb'))
  || voices.find((voice) => voice.lang?.toLowerCase().startsWith('en-us'))
  || voices.find((voice) => voice.lang?.toLowerCase().startsWith('en'))
  || voices[0]
);

export const speechIsSupported = () => (
  typeof window !== 'undefined'
  && 'speechSynthesis' in window
  && 'SpeechSynthesisUtterance' in window
);

export const speakText = (text) => {
  if (!speechIsSupported() || !text) return false;

  const synthesizer = window.speechSynthesis;
  const utterance = new window.SpeechSynthesisUtterance(text);
  utterance.volume = 1;
  utterance.rate = 0.92;
  utterance.pitch = 1;
  utterance.lang = 'en-IN';

  let started = false;
  const beginSpeech = () => {
    if (started) return;
    started = true;
    const voice = chooseVoice(synthesizer.getVoices());
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang;
    }
    synthesizer.cancel();
    synthesizer.resume();
    synthesizer.speak(utterance);
  };

  if (synthesizer.getVoices().length > 0) {
    beginSpeech();
  } else {
    synthesizer.addEventListener('voiceschanged', beginSpeech, { once: true });
    window.setTimeout(beginSpeech, 250);
  }
  return true;
};
