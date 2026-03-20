import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from './config';
import { 
  Send, Bot, User, Sparkles, AlertCircle, RefreshCw, 
  Menu, X, MessageSquare, GraduationCap, MapPin, Globe, Phone, LogIn, UserPlus, LogOut, Loader2, Database,
  Mic, MicOff, Volume2, VolumeX, ThumbsUp, ThumbsDown, Star, Trash2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import AdminDashboard from './AdminDashboard';


export default function App() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "bot",
      content: "Xin chào! 👋 Mình là Chatbot Tuyển sinh của Đại học Nam Cần Thơ (DNC). Mình có thể giúp bạn tìm hiểu về 45 ngành học, điểm chuẩn năm 2025, cũng như 9 phương thức xét tuyển. Bạn quan tâm đến thông tin gì nào?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Auth state
  const [isRecording, setIsRecording] = useState(false);
  const [speakingId, setSpeakingId] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login', 'register', 'forgot', 'reset'
  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  const [resetToken, setResetToken] = useState(null);
  
  // Profile state
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileForm, setProfileForm] = useState({ khoi_thi: '', diem_du_kien: '' });
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  const [profileMessage, setProfileMessage] = useState({ type: '', text: '' });

  // History state
  const [history, setHistory] = useState([]);
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [isAdminMode, setIsAdminMode] = useState(false);

  // Ngành quan tâm & Phản hồi
  const [favorites, setFavorites] = useState([]);
  const [favoriteForm, setFavoriteForm] = useState({ ma_nganh: '', ten_nganh: '' });
  const [feedbackSent, setFeedbackSent] = useState({});

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const recordingInputStartRef = useRef("");
  const recordingAccumulatedRef = useRef("");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
    const handleResize = () => {
      if (window.innerWidth < 1024) setIsSidebarOpen(false);
      else setIsSidebarOpen(true);
    };
    window.addEventListener('resize', handleResize);
    handleResize();
    
    // Check for reset token in URL
    const params = new URLSearchParams(window.location.search);
    const tokenParams = params.get('reset_token');
    if (tokenParams) {
       setResetToken(tokenParams);
       setAuthMode('reset');
       setShowAuthModal(true);
       window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch user profile, history and favorites on load if logged in
  useEffect(() => {
    if (token) {
      fetchUserProfile();
      fetchUserHistory();
      fetchFavorites();
    } else {
      setFavorites([]);
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const res = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentUser(res.data);
      setProfileForm({
        khoi_thi: res.data.khoi_thi || '',
        diem_du_kien: res.data.diem_du_kien || ''
      });
    } catch (err) {
      console.error(err);
      handleLogout();
    }
  };

  const fetchUserHistory = async () => {
    try {
      const res = await axios.get(`${API_URL}/auth/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchFavorites = async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_URL}/auth/favorites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFavorites(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddFavorite = async (e) => {
    e?.preventDefault();
    if (!favoriteForm.ma_nganh.trim() || !token) return;
    try {
      await axios.post(`${API_URL}/auth/favorites`, {
        ma_nganh: favoriteForm.ma_nganh.trim(),
        ten_nganh: favoriteForm.ten_nganh.trim() || null
      }, { headers: { Authorization: `Bearer ${token}` } });
      setFavoriteForm({ ma_nganh: '', ten_nganh: '' });
      fetchFavorites();
    } catch (err) {
      alert(err.response?.data?.detail || 'Không thể thêm ngành.');
    }
  };

  const handleRemoveFavorite = async (ma_nganh) => {
    if (!token) return;
    try {
      await axios.delete(`${API_URL}/auth/favorites/${encodeURIComponent(ma_nganh)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchFavorites();
    } catch (err) {
      alert(err.response?.data?.detail || 'Không thể xóa.');
    }
  };

  const handleFeedback = async (messageId, rating) => {
    if (feedbackSent[messageId]) return;
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      await axios.post(`${API_URL}/chat/feedback`, { message_id: messageId, rating }, { headers });
      setFeedbackSent(prev => ({ ...prev, [messageId]: true }));
    } catch (err) {
      alert(err.response?.data?.detail || 'Gửi phản hồi thất bại.');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsAuthLoading(true);
    setAuthError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', authForm.username);
      formData.append('password', authForm.password);
      
      const res = await axios.post(`${API_URL}/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      const newToken = res.data.access_token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      setShowAuthModal(false);
      setSessionId(crypto.randomUUID()); // Reset session
      setMessages([{
        id: "welcome", role: "bot", 
        content: `Chào ${authForm.username}! Đã đăng nhập thành công.`, 
        timestamp: new Date().toISOString()
      }]);
    } catch (err) {
      setAuthError(err.response?.data?.detail || 'Đăng nhập thất bại.');
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');
    try {
      await axios.post(`${API_URL}/auth/register`, {
        username: authForm.username,
        email: authForm.email,
        password: authForm.password
      });
      // Auto login after register
      await handleLogin(e);
    } catch (err) {
      setAuthError(err.response?.data?.detail || 'Đăng ký thất bại.');
      setIsAuthLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setIsAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');
    try {
      const res = await axios.post(
        `${API_URL}/auth/forgot-password`,
        { email: authForm.email },
        { timeout: 40000 }
      );
      setAuthSuccess(res.data.message);
    } catch (err) {
      const data = err.response?.data;
      const d = data?.detail;
      let msg =
        typeof d === 'string'
          ? d
          : Array.isArray(d)
            ? d.map((x) => x.msg || JSON.stringify(x)).join(' ')
            : typeof data?.message === 'string'
              ? data.message
              : err.message;
      if (!msg || msg === 'Network Error') {
        msg = 'Lỗi khi gửi yêu cầu. Kiểm tra kết nối hoặc thử lại.';
      }
      setAuthError(msg);
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setIsAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');
    if (authForm.password !== authForm.confirmPassword) {
       setAuthError('Mật khẩu nhập lại không khớp.');
       setIsAuthLoading(false);
       return;
    }
    try {
      const res = await axios.post(`${API_URL}/auth/reset-password`, {
        token: resetToken,
        new_password: authForm.password
      });
      setAuthSuccess(res.data.message);
      setTimeout(() => {
         setAuthMode('login');
         setAuthForm({ ...authForm, password: '', confirmPassword: '' });
         setAuthSuccess('');
      }, 3000);
    } catch (err) {
      const d = err.response?.data?.detail;
      const msg =
        typeof d === 'string'
          ? d
          : Array.isArray(d)
            ? d.map((x) => x.msg || JSON.stringify(x)).join(' ')
            : 'Đặt lại mật khẩu thất bại.';
      setAuthError(msg);
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setIsProfileLoading(true);
    setProfileMessage({ type: '', text: '' });
    try {
      const payload = {};
      if (profileForm.khoi_thi.trim() !== '') payload.khoi_thi = profileForm.khoi_thi;
      if (profileForm.diem_du_kien !== '') payload.diem_du_kien = parseFloat(profileForm.diem_du_kien);
      
      const res = await axios.put(`${API_URL}/auth/profile`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentUser(res.data);
      setProfileMessage({ type: 'success', text: 'Cập nhật hồ sơ thành công!' });
      setTimeout(() => setShowProfileModal(false), 2000);
    } catch (err) {
      setProfileMessage({ type: 'error', text: err.response?.data?.detail || 'Lỗi khi cập nhật hồ sơ.' });
    } finally {
      setIsProfileLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setCurrentUser(null);
    setHistory([]);
    localStorage.removeItem('token');
    handleReset();
  };

  const loadSession = (selectedSessionId, sessionMessages) => {
    setSessionId(selectedSessionId);
    
    // Sort logic requires checking how db returns it. Assuming chronological.
    if(sessionMessages.length === 0) return;
    
    const formattedMessages = sessionMessages.map(m => ({
      id: crypto.randomUUID(),
      role: m.role,
      content: m.content,
      timestamp: m.timestamp
    }));
    setMessages(formattedMessages);
    if(window.innerWidth < 1024) setIsSidebarOpen(false);
  };

  const handleSendMessage = async (text = input) => {
    if (!text.trim()) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const headers = {};
      if(token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await axios.post(`${API_URL}/chat/`, {
        message: text,
        session_id: sessionId
      }, { headers });

      const data = response.data;
      
      const botMessage = {
        id: data.bot_message_id ?? crypto.randomUUID(),
        role: "bot",
        content: data.answer,
        suggestions: data.suggested_questions?.map(s => s.text) || [],
        sources: data.sources || [],
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Background reload history
      if(token) fetchUserHistory();
      
    } catch (err) {
      console.error("Chat error:", err);
      setError("Hệ thống đang bảo trì hoặc mất kết nối mạng. Vui lòng thử lại sau.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSessionId(crypto.randomUUID());
    setMessages([{
      id: "welcome",
      role: "bot",
      content: "Xin chào! 👋 Mình là Chatbot Tuyển sinh của Đại học Nam Cần Thơ (DNC). Mình có thể giúp bạn tìm hiểu về 45 ngành học, điểm chuẩn năm 2025, cũng như 9 phương thức xét tuyển. Bạn quan tâm đến thông tin gì nào?",
      timestamp: new Date().toISOString()
    }]);
    setInput("");
    setError(null);
  };

  const handleStartRecording = async () => {
    if (isRecording) {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (_) {}
      }
      setIsRecording(false);
      return;
    }

    // Web Speech API chỉ hoạt động trên HTTPS hoặc localhost
    const isSecure = window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!isSecure) {
      alert("Nhập bằng giọng nói cần truy cập qua https:// hoặc http://localhost (không dùng địa chỉ IP hoặc http khác).");
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Trình duyệt của bạn không hỗ trợ nhận diện giọng nói (Web Speech API). Vui lòng dùng Chrome hoặc Edge mới nhất.");
      return;
    }

    // Yêu cầu quyền microphone trước để tránh lỗi im lặng
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        alert("Bạn cần cấp quyền Micro để nhập bằng giọng nói. Hãy bấm 🔒 trên thanh địa chỉ → Cài đặt trang → Cho phép Micro.");
      } else if (err.name === 'NotFoundError') {
        alert("Không tìm thấy microphone. Kiểm tra thiết bị và thử lại.");
      } else {
        alert("Không thể truy cập microphone: " + (err.message || err.name));
      }
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'vi-VN';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognitionRef.current = recognition;
    recordingInputStartRef.current = input;
    recordingAccumulatedRef.current = "";

    recognition.onstart = () => setIsRecording(true);

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0]?.transcript ?? '';
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        const sep = recordingAccumulatedRef.current && !recordingAccumulatedRef.current.endsWith(' ') ? ' ' : '';
        recordingAccumulatedRef.current += sep + finalTranscript;
      }

      const prefix = recordingInputStartRef.current
        ? (recordingInputStartRef.current.endsWith(' ') ? recordingInputStartRef.current : recordingInputStartRef.current + ' ')
        : '';
      const full = prefix + recordingAccumulatedRef.current + (interimTranscript ? (recordingAccumulatedRef.current && !recordingAccumulatedRef.current.endsWith(' ') ? ' ' : '') + interimTranscript : '');
      setInput(full.trim() ? full : prefix.trim() || full);
    };

    recognition.onerror = (event) => {
      console.error('Lỗi nhận diện giọng nói:', event.error);
      setIsRecording(false);
      if (event.error === 'not-allowed') {
        alert('Quyền Micro bị từ chối. Bấm 🔒 trên thanh địa chỉ → Cài đặt trang → Cho phép Micro.');
      } else if (event.error !== 'no-speech' && event.error !== 'aborted') {
        alert('Lỗi nhận diện giọng nói: ' + event.error);
      }
    };

    recognition.onend = () => setIsRecording(false);

    try {
      recognition.start();
    } catch (e) {
      console.error(e);
      setIsRecording(false);
      alert("Không thể bật nhận diện giọng nói. Thử tải lại trang và dùng Chrome/Edge.");
    }
  };

  const handleTextToSpeech = (text, id) => {
    if (!window.speechSynthesis) {
      alert("Trình duyệt của bạn không hỗ trợ đọc văn bản.");
      return;
    }
    
    if (speakingId === id) {
       window.speechSynthesis.cancel();
       setSpeakingId(null);
       return;
    }
    
    window.speechSynthesis.cancel();
    
    const cleanText = text.replace(/[*#`_]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'vi-VN';
    utterance.rate = 1.0;
    
    utterance.onstart = () => setSpeakingId(id);
    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    window.speechSynthesis.speak(utterance);
  };

  if (isAdminMode && currentUser?.username === 'admin') {
    return <AdminDashboard token={token} onBack={() => setIsAdminMode(false)} />;
  }

  return (
    <div className="flex h-screen w-full bg-[#f8fafc] font-sans overflow-hidden">
      {/* Decorative Background Pattern */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden sm:block hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400/20 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-5%] w-[30%] h-[30%] bg-amber-400/20 rounded-full blur-[100px]"></div>
      </div>

       {/* Auth Modal */}
       {showAuthModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 relative">
            <button 
              onClick={() => setShowAuthModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X size={20} />
            </button>
            
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                {authMode === 'register' ? <UserPlus size={24} /> : (authMode === 'login' ? <LogIn size={24} /> : <AlertCircle size={24} />)}
              </div>
              <h2 className="text-xl font-bold text-slate-800">
                {authMode === 'register' ? 'Tạo tài khoản' : (authMode === 'login' ? 'Đăng nhập' : (authMode === 'reset' ? 'Đặt lại mật khẩu' : 'Quên mật khẩu'))}
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                {authMode === 'register' ? 'Lưu trữ lịch sử chat của bạn' : (authMode === 'login' ? 'Đăng nhập để xem lịch sử chat' : (authMode === 'reset' ? 'Tạo mật khẩu cá nhân mới' : 'Nhập email để nhận link khôi phục'))}
              </p>
            </div>

            {authError && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100 flex items-center gap-2">
                <AlertCircle size={16} className="flex-shrink-0" />
                {authError}
              </div>
            )}
            {authSuccess && (
              <div className="mb-4 p-3 bg-green-50 text-green-600 text-sm rounded-xl border border-green-100 flex items-center gap-2">
                <Sparkles size={16} className="flex-shrink-0" />
                {authSuccess}
              </div>
            )}

            <form onSubmit={
              authMode === 'register' ? handleRegister : 
              authMode === 'login' ? handleLogin : 
              authMode === 'forgot' ? handleForgotPassword : 
              handleResetPassword
            } className="space-y-4">
              
              {(authMode === 'login' || authMode === 'register') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Tên đăng nhập</label>
                  <input 
                    type="text" 
                    required
                    value={authForm.username}
                    onChange={e => setAuthForm({...authForm, username: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                    placeholder="Nhập username"
                  />
                </div>
              )}

              {(authMode === 'register' || authMode === 'forgot') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
                  <input 
                    type="email" 
                    required
                    value={authForm.email}
                    onChange={e => setAuthForm({...authForm, email: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                    placeholder="Nhập email đăng ký"
                  />
                </div>
              )}

              {(authMode === 'login' || authMode === 'register' || authMode === 'reset') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Mật khẩu {authMode==='reset'?'mới':''}</label>
                  <input 
                    type="password" 
                    required
                    value={authForm.password}
                    onChange={e => setAuthForm({...authForm, password: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                    placeholder="••••••••"
                  />
                </div>
              )}

              {authMode === 'reset' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Xác nhận mật khẩu</label>
                  <input 
                    type="password" 
                    required
                    value={authForm.confirmPassword}
                    onChange={e => setAuthForm({...authForm, confirmPassword: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                    placeholder="••••••••"
                  />
                </div>
              )}
              
              {authMode === 'login' && (
                <div className="flex justify-end mt-[-8px]">
                  <button type="button" onClick={() => { setAuthMode('forgot'); setAuthError(''); setAuthSuccess(''); }} className="text-xs text-blue-600 hover:underline hover:text-blue-800">
                    Quên mật khẩu?
                  </button>
                </div>
              )}

              <button 
                type="submit" 
                disabled={isAuthLoading}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2 mt-2"
              >
                {isAuthLoading && <Loader2 size={16} className="animate-spin" />}
                {authMode === 'register' ? 'Đăng ký ngay' : (authMode === 'login' ? 'Đăng nhập' : (authMode === 'reset' ? 'Đổi mật khẩu' : 'Nhận link khôi phục'))}
              </button>
            </form>

            {authMode !== 'reset' && (
              <div className="mt-6 text-center text-sm text-slate-500 flex flex-col gap-2">
                <div>
                  {authMode === 'register' ? 'Đã có tài khoản? ' : 'Chưa có tài khoản? '}
                  <button 
                    onClick={() => {
                      setAuthMode(authMode === 'register' ? 'login' : 'register');
                      setAuthError('');
                      setAuthSuccess('');
                    }} 
                    className="text-blue-600 font-medium hover:underline"
                  >
                    {authMode === 'register' ? 'Đăng nhập' : 'Đăng ký ngay'}
                  </button>
                </div>
                {authMode === 'forgot' && (
                   <div>
                    <button type="button" onClick={() => { setAuthMode('login'); setAuthError(''); setAuthSuccess(''); }} className="text-xs text-slate-500 hover:underline">
                      &larr; Quay lại đăng nhập
                    </button>
                   </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Profile Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 relative">
            <button 
              onClick={() => setShowProfileModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X size={20} />
            </button>
            
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-3">
                <GraduationCap size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-800">
                Hồ sơ cá nhân
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Cập nhật điểm và khối thi để AI tư vấn ngành phù hợp nhất cho bạn.
              </p>
            </div>

            {profileMessage.text && (
              <div className={`mb-4 p-3 text-sm rounded-xl border flex items-center gap-2 ${
                profileMessage.type === 'error' ? 'bg-red-50 text-red-600 border-red-100' : 'bg-green-50 text-green-600 border-green-100'
              }`}>
                {profileMessage.type === 'error' ? <AlertCircle size={16} /> : <Sparkles size={16} />}
                {profileMessage.text}
              </div>
            )}

            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Khối thi dự kiến (Ví dụ: A00, A01, D01)</label>
                <input 
                  type="text" 
                  value={profileForm.khoi_thi}
                  onChange={e => setProfileForm({...profileForm, khoi_thi: e.target.value.toUpperCase()})}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 uppercase"
                  placeholder="A00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Mức điểm dự kiến đạt được (Ví dụ: 22.5)</label>
                <input 
                  type="number" 
                  step="0.1"
                  min="0"
                  max="30"
                  value={profileForm.diem_du_kien}
                  onChange={e => setProfileForm({...profileForm, diem_du_kien: e.target.value})}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  placeholder="22.5"
                />
              </div>

              <button 
                type="submit" 
                disabled={isProfileLoading}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2 mt-4"
              >
                {isProfileLoading && <Loader2 size={16} className="animate-spin" />}
                Lưu hồ sơ
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside 
        className={`${
          isSidebarOpen
            ? 'translate-x-0 w-[85vw] sm:w-80 pointer-events-auto'
            : '-translate-x-full w-[85vw] sm:w-80 pointer-events-none'
        } fixed lg:static inset-y-0 left-0 z-40 bg-white/80 backdrop-blur-xl border-r border-slate-200/60 shadow-[4px_0_24px_rgba(0,0,0,0.02)] transition-all duration-300 ease-in-out flex flex-col`}
      >
        <div className="p-6 flex flex-col items-center border-b border-slate-100">
          <div className="w-20 h-20 rounded-2xl bg-white shadow-sm flex items-center justify-center p-2 mb-4 border border-slate-100 relative group overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-50 to-amber-50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <img 
              src="https://nctu.edu.vn/Uploads/News/images/DNC_C.png" 
              alt="DNC Logo" 
              className="w-full h-full object-contain relative z-10 drop-shadow-sm"
            />
          </div>
          <h1 className="font-bold text-lg text-slate-800 tracking-tight text-center">Chatbox hỗ trợ tuyển sinh</h1>
          <p className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full mt-2">✨ AI Assistant</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-hide">
          
          <div className="space-y-4">
             {currentUser ? (
              <div className="bg-blue-50/50 rounded-xl p-4 border border-blue-100/50">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
                    {currentUser.username[0].toUpperCase()}
                  </div>
                  <div className="flex-1 truncate">
                    <p className="text-sm font-bold text-slate-800 truncate">{currentUser.username}</p>
                    <p className="text-xs text-slate-500">Người dùng</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <button 
                    onClick={() => {
                       setProfileForm({
                         khoi_thi: currentUser?.khoi_thi || '',
                         diem_du_kien: currentUser?.diem_du_kien || ''
                       });
                       setProfileMessage({ type: '', text: '' });
                       setShowProfileModal(true);
                    }}
                    className="w-full py-2 flex items-center justify-center gap-2 text-xs text-blue-700 bg-white hover:bg-blue-50 border border-blue-100 rounded-lg transition-colors"
                  >
                    <User size={14} />
                    Hồ sơ
                  </button>
                  <button 
                    onClick={handleLogout}
                    className="w-full py-2 flex items-center justify-center gap-2 text-xs text-red-600 bg-white hover:bg-red-50 rounded-lg border border-red-100 transition-colors"
                  >
                    <LogOut size={14} />
                    Đăng xuất
                  </button>
                </div>
                {currentUser?.username === 'admin' && (
                  <button 
                    onClick={() => setIsAdminMode(true)}
                    className="w-full mt-2 py-2 flex items-center justify-center gap-2 text-sm text-blue-800 bg-blue-100 hover:bg-blue-200 rounded-lg border border-blue-200 transition-colors font-semibold"
                  >
                    <Database size={14} />
                    Admin Panel
                  </button>
                )}
              </div>
             ) : (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
                <div className="w-10 h-10 mx-auto rounded-full bg-slate-200 text-slate-500 flex items-center justify-center font-bold mb-2">
                  <User size={18} />
                </div>
                <p className="text-xs text-slate-500 mb-3">Bạn chưa đăng nhập. Lưu hồ sơ để xem lại lịch sử.</p>
                <div className="grid grid-cols-2 gap-2">
                   <button 
                     onClick={() => { setAuthMode('login'); setShowAuthModal(true); setAuthError(''); setAuthSuccess(''); }}
                     className="px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg hover:border-blue-400 font-medium"
                   >
                     Đăng nhập
                   </button>
                   <button 
                     onClick={() => { setAuthMode('register'); setShowAuthModal(true); setAuthError(''); setAuthSuccess(''); }}
                     className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                   >
                     Đăng ký
                   </button>
                </div>
              </div>
             )}
          </div>

          <div className="space-y-2 pt-4 border-t border-slate-100">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-2">Lịch sử trò chuyện</h3>
            
            <button 
              onClick={handleReset}
              className={`w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl transition-colors border ${
                sessionId && messages.length > 1 && !history.find(h => h.session_id === sessionId)
                  ? 'bg-blue-50 text-blue-700 border-blue-100'
                  : 'hover:bg-slate-50 text-slate-600 border-transparent hover:border-slate-200'
              }`}
            >
              <div className="flex items-center gap-3 truncate">
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm font-medium truncate">Cuộc trò chuyện mới</span>
              </div>
            </button>

            {history.map((hist, i) => (
              <button 
                key={hist.session_id}
                onClick={() => loadSession(hist.session_id, hist.messages)}
                className={`w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl transition-colors border ${
                  sessionId === hist.session_id
                    ? 'bg-blue-50 text-blue-700 border-blue-100'
                    : 'hover:bg-slate-50 text-slate-600 border-transparent hover:border-slate-200'
                }`}
              >
                <div className="flex items-center gap-3 truncate">
                  <MessageSquare className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm font-medium truncate">
                    {hist.messages.find(m => m.role === 'user')?.content.substring(0, 20) || 'Hội thoại'}...
                  </span>
                </div>
              </button>
            ))}
          </div>

          {token && (
            <div className="space-y-2 pt-4 border-t border-slate-100 mt-4">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-2">Ngành quan tâm</h3>
              <form onSubmit={handleAddFavorite} className="px-2 space-y-2 mb-3">
                <input
                  type="text"
                  placeholder="Mã ngành (vd: 7720101)"
                  value={favoriteForm.ma_nganh}
                  onChange={e => setFavoriteForm(f => ({ ...f, ma_nganh: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                />
                <input
                  type="text"
                  placeholder="Tên ngành (tùy chọn)"
                  value={favoriteForm.ten_nganh}
                  onChange={e => setFavoriteForm(f => ({ ...f, ten_nganh: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                />
                <button type="submit" className="w-full py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center justify-center gap-1">
                  <Star size={14} /> Lưu ngành
                </button>
              </form>
              {favorites.length === 0 ? (
                <p className="text-xs text-slate-500 px-2">Chưa lưu ngành nào.</p>
              ) : (
                <ul className="space-y-1">
                  {favorites.map(fav => (
                    <li key={fav.id} className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg hover:bg-slate-50 group">
                      <span className="text-sm text-slate-700 truncate flex-1" title={fav.ten_nganh || fav.ma_nganh}>
                        {fav.ten_nganh || fav.ma_nganh}
                      </span>
                      <button type="button" onClick={() => handleRemoveFavorite(fav.ma_nganh)} className="p-1.5 text-slate-400 hover:text-red-600 rounded transition-colors" title="Xóa khỏi danh sách">
                        <Trash2 size={14} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="space-y-2 pt-4 border-t border-slate-100 mt-6">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-2">Liên hệ DNC</h3>
            <a href="https://nctu.edu.vn" target="_blank" rel="noreferrer" className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-colors">
              <Globe className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium">Website chính thức</span>
            </a>
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-colors cursor-default">
              <Phone className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium">0292 3 798 222</span>
            </div>
          </div>

        </div>

        <div className="p-4 border-t border-slate-100">
          <button 
            onClick={handleReset}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-white border border-slate-200 text-slate-700 font-medium rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm active:scale-[0.98]"
          >
            <RefreshCw size={16} />
            Làm mới hội thoại
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full relative z-10 w-full lg:w-[calc(100%-20rem)] bg-transparent">
        
        {/* Header */}
        <header className="h-16 bg-white/70 backdrop-blur-md border-b border-slate-200/50 flex items-center justify-between px-4 sm:px-6 z-20 sticky top-0">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors lg:hidden focus:outline-none"
            >
              {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div className="flex items-center gap-2 lg:hidden">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center p-1 shadow-sm">
                <img src="https://nctu.edu.vn/Uploads/News/images/DNC_C.png" className="w-full h-full object-contain filter brightness-0 invert" alt="Logo" />
              </div>
              <span className="font-semibold text-slate-800">DNC AI</span>
            </div>
            <div className="hidden lg:flex items-center gap-2 text-sm font-medium text-slate-500">
              <GraduationCap size={18} className="text-blue-500" />
              Kỳ tuyển sinh Đại học chính quy 2026
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             {!currentUser && (
               <button 
                  onClick={() => { setAuthMode('login'); setShowAuthModal(true); setAuthError(''); setAuthSuccess(''); }}
                  className="lg:hidden text-xs font-medium text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100"
               >
                 Đăng nhập
               </button>
             )}
             <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-full border border-green-100">
               <span className="relative flex h-2 w-2">
                 <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                 <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
               </span>
               <span className="text-xs font-semibold text-green-700 hidden sm:inline">Online</span>
             </div>
          </div>
        </header>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 scroll-smooth pb-32">
          <div className="max-w-3xl mx-auto space-y-8">
            {messages.map((msg, idx) => (
              <div 
                key={msg.id || idx} 
                className={`flex w-full group ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-4 max-w-[85%] sm:max-w-[75%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  
                  {/* Avatar Avatar Container*/}
                  <div className="flex-shrink-0 mt-1">
                    {msg.role === 'user' ? (
                      <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-tr from-slate-200 to-slate-100 flex items-center justify-center text-slate-500 shadow-sm border border-slate-200 shadow-slate-200/50 overflow-hidden text-sm font-bold uppercase">
                        {currentUser ? currentUser.username[0] : <User size={18} />}
                      </div>
                    ) : (
                      <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white shadow-md border border-blue-500 shadow-blue-500/30">
                        <Bot size={20} />
                      </div>
                    )}
                  </div>

                  {/* Message Body */}
                  <div className="flex flex-col gap-1.5 min-w-0 w-full">
                    <div className={`flex items-center gap-2 px-1 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <span className="text-xs font-semibold text-slate-500">
                        {msg.role === 'user' ? (currentUser ? currentUser.username : 'Bạn') : 'DNC Assistant'}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">
                        {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </span>
                    </div>

                    <div 
                      className={`px-5 py-3.5 rounded-2xl shadow-sm text-[15px] leading-relaxed relative w-full ${
                        msg.role === 'user' 
                          ? 'bg-blue-600 text-white rounded-tr-sm border border-blue-700/50' 
                          : 'bg-white text-slate-700 border border-slate-200/60 rounded-tl-sm shadow-slate-200/40'
                      }`}
                    >
                      {msg.role === 'user' ? (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      ) : (
                        <div className="prose prose-slate max-w-none prose-p:leading-relaxed prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline prose-strong:text-slate-800 text-sm">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>

                    {/* Sources & Suggestions */}
                    {msg.role === 'bot' && (
                      <div className="mt-2 space-y-4 pl-1">
                        
                        {/* Audio TTS & Feedback */}
                        <div className="flex flex-wrap items-center gap-2">
                           <button 
                             onClick={() => handleTextToSpeech(msg.content, msg.id || idx)}
                             className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.05)] transition-all border
                               ${speakingId === (msg.id || idx)
                                 ? 'bg-amber-100 border-amber-200 text-amber-700 hover:bg-amber-200' 
                                 : 'bg-white border-slate-200/80 text-blue-600 hover:border-blue-300 hover:bg-blue-50'
                               }`}
                             title={speakingId === (msg.id || idx) ? "Dừng đọc" : "Đọc nội dung (Text-to-Speech)"}
                           >
                             {speakingId === (msg.id || idx) ? (
                               <><VolumeX size={14} /> Dừng đọc</>
                             ) : (
                               <><Volume2 size={14} /> Phát âm thanh</>
                             )}
                           </button>

                           {typeof msg.id === 'number' && (
                             <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                               {feedbackSent[msg.id] ? (
                                 <span className="font-medium text-green-600">Đã gửi phản hồi</span>
                               ) : (
                                 <>
                                   <button type="button" onClick={() => handleFeedback(msg.id, 'up')} className="inline-flex items-center gap-1 px-2 py-1 rounded border border-slate-200 hover:bg-green-50 hover:border-green-200 text-slate-600 hover:text-green-700 transition-colors" title="Hữu ích">
                                     <ThumbsUp size={12} /> Hữu ích
                                   </button>
                                   <button type="button" onClick={() => handleFeedback(msg.id, 'down')} className="inline-flex items-center gap-1 px-2 py-1 rounded border border-slate-200 hover:bg-red-50 hover:border-red-200 text-slate-600 hover:text-red-700 transition-colors" title="Báo sai">
                                     <ThumbsDown size={12} /> Báo sai
                                   </button>
                                 </>
                               )}
                             </span>
                           )}

                           {msg.sources && msg.sources.length > 0 && (
                             <div className="flex flex-wrap gap-2">
                               {msg.sources.map((src, s_idx) => (
                                 <span key={s_idx} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-blue-50 text-blue-700 text-[11px] rounded-lg border border-blue-100/60 font-medium transition-colors hover:bg-blue-100">
                                   <Sparkles size={12} className="text-blue-500" />
                                   {src.name}
                                 </span>
                               ))}
                             </div>
                           )}
                        </div>
                        
                        {msg.suggestions && msg.suggestions.length > 0 && idx === messages.length - 1 && (
                          <div className="flex flex-col gap-3 mt-4 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-150 fill-mode-both">
                            <div className="flex items-center gap-3 mb-1">
                              <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>
                              <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest px-2">Gợi ý câu hỏi</span>
                              <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {msg.suggestions.map((sg, sg_idx) => (
                                <button
                                  key={sg_idx}
                                  onClick={() => handleSendMessage(sg)}
                                  className="px-4 py-2.5 bg-white text-slate-600 border border-slate-200/80 rounded-xl text-[13px] font-medium hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/50 hover:shadow-sm transition-all text-left active:scale-[0.98]"
                                >
                                  {sg}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex w-full group justify-start items-start gap-4 transition-all duration-300">
                 <div className="flex-shrink-0 mt-1">
                    <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white shadow-md border border-blue-500 animate-pulse">
                      <Bot size={20} />
                    </div>
                 </div>
                 <div className="bg-white border border-slate-200/60 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm h-[52px] flex items-center gap-2 min-w-[70px]">
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce"></span>
                 </div>
              </div>
            )}

            {error && (
              <div className="flex w-full justify-center py-2">
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-xl max-w-lg border border-red-100 shadow-sm shadow-red-500/5 animate-in fade-in zoom-in-95 duration-200">
                  <AlertCircle size={18} className="flex-shrink-0" />
                  <p className="text-sm font-medium">{error}</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} className="h-4" />
          </div>
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#f8fafc] via-[#f8fafc] to-transparent pt-10 pb-6 px-4 z-20">
          <div className="max-w-3xl mx-auto relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-400/20 via-blue-500/20 to-amber-400/20 rounded-[28px] blur-sm opacity-50 transition-opacity group-focus-within:opacity-100"></div>
            <div className="relative bg-white border border-slate-200 shadow-lg shadow-slate-200/50 text-slate-800 rounded-[24px] flex items-end p-2 transition-all focus-within:border-blue-300 focus-within:shadow-blue-500/10">
              <textarea 
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ví dụ: Điểm chuẩn ngành Y khoa là bao nhiêu?"
                className="flex-1 resize-none bg-transparent border-none py-3 pl-4 pr-[88px] sm:pr-[100px] focus:outline-none focus:ring-0 min-h-[48px] max-h-[160px] text-[15px] placeholder-slate-400 shadow-none appearance-none"
                rows="1"
                disabled={isLoading}
              />
              <div className="absolute right-2 bottom-2 flex items-center gap-1">
                <button
                  onClick={handleStartRecording}
                  disabled={isLoading}
                  type="button"
                  title="Nhập bằng giọng nói"
                  className={`p-2.5 rounded-xl transition-all duration-200 flex items-center justify-center
                    ${isRecording 
                      ? 'bg-red-100 text-red-600 animate-pulse border border-red-200 shadow-sm' 
                      : 'bg-transparent text-slate-400 hover:bg-slate-100 hover:text-blue-600'
                    }
                  `}
                >
                  {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                </button>
                <button
                  onClick={() => handleSendMessage()}
                  disabled={!input.trim() || isLoading}
                  className={`p-2.5 rounded-[14px] transition-all duration-200 flex items-center justify-center
                    ${!input.trim() || isLoading 
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/30 hover:scale-105 active:scale-95'
                    }
                  `}
                >
                  <Send size={18} className={`${isLoading ? "animate-pulse" : ""} ml-0.5`} />
                </button>
              </div>
            </div>
            <div className="mt-3 text-center flex flex-col items-center justify-center gap-1">
              <p className="text-[11px] font-medium text-slate-400">
                Chatbot có thể mắc lỗi do AI. Vui lòng tham khảo <a href="https://nctu.edu.vn" className="text-blue-500 hover:underline">Thông báo tuyển sinh chính thức</a>.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && window.innerWidth < 1024 && (
        <div 
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-30 lg:hidden animate-in fade-in"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
    </div>
  );
}
