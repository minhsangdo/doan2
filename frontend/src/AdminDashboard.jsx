import React, { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import {
  Users,
  MessageSquare,
  BarChart3,
  Database,
  Save,
  Edit,
  Search,
  RefreshCw,
  Layers,
  ChevronDown,
  ChevronRight,
  Bot,
} from 'lucide-react';
import axios from 'axios';
import { API_URL } from './config';

const AdminDashboard = ({ token, onBack }) => {
  const [activeTab, setActiveTab] = useState('analytics');
  const [popularMajors, setPopularMajors] = useState([]);
  const [kgStats, setKgStats] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [majors, setMajors] = useState([]);
  const [majorSearch, setMajorSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState(null);
  const [editingMajor, setEditingMajor] = useState(null);
  const [form, setForm] = useState({
    ten: '',
    nhom: '',
    mo_ta: '',
    diem_thpt: '',
    diem_hocba: '',
  });
  const [rebuildConfirm, setRebuildConfirm] = useState(false);
  const [rebuildFullIngest, setRebuildFullIngest] = useState(true);
  const [rebuildBusy, setRebuildBusy] = useState(false);
  const [expandedSessions, setExpandedSessions] = useState({});

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}` }),
    [token]
  );

  const fetchData = async () => {
    setLoading(true);
    setActionMsg(null);
    try {
      if (activeTab === 'analytics') {
        const [statsRes, popRes] = await Promise.all([
          axios.get(`${API_URL}/admin/stats`, { headers }),
          axios.get(`${API_URL}/admin/stats/popular-majors`, { headers }),
        ]);
        setKgStats(statsRes.data);
        setPopularMajors(popRes.data);
      } else if (activeTab === 'chatHistory') {
        const res = await axios.get(`${API_URL}/admin/chat-history`, { headers });
        setChatHistory(res.data);
      } else if (activeTab === 'kg') {
        const res = await axios.get(`${API_URL}/admin/majors`, { headers });
        setMajors(Array.isArray(res.data) ? res.data : []);
      }
    } catch (err) {
      console.error(err);
      const d = err.response?.data?.detail;
      setActionMsg({
        type: 'err',
        text: typeof d === 'string' ? d : 'Lỗi tải dữ liệu (403? Đăng nhập lại bằng admin).',
      });
    }
    setLoading(false);
  };

  const filteredMajors = useMemo(() => {
    const q = majorSearch.trim().toLowerCase();
    if (!q) return majors;
    return majors.filter(
      (m) =>
        (m.ma_nganh && String(m.ma_nganh).toLowerCase().includes(q)) ||
        (m.ten && String(m.ten).toLowerCase().includes(q)) ||
        (m.nhom && String(m.nhom).toLowerCase().includes(q))
    );
  }, [majors, majorSearch]);

  const openEdit = (m) => {
    setEditingMajor(m);
    setForm({
      ten: m.ten || '',
      nhom: m.nhom || '',
      mo_ta: m.mo_ta || '',
      diem_thpt: m.diem_thpt != null ? String(m.diem_thpt) : '',
      diem_hocba: m.diem_hocba != null ? String(m.diem_hocba) : '',
    });
  };

  const saveMajor = async () => {
    if (!editingMajor) return;
    try {
      const payload = {
        ten: form.ten,
        nhom: form.nhom,
        mo_ta: form.mo_ta || null,
        diem_thpt: form.diem_thpt === '' ? null : parseFloat(form.diem_thpt),
        diem_hocba: form.diem_hocba === '' ? null : parseFloat(form.diem_hocba),
      };
      await axios.put(`${API_URL}/admin/majors/${encodeURIComponent(editingMajor.ma_nganh)}`, payload, {
        headers,
      });
      setActionMsg({ type: 'ok', text: 'Đã cập nhật ngành / điểm chuẩn trên Neo4j.' });
      setEditingMajor(null);
      fetchData();
    } catch (err) {
      const d = err.response?.data?.detail;
      setActionMsg({
        type: 'err',
        text: typeof d === 'string' ? d : 'Lỗi khi cập nhật.',
      });
    }
  };

  const runRebuild = async () => {
    if (!rebuildConfirm) {
      setActionMsg({ type: 'err', text: 'Tick ô xác nhận trước khi rebuild (use case).' });
      return;
    }
    setRebuildBusy(true);
    setActionMsg(null);
    try {
      const res = await axios.post(
        `${API_URL}/admin/rebuild`,
        { confirm: true, full_ingest: rebuildFullIngest },
        { headers, timeout: 600000 }
      );
      setActionMsg({ type: 'ok', text: res.data?.message || 'Rebuild xong.' });
      if (activeTab === 'analytics') fetchData();
      if (activeTab === 'kg') fetchData();
    } catch (err) {
      const d = err.response?.data?.detail;
      setActionMsg({
        type: 'err',
        text: typeof d === 'string' ? d : err.message || 'Lỗi rebuild (timeout / Neo4j / JSON).',
      });
    }
    setRebuildBusy(false);
  };

  const toggleSessionExpand = (key) => {
    setExpandedSessions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex h-screen bg-slate-50 w-full font-sans">
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col pt-6 font-semibold shadow-sm">
        <h2 className="text-xl px-6 mb-8 text-blue-700 flex items-center gap-2">
          <Database size={24} /> DNC Admin
        </h2>

        <nav className="flex-1 px-4 space-y-2 text-[15px]">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all ${
              activeTab === 'analytics'
                ? 'bg-blue-50 text-blue-600 shadow-sm'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <BarChart3 size={18} /> Thống kê KG
          </button>

          <button
            onClick={() => setActiveTab('kg')}
            className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all ${
              activeTab === 'kg'
                ? 'bg-blue-50 text-blue-600 shadow-sm'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <Layers size={18} /> Quản lý Knowledge Graph
          </button>

          <button
            onClick={() => setActiveTab('chatHistory')}
            className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all ${
              activeTab === 'chatHistory'
                ? 'bg-blue-50 text-blue-600 shadow-sm'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
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

      <div className="flex-1 overflow-auto p-8 bg-slate-50">
        {actionMsg && (
          <div
            className={`mb-4 px-4 py-3 rounded-xl text-sm ${
              actionMsg.type === 'ok'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {actionMsg.text}
          </div>
        )}

        {loading ? (
          <div className="flex h-full items-center justify-center text-blue-500">
            <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <h1 className="text-2xl font-bold text-slate-800">Thống kê quan tâm & đồ thị Neo4j</h1>
                <p className="text-slate-500">
                  <code className="text-xs bg-slate-200 px-1 rounded">get_kg_stats()</code> &{' '}
                  <code className="text-xs bg-slate-200 px-1 rounded">get_popular_majors()</code> — dữ liệu từ
                  Neo4j.
                </p>

                {kgStats && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs text-slate-500 uppercase">Tổng số nút</div>
                      <div className="text-2xl font-bold text-slate-800">{kgStats.total_nodes ?? 0}</div>
                    </div>
                    <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                      <div className="text-xs text-slate-500 uppercase">Tổng quan hệ</div>
                      <div className="text-2xl font-bold text-slate-800">
                        {kgStats.total_relationships ?? 0}
                      </div>
                    </div>
                  </div>
                )}

                {kgStats?.node_counts && Object.keys(kgStats.node_counts).length > 0 && (
                  <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="font-semibold text-slate-700 mb-3">Số nút theo nhãn</h3>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(kgStats.node_counts).map(([label, c]) => (
                        <span
                          key={label}
                          className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-sm"
                        >
                          {label}: <strong>{c}</strong>
                        </span>
                      ))}
                    </div>
                    {kgStats.relationship_counts && Object.keys(kgStats.relationship_counts).length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <h3 className="font-semibold text-slate-700 mb-2">Quan hệ</h3>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(kgStats.relationship_counts).map(([rel, c]) => (
                            <span
                              key={rel}
                              className="px-3 py-1 rounded-full bg-blue-50 text-blue-800 text-sm"
                            >
                              {rel}: <strong>{c}</strong>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mt-2 h-[450px]">
                  <h3 className="font-semibold text-slate-700 mb-2">Ngành được quan tâm (tra cứu)</h3>
                  {popularMajors.length > 0 ? (
                    <ResponsiveContainer width="100%" height="90%">
                      <BarChart
                        data={popularMajors}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                        <XAxis type="number" />
                        <YAxis dataKey="ten" type="category" width={150} tick={{ fontSize: 12 }} />
                        <Tooltip cursor={{ fill: '#f1f5f9' }} />
                        <Bar
                          dataKey="count"
                          fill="#3b82f6"
                          radius={[0, 4, 4, 0]}
                          barSize={24}
                          name="Lượt tra cứu"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-center text-slate-500 mt-20">
                      Chưa có dữ liệu tra cứu từ người dùng (search_count trên Neo4j).
                    </p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'kg' && (
              <div className="space-y-6">
                <h1 className="text-2xl font-bold text-slate-800">Quản lý Knowledge Graph (Neo4j)</h1>
                <p className="text-slate-500">
                  Xem / cập nhật ngành & điểm chuẩn; rebuild có bước xác nhận <code>confirm=true</code>.
                </p>

                <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 space-y-3">
                  <h3 className="font-semibold text-amber-900 flex items-center gap-2">
                    <RefreshCw size={18} /> Rebuild Knowledge Graph
                  </h3>
                  <label className="flex items-center gap-2 text-sm text-amber-900">
                    <input
                      type="checkbox"
                      checked={rebuildConfirm}
                      onChange={(e) => setRebuildConfirm(e.target.checked)}
                    />
                    Tôi xác nhận thao tác rebuild (xóa dữ liệu graph theo lựa chọn bên dưới).
                  </label>
                  <label className="flex items-center gap-2 text-sm text-amber-900">
                    <input
                      type="checkbox"
                      checked={rebuildFullIngest}
                      onChange={(e) => setRebuildFullIngest(e.target.checked)}
                    />
                    Nạp đầy đủ từ JSON trong <code className="bg-amber-100 px-1 rounded">data/processed</code>{' '}
                    (GraphBuilder)
                  </label>
                  <button
                    type="button"
                    disabled={rebuildBusy}
                    onClick={runRebuild}
                    className="px-4 py-2 rounded-xl bg-amber-600 text-white font-medium hover:bg-amber-700 disabled:opacity-50"
                  >
                    {rebuildBusy ? 'Đang xử lý…' : 'Thực hiện rebuild'}
                  </button>
                </div>

                <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                      type="search"
                      placeholder="Tìm mã ngành, tên, nhóm..."
                      value={majorSearch}
                      onChange={(e) => setMajorSearch(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white"
                    />
                  </div>
                  <span className="text-sm text-slate-500">{filteredMajors.length} ngành</span>
                </div>

                <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                  <div className="overflow-x-auto max-h-[calc(100vh-340px)]">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-slate-100 text-slate-600 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 font-semibold">Mã</th>
                          <th className="px-3 py-2 font-semibold">Tên ngành</th>
                          <th className="px-3 py-2 font-semibold">Nhóm</th>
                          <th className="px-3 py-2 font-semibold">THPT</th>
                          <th className="px-3 py-2 font-semibold">Học bạ</th>
                          <th className="px-3 py-2 font-semibold w-24">Sửa</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {filteredMajors.map((m) => (
                          <tr key={m.ma_nganh} className="hover:bg-slate-50">
                            <td className="px-3 py-2 font-mono text-xs">{m.ma_nganh}</td>
                            <td className="px-3 py-2 max-w-xs truncate" title={m.ten}>
                              {m.ten}
                            </td>
                            <td className="px-3 py-2">{m.nhom}</td>
                            <td className="px-3 py-2">{m.diem_thpt ?? '—'}</td>
                            <td className="px-3 py-2">{m.diem_hocba ?? '—'}</td>
                            <td className="px-3 py-2">
                              <button
                                type="button"
                                onClick={() => openEdit(m)}
                                className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                              >
                                <Edit size={14} /> Sửa
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chatHistory' && (
              <div className="space-y-6">
                <h1 className="text-2xl font-bold text-slate-800">Lịch sử chat toàn hệ thống</h1>
                <p className="text-slate-500">
                  Truy xuất từ <strong>SQLite</strong> qua SQLAlchemy:{' '}
                  <code className="text-xs bg-slate-200 px-1 rounded">User → ChatSession → ChatMessage</code>.
                </p>

                <div className="space-y-4">
                  {chatHistory.length === 0 && (
                    <p className="text-slate-500 text-center py-10">Chưa có phiên chat nào.</p>
                  )}

                  {chatHistory.map((u) => (
                    <div
                      key={u.user_id}
                      className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
                    >
                      <div className="bg-blue-50 px-5 py-3 border-b border-blue-100 flex items-center gap-3 text-blue-800 font-semibold">
                        <Users size={18} /> {u.username}{' '}
                        <span className="text-xs font-normal text-blue-600">(id: {u.user_id})</span>
                      </div>
                      <div className="p-5 space-y-3">
                        {u.sessions.map((s) => {
                          const exKey = `${u.user_id}-${s.session_id}`;
                          const open = !!expandedSessions[exKey];
                          return (
                            <div
                              key={s.session_id}
                              className="border border-slate-200 rounded-lg overflow-hidden"
                            >
                              <button
                                type="button"
                                onClick={() => toggleSessionExpand(exKey)}
                                className="w-full flex items-center gap-2 px-3 py-2 bg-slate-50 text-left text-sm font-medium text-slate-700 hover:bg-slate-100"
                              >
                                {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                Phiên: <span className="font-mono text-xs">{s.session_id}</span> —{' '}
                                {new Date(s.created_at).toLocaleString('vi-VN')} — {s.messages?.length || 0} tin
                              </button>
                              {open && (
                                <div className="p-3 space-y-2 bg-white max-h-[400px] overflow-y-auto">
                                  {(s.messages || []).map((msg, i) => (
                                    <div
                                      key={i}
                                      className={`text-sm p-2 rounded-lg flex gap-2 ${
                                        msg.role === 'user'
                                          ? 'bg-slate-50 text-slate-800 border border-slate-100'
                                          : 'bg-indigo-50 text-indigo-900 border border-indigo-100'
                                      }`}
                                    >
                                      {msg.role === 'user' ? (
                                        <Users size={14} className="shrink-0 mt-0.5 text-slate-500" />
                                      ) : (
                                        <Bot size={14} className="shrink-0 mt-0.5 text-indigo-600" />
                                      )}
                                      <div className="min-w-0 flex-1">
                                        <div className="text-[10px] text-slate-400 uppercase mb-0.5">
                                          {msg.role === 'user' ? 'User' : 'Bot'} ·{' '}
                                          {msg.time
                                            ? new Date(msg.time).toLocaleString('vi-VN')
                                            : ''}
                                        </div>
                                        <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {editingMajor && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Edit size={20} /> Cập nhật: {editingMajor.ma_nganh}
            </h3>
            <label className="block text-sm">
              <span className="text-slate-600">Tên ngành</span>
              <input
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
                value={form.ten}
                onChange={(e) => setForm((f) => ({ ...f, ten: e.target.value }))}
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">Nhóm</span>
              <input
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
                value={form.nhom}
                onChange={(e) => setForm((f) => ({ ...f, nhom: e.target.value }))}
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">Mô tả</span>
              <textarea
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 min-h-[80px]"
                value={form.mo_ta}
                onChange={(e) => setForm((f) => ({ ...f, mo_ta: e.target.value }))}
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm">
                <span className="text-slate-600">Điểm THPT</span>
                <input
                  type="number"
                  step="0.01"
                  className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
                  value={form.diem_thpt}
                  onChange={(e) => setForm((f) => ({ ...f, diem_thpt: e.target.value }))}
                />
              </label>
              <label className="block text-sm">
                <span className="text-slate-600">Điểm học bạ</span>
                <input
                  type="number"
                  step="0.01"
                  className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
                  value={form.diem_hocba}
                  onChange={(e) => setForm((f) => ({ ...f, diem_hocba: e.target.value }))}
                />
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingMajor(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={saveMajor}
                className="px-4 py-2 rounded-xl bg-blue-600 text-white font-medium inline-flex items-center gap-2"
              >
                <Save size={18} /> Lưu lên Neo4j
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
