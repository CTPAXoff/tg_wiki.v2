import React, { useState, useEffect } from 'react';
import axios from 'axios';

// API base URL
const API_BASE = '/api';

function App() {
  const [authStatus, setAuthStatus] = useState('empty');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [progress, setProgress] = useState(null);
  const [messages, setMessages] = useState([]);
  const [showMessages, setShowMessages] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
    const interval = setInterval(checkProgress, 1000);
    return () => clearInterval(interval);
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/auth/status`);
      setAuthStatus(response.data.status);
      if (response.data.phone) {
        setPhone(response.data.phone);
      }
    } catch (err) {
      console.error('Failed to check auth status:', err);
    }
  };

  const checkProgress = async () => {
    try {
      const response = await axios.get(`${API_BASE}/telegram/progress`);
      setProgress(response.data);
    } catch (err) {
      console.error('Failed to check progress:', err);
    }
  };

  const loadMessages = async () => {
    if (!selectedChat) return;
    
    setError('');
    try {
      const response = await axios.get(`${API_BASE}/telegram/messages`, {
        params: { chat_id: selectedChat.id }
      });
      setMessages(response.data);
      setShowMessages(true);
      setSuccess(`Загружено ${response.data.length} сообщений`);
    } catch (err) {
      setError(err.response?.data?.message || 'Ошибка загрузки сообщений');
    }
  };

  const requestCode = async () => {
    setError('');
    setSuccess('');
    try {
      await axios.post(`${API_BASE}/auth/request-code`, { phone });
      setSuccess('Код отправлен');
    } catch (err) {
      setError(err.response?.data?.message || 'Ошибка отправки кода');
    }
  };

  const confirmCode = async () => {
    setError('');
    setSuccess('');
    try {
      await axios.post(`${API_BASE}/auth/confirm-code`, { phone, code });
      setSuccess('Авторизация успешна');
      setAuthStatus('valid');
      setCode('');
    } catch (err) {
      setError(err.response?.data?.message || 'Ошибка подтверждения кода');
    }
  };

  const resetSession = async () => {
    setError('');
    setSuccess('');
    try {
      await axios.post(`${API_BASE}/auth/reset`);
      setSuccess('Сессия сброшена');
      setAuthStatus('empty');
      setPhone('');
      setCode('');
      setChats([]);
      setSelectedChat(null);
      setMessages([]);
      setShowMessages(false);
    } catch (err) {
      setError(err.response?.data?.message || 'Ошибка сброса сессии');
    }
  };

  const loadChats = async () => {
    setError('');
    setSuccess('');
    try {
      const response = await axios.get(`${API_BASE}/telegram/chats`);
      setChats(response.data);
      setSuccess('Список чатов загружен');
    } catch (err) {
      setError(err.response?.data?.message || 'Ошибка загрузки чатов');
    }
  };

  const startParsing = async () => {
    if (!selectedChat) {
      setError('Выберите чат');
      return;
    }

    setError('');
    setSuccess('');
    try {
      await axios.post(`${API_BASE}/telegram/fetch-messages`, {
        chat_id: selectedChat.id,
        from_date: fromDate || null,
        to_date: toDate || null
      });
      setSuccess('Парсинг начат');
    } catch (err) {
      setError(err.response?.data?.message || 'Ошибка запуска парсинга');
    }
  };

  return (
    <div className="container">
      <h1>Telegram Parser</h1>
      
      {/* Auth Status */}
      <div className={`status ${authStatus}`}>
        Статус: {authStatus === 'valid' ? 'Авторизован' : authStatus === 'invalid' ? 'Недействителен' : 'Пусто'}
      </div>

      {/* Auth Section */}
      {authStatus === 'empty' && (
        <div className="form-group">
          <label>Номер телефона:</label>
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+79991234567"
          />
          <button onClick={requestCode} disabled={!phone}>
            Отправить код
          </button>
          {success && <div className="success-message">{success}</div>}
          {error && <div className="error-message">{error}</div>}
          
          {success && (
            <div className="form-group">
              <label>Код из Telegram:</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="12345"
              />
              <button onClick={confirmCode} disabled={!code}>
                Подтвердить
              </button>
            </div>
          )}
        </div>
      )}

      {/* Invalid Session */}
      {authStatus === 'invalid' && (
        <div className="form-group">
          <p>Сессия недействительна</p>
          <button onClick={resetSession} className="danger">
            Сбросить сессию
          </button>
        </div>
      )}

      {/* Valid Session */}
      {authStatus === 'valid' && (
        <>
          <div className="form-group">
            <button onClick={resetSession} className="secondary">
              Сбросить сессию
            </button>
            <button onClick={loadChats}>
              Загрузить список чатов
            </button>
          </div>

          {chats.length > 0 && (
            <div className="form-group">
              <label>Выберите чат:</label>
              <div className="chat-list">
                {chats.map((chat) => (
                  <div
                    key={chat.id}
                    className={`chat-item ${selectedChat?.id === chat.id ? 'selected' : ''}`}
                    onClick={() => setSelectedChat(chat)}
                  >
                    {chat.title}
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedChat && (
            <div className="form-group">
              <label>Дата с:</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
              <label>Дата по:</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
              <button onClick={startParsing}>
                Начать парсинг
              </button>
              <button onClick={loadMessages} className="secondary">
                Показать сообщения
              </button>
            </div>
          )}

          {showMessages && messages.length > 0 && (
            <div className="form-group">
              <h3>Сообщения ({messages.length})</h3>
              <div className="messages-list">
                {messages.slice(0, 20).map((msg) => (
                  <div key={msg.id} className="message-item">
                    <div className="message-header">
                      <strong>{msg.sender_name}</strong>
                      <small>{new Date(msg.date).toLocaleString()}</small>
                    </div>
                    <div className="message-text">{msg.text}</div>
                  </div>
                ))}
                {messages.length > 20 && (
                  <p>...и еще {messages.length - 20} сообщений</p>
                )}
              </div>
            </div>
          )}

          {progress && progress.status !== 'idle' && (
            <div className="form-group">
              <h3>Прогресс парсинга</h3>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress.progress * 100}%` }}
                />
              </div>
              <p>
                {progress.status === 'parsing' && `Парсинг: ${Math.round(progress.progress * 100)}%`}
                {progress.status === 'completed' && 'Завершено'}
                {progress.status === 'failed' && 'Ошибка'}
              </p>
              <p>Сообщений обработано: {progress.messages_processed}</p>
              {progress.current_chat && <p>Текущий чат: {progress.current_chat}</p>}
            </div>
          )}

          {success && <div className="success-message">{success}</div>}
          {error && <div className="error-message">{error}</div>}
        </>
      )}
    </div>
  );
}

export default App;