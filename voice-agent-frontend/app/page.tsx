'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('Connecting...');
  const [messages, setMessages] = useState<Message[]>([]);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const isMountedRef = useRef(true);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isRecordingRef = useRef(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const SILENCE_THRESHOLD = 0.02;
  const SILENCE_DURATION = 600;

  const closeAudioContext = () => {
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
    audioContextRef.current = null;
  };

  useEffect(() => {
    isMountedRef.current = true;
    let storedSessionId = localStorage.getItem('voice-agent-session');
    if (!storedSessionId) {
      storedSessionId = crypto.randomUUID();
      localStorage.setItem('voice-agent-session', storedSessionId);
    }

    const wsUrl = `ws://localhost:8001/ws/voice?session_id=${storedSessionId}`;
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) return;
      setIsConnected(true);
      setStatus('Connected');
      startListening();
    };

    ws.onclose = (event) => {
      if (!isMountedRef.current) return;
      if (wsRef.current === ws) {
        setIsConnected(false);
        setStatus('Disconnected');
        setIsProcessing(false);
        stopListening();
      }
    };

    ws.onerror = () => {
      if (!isMountedRef.current) return;
      if (wsRef.current === ws) setStatus('Error');
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        const data = JSON.parse(event.data);
        if (data.type === 'result') {
          setMessages((prev) => [
            ...prev,
            { role: 'user', content: data.user_text },
            { role: 'assistant', content: data.assistant_text },
          ]);
          setIsProcessing(false);
          startListening();
        } else if (data.type === 'error') {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `⚠️ ${data.detail}` },
          ]);
          setIsProcessing(false);
          startListening();
        }
      } else if (event.data instanceof ArrayBuffer) {
        const blob = new Blob([event.data], { type: 'audio/mpeg' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        if (audioPlayerRef.current) {
          audioPlayerRef.current.src = url;
          audioPlayerRef.current.play();
        }
      }
    };

    return () => {
      isMountedRef.current = false;
      stopListening();
      if (wsRef.current === ws) wsRef.current = null;
      ws.close();
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startListening = async () => {
    if (!isConnected || isProcessing || isRecordingRef.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      closeAudioContext();

      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'end' }));
        }
        stream.getTracks().forEach((track) => track.stop());
        closeAudioContext();
        isRecordingRef.current = false;
        setIsRecording(false);
        setIsProcessing(true);
        setStatus('Processing...');
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      };

      mediaRecorder.start(250);
      isRecordingRef.current = true;
      setIsRecording(true);
      setStatus('Listening...');
      detectSilence();
    } catch (err) {
      setStatus('Microphone error');
    }
  };

  const detectSilence = () => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const dataArray = new Uint8Array(analyser.fftSize);

    const check = () => {
      if (!isRecordingRef.current) return;
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const value = (dataArray[i] - 128) / 128;
        sum += value * value;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      if (rms < SILENCE_THRESHOLD) {
        if (!silenceTimeoutRef.current) {
          silenceTimeoutRef.current = setTimeout(() => {
            if (mediaRecorderRef.current && isRecordingRef.current) {
              mediaRecorderRef.current.stop();
            }
            silenceTimeoutRef.current = null;
          }, SILENCE_DURATION);
        }
      } else {
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      }
      requestAnimationFrame(check);
    };
    check();
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && isRecordingRef.current) {
      mediaRecorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    closeAudioContext();
    isRecordingRef.current = false;
    setIsRecording(false);
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
  };

  return (
    <main className="voice-main">
      <div className="voice-card">
        <div className="voice-header">
          <h1>Mo Salah Voice Agent</h1>
          <div className="status">
            <span className={`dot ${isConnected ? 'green' : 'red'}`} />
            <span>{status}</span>
          </div>
        </div>

        <div className="conversation">
          {messages.length === 0 && (
            <div className="empty">Start speaking...</div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="bubble">
                {msg.role === 'assistant' ? (
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        <div className="orb-container">
          <div className={`orb ${isRecording ? 'recording' : isProcessing ? 'processing' : ''}`} />
        </div>

        <div className="controls">
          <button
            onClick={startListening}
            disabled={isRecording || !isConnected || isProcessing}
            className="btn start"
          >
            {isRecording ? 'Listening...' : 'Start Listening'}
          </button>
          <button
            onClick={stopListening}
            disabled={!isRecording}
            className="btn stop"
          >
            Stop
          </button>
        </div>

        <audio ref={audioPlayerRef} controls className="audio-player" />
      </div>

      <div className="watermark">Mohamed Salah</div>
    </main>
  );
}