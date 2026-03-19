import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Users, MessageSquare, BarChart3, Database, Save, Edit, Search } from 'lucide-react';
import axios from 'axios';
import { API_URL } from './config';

const AdminDashboard = ({ token, onBack }) => {
  const [activeTab, setActiveTab] = useState('analytics');
  const [popularMajors, setPopularMajors] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch initial data
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      if (activeTab === 'analytics') {
        const res = await axios.get(`${API_URL}/admin/stats/popular-majors`, { headers });
        setPopularMajors(res.data);
      } else if (activeTab === 'chatHistory') {
        const res = await axios.get(`${API_URL}/admin/chat-history`, { headers });
        setChatHistory(res.data);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };


  return (
    <div className="flex h-screen bg-slate-50 w-full font-sans">
      {/* Sidebar Menu */}
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col pt-6 font-semibold shadow-sm">
        <h2 className="text-xl px-6 mb-8 text-blue-700 flex items-center gap-2">
          <Database size={24} /> DNC Admin
        </h2>
        
        <nav className="flex-1 px-4 space-y-2 text-[15px]">
          <button 
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all ${
              activeTab === 'analytics' ? 'bg-blue-50 text-blue-600 shadow-sm' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <BarChart3 size={18} /> Thống Kê
          </button>
          
          <button 
            onClick={() => setActiveTab('chatHistory')}
            className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all ${
              activeTab === 'chatHistory' ? 'bg-blue-50 text-blue-600 shadow-sm' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <MessageSquare size={18} /> Lịch sử Chat
          </button>

        </nav>

        <div className="p-4 border-t">
          <button 
            onClick={onBack}
            className="w-full py-2.5 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-50 transition font-medium"
          >
            Quay lại Chatbot
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto p-8 bg-slate-50">
        
        {loading ? (
          <div className="flex h-full items-center justify-center text-blue-500">
             <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin"></div>
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* TAB: THỐNG KÊ */}
            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <h1 className="text-2xl font-bold text-slate-800">Thống Kê Mức Độ Quan Tâm</h1>
                <p className="text-slate-500">Dựa vào số lần người dùng tra cứu thông tin AI.</p>
                
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mt-6 h-[450px]">
                  {popularMajors.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={popularMajors} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                        <XAxis type="number" />
                        <YAxis dataKey="ten" type="category" width={150} tick={{fontSize: 12}} />
                        <Tooltip cursor={{fill: '#f1f5f9'}} />
                        <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} name="Lượt tra cứu" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                     <p className="text-center text-slate-500 mt-20">Chưa có đủ dữ liệu tra cứu từ người dùng.</p>
                  )}
                </div>
              </div>
            )}

            {/* TAB: LỊCH SỬ CHAT */}
            {activeTab === 'chatHistory' && (
              <div className="space-y-6">
                 <h1 className="text-2xl font-bold text-slate-800">Lịch sử tìm kiếm</h1>
                 <p className="text-slate-500">Theo dõi người dùng đang tương tác với hệ thống AI như thế nào.</p>
                 
                 <div className="space-y-4">
                  {chatHistory.length === 0 && <p className="text-slate-500 text-center py-10">Chưa có dữ liệu trò chuyện.</p>}
                  
                  {chatHistory.map(userStats => (
                    <div key={userStats.user_id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                      <div className="bg-blue-50 px-5 py-3 border-b border-blue-100 flex items-center gap-3 text-blue-800 font-semibold">
                        <Users size={18} /> Người dùng: {userStats.username}
                      </div>
                      <div className="p-5 space-y-4 max-h-[300px] overflow-y-auto">
                         {userStats.sessions.map(s => (
                           <div key={s.session_id} className="border-l-4 border-slate-300 pl-4 py-1">
                             <div className="text-xs text-slate-400 mb-2 font-mono">Phiên: {new Date(s.created_at).toLocaleString('vi-VN')}</div>
                             {s.messages.filter(m => m.role === 'user').slice(-3).map((m, i) => (
                               <div key={i} className="text-sm text-slate-700 bg-slate-50 p-2 rounded mb-1">
                                  "{m.content}"
                               </div>
                             ))}
                           </div>
                         ))}
                      </div>
                    </div>
                  ))}
                 </div>
              </div>
            )}


          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
