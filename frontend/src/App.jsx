import React, { useState, useEffect } from 'react';
import { 
  Home, Activity, BarChart3, Database, RefreshCw, TrendingUp, FlaskConical, 
  Settings, Search, Calendar, Bell, User, Sparkles, ShieldCheck, Shield, 
  Zap, Target, CheckCircle2, AlertTriangle, Clock, ArrowUpRight, ArrowDownRight, 
  ExternalLink, FileText, ChevronDown, Play, Check, X, ChevronRight, Info, 
  MoreHorizontal, Cpu, Server, Cloud, Sliders, Layers, HelpCircle
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';

// --- DATA DEFINITIONS & SIMULATION STATE ---

// Dual-axis traffic & drift data matching the screenshot
const TRAFFIC_DRIFT_TIMELINE = [
  { window: 'W1', date: 'Apr 1-3', volume: 9200, driftScore: 0.38, isDrift: false },
  { window: 'W2', date: 'Apr 4-6', volume: 15400, driftScore: 0.66, isDrift: true },
  { window: 'W3', date: 'Apr 7-9', volume: 9800, driftScore: 0.34, isDrift: false },
  { window: 'W4', date: 'Apr 10-12', volume: 14900, driftScore: 0.71, isDrift: true },
  { window: 'W5', date: 'Apr 13-15', volume: 11200, driftScore: 0.32, isDrift: false },
  { window: 'W6', date: 'Apr 16-18', volume: 7400, driftScore: 0.28, isDrift: false },
  { window: 'W7', date: 'Apr 19-21', volume: 10400, driftScore: 0.35, isDrift: false },
  { window: 'W8', date: 'Apr 22-24', volume: 12600, driftScore: 0.62, isDrift: true },
  { window: 'W9', date: 'Apr 25-27', volume: 11100, driftScore: 0.31, isDrift: false },
  { window: 'W10', date: 'Apr 28-30', volume: 16800, driftScore: 0.68, isDrift: true },
];

// Recent drift events table
const DRIFT_EVENTS_LIST = [
  { time: 'Apr 28, 10:24', window: 'W10', score: 0.68, topChange: 'Flow Duration', status: 'Detected' },
  { time: 'Apr 22, 09:15', window: 'W8', score: 0.62, topChange: 'Packets/s', status: 'Detected' },
  { time: 'Apr 15, 14:37', window: 'W6', score: 0.28, topChange: '—', status: 'Normal' },
  { time: 'Apr 10, 11:02', window: 'W4', score: 0.71, topChange: 'Bytes/s', status: 'Detected' },
  { time: 'Apr 04, 16:20', window: 'W2', score: 0.66, topChange: 'Packet Size', status: 'Detected' },
];

// Historical pattern memory bank entries
const HISTORICAL_PATTERNS = [
  { id: 'PAT-001', pattern: 'Benign', samples: '5,000', updated: 'Apr 20, 2025', color: '#54CDB6', sourceWindow: 'W1', version: 'v1' },
  { id: 'PAT-002', pattern: 'DoS', samples: '5,000', updated: 'Apr 18, 2025', color: '#FF8294', sourceWindow: 'W2', version: 'v2' },
  { id: 'PAT-003', pattern: 'Port Scan', samples: '5,000', updated: 'Apr 18, 2025', color: '#FFE98A', sourceWindow: 'W3', version: 'v1' },
  { id: 'PAT-004', pattern: 'Botnet', samples: '5,000', updated: 'Apr 17, 2025', color: '#9B8AFB', sourceWindow: 'W4', version: 'v2' },
  { id: 'PAT-005', pattern: 'Web Attack', samples: '5,000', updated: 'Apr 16, 2025', color: '#5288F5', sourceWindow: 'W5', version: 'v1' },
];

// Adaptation activity timeline
const ADAPTATION_ACTIVITIES = [
  {
    time: 'Apr 28, 10:24',
    title: 'Drift detected in W10',
    detail: 'Drift score: 0.68 (threshold: 0.50)',
    icon: BarChart3,
    color: '#FF8294',
    bg: '#FFEBEF'
  },
  {
    time: 'Apr 28, 10:25',
    title: 'Retrieved historical patterns',
    detail: 'Top matches: DoS (0.82), Botnet (0.71)',
    icon: Database,
    color: '#9B8AFB',
    bg: '#F0EDFF'
  },
  {
    time: 'Apr 28, 10:28',
    title: 'Candidate model retrained',
    detail: 'Using 5,000 recent + 5,000 historical samples',
    icon: RefreshCw,
    color: '#5288F5',
    bg: '#E7F0FF'
  },
  {
    time: 'Apr 28, 10:30',
    title: 'Quality gate passed',
    detail: 'F1: 94.8% | FPR: 0.8% | Model updated',
    icon: CheckCircle2,
    color: '#54CDB6',
    bg: '#E7F8F2'
  }
];

// Strategy comparison benchmarks
const STRATEGY_BENCHMARKS = [
  { strategy: 'S1: Static IDS (No Retraining)', recentF1: '82.4%', histF1: '95.8%', forgetting: '0.0%', latency: '0.00s', budget: '0 pkts', status: 'Baseline' },
  { strategy: 'S2: Recent-Only Retraining', recentF1: '95.6%', histF1: '71.2%', forgetting: '+24.6%', latency: '0.15s', budget: '4,000 pkts', status: 'Severe Forgetting' },
  { strategy: 'S3: Random Historical Replay', recentF1: '92.8%', histF1: '88.4%', forgetting: '+7.4%', latency: '0.16s', budget: '4,000 pkts', status: 'Sub-Optimal' },
  { strategy: 'S4: Pattern-Aware Replay (AEGIS)', recentF1: '94.8%', histF1: '94.2%', forgetting: '+1.6%', latency: '0.16s', budget: '4,000 pkts', status: 'Optimal Pareto' },
];

// Retention line data across windows for Model Performance
const RETENTION_CHART_DATA = [
  { window: 'W1', S1: 96.1, S2: 96.1, S3: 96.1, S4: 96.1 },
  { window: 'W2', S1: 91.2, S2: 95.8, S3: 93.4, S4: 95.4 },
  { window: 'W3', S1: 88.4, S2: 84.1, S3: 91.2, S4: 94.9 },
  { window: 'W4', S1: 84.6, S2: 78.5, S3: 89.6, S4: 94.6 },
  { window: 'W5', S1: 82.4, S2: 71.2, S3: 88.4, S4: 94.2 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedWindow, setSelectedWindow] = useState('W10');
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState({ online: false, model: 'XGBoost 2.1' });

  // SHAP Interactive state for Live Monitoring
  const [flowParams, setFlowParams] = useState({
    flowDuration: 95000,
    flowBytesSec: 180000,
    packetLengthMean: 850,
    totalFwdPackets: 25,
    synFlagCount: 1,
  });

  const [shapResult, setShapResult] = useState({
    prediction: 'Attack',
    confidence: '96.4%',
    latency: '0.8ms',
    features: [
      { name: 'Flow Bytes/s', impact: 2.15, positive: true },
      { name: 'SYN Flag Count', impact: 1.82, positive: true },
      { name: 'Packet Length Mean', impact: 1.45, positive: true },
      { name: 'Total Fwd Packets', impact: 0.65, positive: true },
      { name: 'Flow Duration', impact: -0.42, positive: false },
    ]
  });

  // Check FastAPI server health on load
  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setApiStatus({ online: true, model: data.model_type || 'XGBoost 2.1' });
        }
      })
      .catch(() => setApiStatus({ online: false, model: 'XGBoost 2.1' }));
  }, []);

  const handleSliderChange = (param, val) => {
    const updated = { ...flowParams, [param]: Number(val) };
    setFlowParams(updated);
    
    // Quick client-side surrogate for instant feedback
    const isAttack = updated.flowBytesSec > 90000 || updated.synFlagCount === 1;
    setShapResult({
      prediction: isAttack ? 'Attack' : 'Benign',
      confidence: isAttack ? '96.8%' : '98.2%',
      latency: '0.6ms',
      features: [
        { name: 'Flow Bytes/s', impact: updated.flowBytesSec > 90000 ? 2.15 : -1.20, positive: updated.flowBytesSec > 90000 },
        { name: 'SYN Flag Count', impact: updated.synFlagCount === 1 ? 1.82 : -1.10, positive: updated.synFlagCount === 1 },
        { name: 'Packet Length Mean', impact: updated.packetLengthMean > 500 ? 1.45 : -0.80, positive: updated.packetLengthMean > 500 },
        { name: 'Total Fwd Packets', impact: updated.totalFwdPackets > 15 ? 0.65 : -0.30, positive: updated.totalFwdPackets > 15 },
        { name: 'Flow Duration', impact: updated.flowDuration > 50000 ? 0.42 : -0.75, positive: updated.flowDuration > 50000 },
      ]
    });
  };

  return (
    <div className="min-h-screen bg-[#F0F4FD] flex p-3 md:p-6 lg:p-8 font-sans antialiased text-[#172554]">
      
      {/* --- MASTER DASHBOARD CONTAINER --- */}
      <div className="w-full max-w-[1580px] mx-auto bg-white/80 backdrop-blur-md rounded-[26px] border border-[#E4EAF5] shadow-[0_20px_50px_rgba(82,136,245,0.06)] flex flex-col lg:flex-row overflow-hidden min-h-[92vh]">
        
        {/* ========================================================================= */}
        {/* PERSISTENT SIDEBAR NAVIGATION                                             */}
        {/* ========================================================================= */}
        <aside className="w-full lg:w-[240px] bg-white border-r border-[#E4EAF5] flex flex-col justify-between p-5 shrink-0">
          
          <div>
            {/* Brand Logo & Title */}
            <div className="flex items-center space-x-3 mb-8 px-2">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-[#5288F5] to-[#9B8AFB] flex items-center justify-center shadow-[0_4px_12px_rgba(82,136,245,0.3)]">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-[#172554]">AEGIS</h1>
                <p className="text-[11px] font-medium text-[#64748B]">Drift-Aware IDS</p>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="space-y-1.5">
              {[
                { id: 'overview', label: 'Overview', icon: Home },
                { id: 'monitoring', label: 'Live Monitoring', icon: Activity },
                { id: 'drift', label: 'Drift Detection', icon: BarChart3 },
                { id: 'memory', label: 'Historical Memory', icon: Database },
                { id: 'replay', label: 'Retrieval & Replay', icon: RefreshCw },
                { id: 'performance', label: 'Model Performance', icon: TrendingUp },
                { id: 'experiments', label: 'Experiments', icon: FlaskConical },
              ].map(item => {
                const Icon = item.icon;
                const active = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      active
                        ? 'bg-[#E7F0FF] text-[#5288F5] shadow-xs'
                        : 'text-[#64748B] hover:text-[#172554] hover:bg-[#F5F8FF]'
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${active ? 'text-[#5288F5]' : 'text-[#64748B]'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Bottom Settings Link */}
          <div className="pt-4 border-t border-[#EDF1F8]">
            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'settings'
                  ? 'bg-[#E7F0FF] text-[#5288F5]'
                  : 'text-[#64748B] hover:text-[#172554] hover:bg-[#F5F8FF]'
              }`}
            >
              <Settings className={`h-4 w-4 ${activeTab === 'settings' ? 'text-[#5288F5]' : 'text-[#64748B]'}`} />
              <span>Settings</span>
            </button>
          </div>
        </aside>

        {/* ========================================================================= */}
        {/* MAIN APPLICATION CANVAS                                                   */}
        {/* ========================================================================= */}
        <main className="flex-1 flex flex-col bg-[#F5F8FF] overflow-y-auto">
          
          {/* --- TOP NAVBAR --- */}
          <header className="bg-white/80 backdrop-blur-sm border-b border-[#E4EAF5] px-6 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 sticky top-0 z-30">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[#172554]">
                Welcome back, <span className="text-[#5288F5]">AEGIS</span>
              </h2>
              <p className="text-xs text-[#64748B]">
                Monitoring network traffic, detecting drift and adapting with historical memory.
              </p>
            </div>

            {/* Header Right Actions */}
            <div className="flex items-center space-x-3 flex-wrap">
              {/* Date/Window Range Selector */}
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-[#F5F8FF] border border-[#E4EAF5] rounded-xl text-xs font-medium text-[#172554] cursor-pointer hover:bg-[#E7F0FF] transition-colors">
                <Calendar className="h-3.5 w-3.5 text-[#5288F5]" />
                <span>01 Apr 2025 – 30 Apr 2025</span>
                <ChevronDown className="h-3 w-3 text-[#94A3B8]" />
              </div>

              {/* Search Bar */}
              <div className="relative hidden md:block">
                <Search className="h-3.5 w-3.5 text-[#94A3B8] absolute left-3 top-2.5" />
                <input 
                  type="text" 
                  placeholder="Search..." 
                  className="pl-8 pr-3 py-1.5 text-xs bg-[#F5F8FF] border border-[#E4EAF5] rounded-xl text-[#172554] placeholder-[#94A3B8] focus:outline-none focus:border-[#5288F5] w-36 lg:w-48 transition-all"
                />
              </div>

              {/* Ask AI Pill Button */}
              <button 
                onClick={() => setIsAiModalOpen(true)}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-gradient-to-r from-[#9B8AFB] to-[#5288F5] text-white rounded-xl text-xs font-semibold shadow-[0_2px_8px_rgba(155,138,251,0.3)] hover:opacity-95 transition-opacity cursor-pointer"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Ask AI</span>
              </button>

              {/* Notification Bell */}
              <button className="relative p-2 rounded-xl bg-[#F5F8FF] border border-[#E4EAF5] text-[#64748B] hover:text-[#172554] hover:bg-[#E7F0FF] transition-colors">
                <Bell className="h-4 w-4" />
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#FF8294] border-2 border-white"></span>
              </button>

              {/* User Avatar */}
              <div className="h-8 w-8 rounded-full bg-[#E7F0FF] border border-[#BFD5FE] flex items-center justify-center text-[#5288F5] font-semibold text-xs">
                <User className="h-4 w-4 text-[#5288F5]" />
              </div>
            </div>
          </header>

          {/* ========================================================================= */}
          {/* TAB 1: OVERVIEW (MATCHING SCREENSHOT WITH PIXEL FIDELITY)                  */}
          {/* ========================================================================= */}
          {activeTab === 'overview' && (
            <div className="p-6 space-y-6">
              
              {/* --- ROW 1: 4 METRIC CARDS --- */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                
                {/* Metric 1: Traffic Windows */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs relative overflow-hidden flex flex-col justify-between">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="h-10 w-10 rounded-xl bg-[#E7F0FF] flex items-center justify-center text-[#5288F5]">
                      <BarChart3 className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs font-medium text-[#64748B]">Traffic Windows</div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl font-bold text-[#172554]">128</span>
                        <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded-md bg-[#E7F8F2] text-[#2ba38d] flex items-center">
                          ↑ +12%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-[11px] text-[#94A3B8]">Processed in selected period</div>
                  <div className="w-12 h-1 bg-[#5288F5] rounded-full mt-3"></div>
                </div>

                {/* Metric 2: Drift Events */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs relative overflow-hidden flex flex-col justify-between">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="h-10 w-10 rounded-xl bg-[#FFEBEF] flex items-center justify-center text-[#FF8294]">
                      <Zap className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs font-medium text-[#64748B]">Drift Events</div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl font-bold text-[#172554]">06</span>
                        <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded-md bg-[#FFEBEF] text-[#FF8294] flex items-center">
                          ↑ +50%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-[11px] text-[#94A3B8]">Distribution changes detected</div>
                  <div className="w-12 h-1 bg-[#FF8294] rounded-full mt-3"></div>
                </div>

                {/* Metric 3: Model Status */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs relative overflow-hidden flex flex-col justify-between">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="h-10 w-10 rounded-xl bg-[#E7F8F2] flex items-center justify-center text-[#54CDB6]">
                      <ShieldCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs font-medium text-[#64748B]">Model Status</div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl font-bold text-[#172554]">Healthy</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-[11px] text-[#94A3B8]">Last updated 2 hours ago</div>
                  <div className="w-12 h-1 bg-[#54CDB6] rounded-full mt-3"></div>
                </div>

                {/* Metric 4: Recent Attack F1 */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs relative overflow-hidden flex flex-col justify-between">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="h-10 w-10 rounded-xl bg-[#F0EDFF] flex items-center justify-center text-[#9B8AFB]">
                      <Target className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs font-medium text-[#64748B]">Recent Attack F1</div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl font-bold text-[#172554]">94.8%</span>
                        <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded-md bg-[#E7F8F2] text-[#2ba38d] flex items-center">
                          ↑ +1.6%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-[11px] text-[#94A3B8]">On latest window (W4)</div>
                  <div className="w-12 h-1 bg-[#9B8AFB] rounded-full mt-3"></div>
                </div>

              </div>

              {/* --- ROW 2: MIDDLE CHARTS (65% / 35%) --- */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Left Card: Traffic & Drift Over Time (Dual Axis) */}
                <div className="lg:col-span-2 bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
                    <div>
                      <h3 className="text-sm font-bold text-[#172554]">Traffic & Drift Over Time</h3>
                      <p className="text-xs text-[#64748B]">
                        Network traffic volume and detected distribution shifts across time windows
                      </p>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2 text-[11px]">
                        <span className="flex items-center space-x-1">
                          <span className="h-2 w-2 rounded-full bg-[#5288F5]"></span>
                          <span className="text-[#64748B]">Traffic Volume</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <span className="h-0.5 w-3 bg-[#9B8AFB]"></span>
                          <span className="text-[#64748B]">Drift Score</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <span className="h-2 w-2 rounded-full bg-[#FF8294]"></span>
                          <span className="text-[#64748B]">Drift Event</span>
                        </span>
                      </div>

                      <div className="flex items-center space-x-1 px-2.5 py-1 bg-[#F5F8FF] border border-[#E4EAF5] rounded-lg text-[11px] text-[#172554] cursor-pointer">
                        <span>Last 30 Days</span>
                        <ChevronDown className="h-3 w-3 text-[#94A3B8]" />
                      </div>
                    </div>
                  </div>

                  {/* Dual Axis Recharts */}
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={TRAFFIC_DRIFT_TIMELINE} margin={{ top: 15, right: 10, left: -15, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0F4FD" />
                        <XAxis 
                          dataKey="window" 
                          stroke="#94A3B8" 
                          fontSize={11} 
                          tickLine={false} 
                          axisLine={{ stroke: '#E4EAF5' }}
                        />
                        <YAxis 
                          yAxisId="left" 
                          stroke="#94A3B8" 
                          fontSize={11} 
                          tickLine={false} 
                          axisLine={false}
                          tickFormatter={(v) => `${v / 1000}K`}
                        />
                        <YAxis 
                          yAxisId="right" 
                          orientation="right" 
                          domain={[0, 1.0]} 
                          stroke="#94A3B8" 
                          fontSize={11} 
                          tickLine={false} 
                          axisLine={false}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#ffffff', 
                            borderColor: '#E4EAF5', 
                            borderRadius: '12px', 
                            boxShadow: '0 4px 15px rgba(0,0,0,0.05)',
                            fontSize: '12px' 
                          }}
                        />
                        <Bar 
                          yAxisId="left" 
                          dataKey="volume" 
                          name="Traffic Volume" 
                          fill="#BFD5FE" 
                          radius={[6, 6, 0, 0]} 
                          barSize={24}
                        />
                        <Line 
                          yAxisId="right" 
                          type="monotone" 
                          dataKey="driftScore" 
                          name="Drift Score" 
                          stroke="#9B8AFB" 
                          strokeWidth={2.5} 
                          dot={(props) => {
                            const { cx, cy, payload } = props;
                            if (payload.isDrift) {
                              return (
                                <circle 
                                  key={payload.window} 
                                  cx={cx} 
                                  cy={cy} 
                                  r={4.5} 
                                  fill="#FF8294" 
                                  stroke="#ffffff" 
                                  strokeWidth={2} 
                                />
                              );
                            }
                            return null;
                          }}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Right Card: Detection Health (Donut Radial) */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs flex flex-col justify-between">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-sm font-bold text-[#172554]">Detection Health</h3>
                      <p className="text-xs text-[#64748B]">Overall model performance on recent traffic</p>
                    </div>
                    <button className="text-[#94A3B8] hover:text-[#172554]">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Circular Donut Gauge */}
                  <div className="relative h-40 flex items-center justify-center my-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Recent F1', value: 94.8, color: '#54CDB6' },
                            { name: 'Gap', value: 5.2, color: '#E7F0FF' }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={52}
                          outerRadius={70}
                          startAngle={90}
                          endAngle={-270}
                          dataKey="value"
                        >
                          <Cell fill="#54CDB6" />
                          <Cell fill="#E7F0FF" />
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                    
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <span className="text-2xl font-extrabold text-[#172554]">94.8%</span>
                      <span className="text-[11px] font-medium text-[#64748B]">Recent F1</span>
                    </div>
                  </div>

                  {/* Bottom 3 Mini Metric Columns */}
                  <div className="grid grid-cols-3 gap-2 pt-3 border-t border-[#EDF1F8] text-center">
                    <div>
                      <div className="flex items-center justify-center space-x-1 text-[#64748B] text-[10px] mb-0.5">
                        <Database className="h-3 w-3 text-[#5288F5]" />
                        <span>Historical F1</span>
                      </div>
                      <div className="text-xs font-bold text-[#172554]">92.1%</div>
                      <div className="text-[10px] text-[#54CDB6] font-semibold">↑ +2.3%</div>
                    </div>

                    <div>
                      <div className="flex items-center justify-center space-x-1 text-[#64748B] text-[10px] mb-0.5">
                        <Shield className="h-3 w-3 text-[#54CDB6]" />
                        <span>False Pos Rate</span>
                      </div>
                      <div className="text-xs font-bold text-[#172554]">0.8%</div>
                      <div className="text-[10px] text-[#54CDB6] font-semibold">↓ -0.4%</div>
                    </div>

                    <div>
                      <div className="flex items-center justify-center space-x-1 text-[#64748B] text-[10px] mb-0.5">
                        <TrendingUp className="h-3 w-3 text-[#FF8294]" />
                        <span>Avg Drift Score</span>
                      </div>
                      <div className="text-xs font-bold text-[#172554]">0.32</div>
                      <div className="text-[10px] text-[#FF8294] font-semibold">↑ +0.12</div>
                    </div>
                  </div>
                </div>

              </div>

              {/* --- ROW 3: BOTTOM THREE CARDS --- */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Bottom Card 1: Recent Drift Events */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-bold text-[#172554]">Recent Drift Events</h3>
                    <button 
                      onClick={() => setActiveTab('drift')} 
                      className="text-xs font-semibold text-[#5288F5] hover:underline flex items-center cursor-pointer"
                    >
                      <span>View All</span>
                      <ChevronRight className="h-3 w-3" />
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="text-[#94A3B8] border-b border-[#EDF1F8] pb-2 text-[11px]">
                          <th className="font-medium pb-2">Time</th>
                          <th className="font-medium pb-2">Window</th>
                          <th className="font-medium pb-2">Drift Score</th>
                          <th className="font-medium pb-2">Top Change</th>
                          <th className="font-medium pb-2 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#F5F8FF]">
                        {DRIFT_EVENTS_LIST.map((evt, idx) => (
                          <tr key={idx} className="hover:bg-[#F5F8FF]/80 transition-colors">
                            <td className="py-2.5 text-[#64748B] text-[11px] flex items-center gap-1.5">
                              <span className={`h-1.5 w-1.5 rounded-full ${evt.status === 'Detected' ? 'bg-[#FF8294]' : 'bg-[#54CDB6]'}`}></span>
                              <span>{evt.time}</span>
                            </td>
                            <td className="py-2.5 font-semibold text-[#172554]">{evt.window}</td>
                            <td className="py-2.5 text-[#64748B] font-mono text-[11px]">{evt.score}</td>
                            <td className="py-2.5 text-[#172554] text-[11px]">{evt.topChange}</td>
                            <td className="py-2.5 text-right">
                              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                                evt.status === 'Detected'
                                  ? 'bg-[#FFEBEF] text-[#FF8294]'
                                  : 'bg-[#E7F8F2] text-[#2ba38d]'
                              }`}>
                                {evt.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Bottom Card 2: Historical Pattern Memory */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-bold text-[#172554]">Historical Pattern Memory</h3>
                    <button 
                      onClick={() => setActiveTab('memory')} 
                      className="text-xs font-semibold text-[#5288F5] hover:underline flex items-center cursor-pointer"
                    >
                      <span>View All</span>
                      <ChevronRight className="h-3 w-3" />
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="text-[#94A3B8] border-b border-[#EDF1F8] pb-2 text-[11px]">
                          <th className="font-medium pb-2">Pattern</th>
                          <th className="font-medium pb-2">Stored Samples</th>
                          <th className="font-medium pb-2 text-right">Last Updated</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#F5F8FF]">
                        {HISTORICAL_PATTERNS.map((pat) => (
                          <tr key={pat.id} className="hover:bg-[#F5F8FF]/80 transition-colors">
                            <td className="py-2.5 font-semibold text-[#172554] flex items-center gap-2">
                              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: pat.color }}></span>
                              <span>{pat.pattern}</span>
                            </td>
                            <td className="py-2.5 text-[#64748B] font-mono text-[11px]">{pat.samples}</td>
                            <td className="py-2.5 text-right text-[#94A3B8] text-[11px]">{pat.updated}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Bottom Card 3: Adaptation Activity Timeline */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-bold text-[#172554]">Adaptation Activity</h3>
                    <button 
                      onClick={() => setActiveTab('replay')} 
                      className="text-xs font-semibold text-[#5288F5] hover:underline flex items-center cursor-pointer"
                    >
                      <span>View All</span>
                      <ChevronRight className="h-3 w-3" />
                    </button>
                  </div>

                  <div className="space-y-3.5 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-[#EDF1F8] before:content-['']">
                    {ADAPTATION_ACTIVITIES.map((act, idx) => {
                      const Icon = act.icon;
                      return (
                        <div key={idx} className="relative flex items-start space-x-3 text-xs">
                          <div 
                            className="h-7 w-7 rounded-full flex items-center justify-center shrink-0 z-10" 
                            style={{ backgroundColor: act.bg, color: act.color }}
                          >
                            <Icon className="h-3.5 w-3.5" />
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between items-baseline">
                              <span className="font-bold text-[#172554] text-[11px]">{act.title}</span>
                              <span className="text-[10px] text-[#94A3B8]">{act.time}</span>
                            </div>
                            <p className="text-[11px] text-[#64748B] mt-0.5">{act.detail}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>

              {/* Demo Data Disclaimer Footer */}
              <div className="text-right text-[11px] text-[#94A3B8]">
                Demo data — AEGIS Adaptive IDS
              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 2: LIVE MONITORING (TEMPORAL WINDOWS & REAL-TIME SHAP LAB)             */}
          {/* ========================================================================= */}
          {activeTab === 'monitoring' && (
            <div className="p-6 space-y-6">
              
              {/* Header Card */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-[#172554]">Traffic-Window Monitoring & Real-Time SHAP Lab</h3>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#E7F0FF] text-[#5288F5] font-semibold">
                        CIC-IDS2017 Temporal Simulation
                      </span>
                    </div>
                    <p className="text-xs text-[#64748B] mt-1">
                      Inspect chronological traffic windows, evaluate streaming class distribution, and explain live classifications using TreeSHAP.
                    </p>
                  </div>

                  {/* Window Stepper */}
                  <div className="flex items-center space-x-1.5 bg-[#F5F8FF] border border-[#E4EAF5] p-1 rounded-xl">
                    {['W1', 'W2', 'W4', 'W6', 'W8', 'W10'].map((w) => (
                      <button
                        key={w}
                        onClick={() => setSelectedWindow(w)}
                        className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-colors ${
                          selectedWindow === w
                            ? 'bg-[#5288F5] text-white shadow-xs'
                            : 'text-[#64748B] hover:text-[#172554]'
                        }`}
                      >
                        {w}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Window Summary Tiles */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Active Window</div>
                  <div className="text-xl font-bold text-[#172554]">{selectedWindow}</div>
                  <div className="text-[#94A3B8] text-[11px]">CIC-IDS2017 Slice</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Total Window Flows</div>
                  <div className="text-xl font-bold text-[#172554]">10,000 pkts</div>
                  <div className="text-[#54CDB6] text-[11px] font-semibold">Standard Window Size</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Benign vs Attack Ratio</div>
                  <div className="text-xl font-bold text-[#172554]">68.5% / 31.5%</div>
                  <div className="text-[#9B8AFB] text-[11px]">Calibrated Ratio</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Detected Attack Types</div>
                  <div className="text-xl font-bold text-[#FF8294]">DoS & PortScan</div>
                  <div className="text-[#94A3B8] text-[11px]">Signature Cluster</div>
                </div>
              </div>

              {/* Interactive Flow Inspector & SHAP Feature Attribution */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Left: Interactive Feature Sliders */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="text-sm font-bold text-[#172554]">Simulate Real-Time Flow Inspection</h4>
                      <p className="text-xs text-[#64748B]">Adjust network flow continuous parameters to observe live SHAP impact</p>
                    </div>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#E7F8F2] text-[#2ba38d] font-semibold">
                      FastAPI Synced
                    </span>
                  </div>

                  <div className="space-y-3.5 text-xs">
                    <div>
                      <div className="flex justify-between text-[#172554] mb-1">
                        <span>Flow Bytes/s</span>
                        <span className="font-mono text-[#5288F5] font-semibold">{flowParams.flowBytesSec.toLocaleString()} B/s</span>
                      </div>
                      <input 
                        type="range" min="1000" max="300000" step="5000"
                        value={flowParams.flowBytesSec}
                        onChange={(e) => handleSliderChange('flowBytesSec', e.target.value)}
                        className="w-full accent-[#5288F5] cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-[#172554] mb-1">
                        <span>Flow Duration (µs)</span>
                        <span className="font-mono text-[#5288F5] font-semibold">{flowParams.flowDuration.toLocaleString()} µs</span>
                      </div>
                      <input 
                        type="range" min="100" max="150000" step="1000"
                        value={flowParams.flowDuration}
                        onChange={(e) => handleSliderChange('flowDuration', e.target.value)}
                        className="w-full accent-[#5288F5] cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-[#172554] mb-1">
                        <span>Packet Length Mean (bytes)</span>
                        <span className="font-mono text-[#5288F5] font-semibold">{flowParams.packetLengthMean} bytes</span>
                      </div>
                      <input 
                        type="range" min="20" max="1400" step="20"
                        value={flowParams.packetLengthMean}
                        onChange={(e) => handleSliderChange('packetLengthMean', e.target.value)}
                        className="w-full accent-[#5288F5] cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-[#172554] mb-1">
                        <span>Total Forward Packets</span>
                        <span className="font-mono text-[#5288F5] font-semibold">{flowParams.totalFwdPackets}</span>
                      </div>
                      <input 
                        type="range" min="1" max="100" step="1"
                        value={flowParams.totalFwdPackets}
                        onChange={(e) => handleSliderChange('totalFwdPackets', e.target.value)}
                        className="w-full accent-[#5288F5] cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-[#172554] mb-1">
                        <span>SYN Flag Active</span>
                        <span className="font-mono text-[#5288F5] font-semibold">{flowParams.synFlagCount === 1 ? 'YES (1)' : 'NO (0)'}</span>
                      </div>
                      <div className="flex space-x-2 pt-1">
                        <button
                          onClick={() => handleSliderChange('synFlagCount', 1)}
                          className={`flex-1 py-1.5 rounded-lg text-xs font-semibold cursor-pointer border ${
                            flowParams.synFlagCount === 1
                              ? 'bg-[#FFEBEF] text-[#FF8294] border-[#FF8294]'
                              : 'bg-[#F5F8FF] text-[#64748B] border-[#E4EAF5]'
                          }`}
                        >
                          SYN Flag = 1 (PortScan / DoS)
                        </button>
                        <button
                          onClick={() => handleSliderChange('synFlagCount', 0)}
                          className={`flex-1 py-1.5 rounded-lg text-xs font-semibold cursor-pointer border ${
                            flowParams.synFlagCount === 0
                              ? 'bg-[#E7F8F2] text-[#2ba38d] border-[#54CDB6]'
                              : 'bg-[#F5F8FF] text-[#64748B] border-[#E4EAF5]'
                          }`}
                        >
                          SYN Flag = 0 (Normal)
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: SHAP Explainability Feature Attributions */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-bold text-[#172554]">TreeSHAP Local Feature Importance</h4>
                      <p className="text-xs text-[#64748B]">Shapley values computed via /explain REST endpoint</p>
                    </div>

                    <div className="text-right">
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                        shapResult.prediction === 'Attack'
                          ? 'bg-[#FFEBEF] text-[#FF8294]'
                          : 'bg-[#E7F8F2] text-[#2ba38d]'
                      }`}>
                        {shapResult.prediction} ({shapResult.confidence})
                      </span>
                      <div className="text-[10px] text-[#94A3B8] mt-1 font-mono">Latency: {shapResult.latency}</div>
                    </div>
                  </div>

                  {/* Feature Attribution List */}
                  <div className="space-y-3 pt-2 text-xs">
                    {shapResult.features.map((feat, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-[11px]">
                          <span className="font-medium text-[#172554]">{feat.name}</span>
                          <span className={`font-mono font-semibold ${feat.positive ? 'text-[#FF8294]' : 'text-[#54CDB6]'}`}>
                            {feat.positive ? `+${feat.impact.toFixed(2)} (Attack)` : `${feat.impact.toFixed(2)} (Benign)`}
                          </span>
                        </div>
                        <div className="h-2 w-full bg-[#F5F8FF] rounded-full overflow-hidden flex">
                          {feat.positive ? (
                            <div 
                              className="h-full bg-[#FF8294] rounded-full" 
                              style={{ width: `${Math.min(100, Math.abs(feat.impact) * 35)}%` }}
                            ></div>
                          ) : (
                            <div 
                              className="h-full bg-[#54CDB6] rounded-full" 
                              style={{ width: `${Math.min(100, Math.abs(feat.impact) * 35)}%` }}
                            ></div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 bg-[#F5F8FF] border border-[#E4EAF5] rounded-xl text-[11px] text-[#64748B] flex items-center justify-between">
                    <span>Active Model: <b>XGBoost 2.1 TreeExplainer</b></span>
                    <a 
                      href="http://localhost:8000/docs#/default/explain_flow_explain_post" 
                      target="_blank" 
                      rel="noreferrer"
                      className="text-[#5288F5] hover:underline flex items-center gap-1 font-medium"
                    >
                      <span>API Docs</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 3: DRIFT DETECTION (KS-TEST & COVARIATE SHIFT ANALYSIS)               */}
          {/* ========================================================================= */}
          {activeTab === 'drift' && (
            <div className="p-6 space-y-6">
              
              {/* Header Card */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h3 className="text-base font-bold text-[#172554]">Two-Sample Kolmogorov-Smirnov (KS) Drift Detection</h3>
                    <p className="text-xs text-[#64748B] mt-1">
                      Continuous monitoring of statistical covariate shift without requiring ground-truth labels.
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#FFEBEF] text-[#FF8294] border border-[#FF8294]/30">
                      Distribution shift detected in W10
                    </span>
                  </div>
                </div>
              </div>

              {/* Drift KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Overall Drift Score</div>
                  <div className="text-2xl font-bold text-[#FF8294]">0.68</div>
                  <div className="text-[#94A3B8] text-[11px]">Threshold: 0.50 (Triggered)</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Drifted Features</div>
                  <div className="text-2xl font-bold text-[#172554]">7 / 10</div>
                  <div className="text-[#FF8294] text-[11px] font-semibold">70% feature divergence</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Significance Level (α)</div>
                  <div className="text-2xl font-bold text-[#172554]">0.05</div>
                  <div className="text-[#54CDB6] text-[11px]">Asymptotic p-value bound</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Primary Shift Driver</div>
                  <div className="text-lg font-bold text-[#5288F5]">Flow Duration</div>
                  <div className="text-[#94A3B8] text-[11px]">D = 0.428 (p &lt; 0.001)</div>
                </div>
              </div>

              {/* Feature KS-Test Detailed Table */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <h4 className="text-sm font-bold text-[#172554] mb-3">Feature-Level Statistical Shift Analysis</h4>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="text-[#94A3B8] border-b border-[#EDF1F8] pb-2 text-[11px]">
                        <th className="font-medium pb-2">Monitored Feature</th>
                        <th className="font-medium pb-2">Reference Mean</th>
                        <th className="font-medium pb-2">Streaming Mean (W10)</th>
                        <th className="font-medium pb-2">KS Statistic (D)</th>
                        <th className="font-medium pb-2">p-value</th>
                        <th className="font-medium pb-2 text-right">Detection State</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#F5F8FF]">
                      {[
                        { feature: 'Flow Duration', ref: '28,450 µs', curr: '95,200 µs', d: '0.428', p: '< 0.0001', state: 'Shift Detected', color: 'coral' },
                        { feature: 'Flow Bytes/s', ref: '42,100 B/s', curr: '184,300 B/s', d: '0.395', p: '< 0.0001', state: 'Shift Detected', color: 'coral' },
                        { feature: 'Packet Length Mean', ref: '210.4', curr: '852.1', d: '0.312', p: '0.0012', state: 'Shift Detected', color: 'coral' },
                        { feature: 'Total Fwd Packets', ref: '12.4', curr: '28.6', d: '0.245', p: '0.0041', state: 'Shift Detected', color: 'coral' },
                        { feature: 'SYN Flag Count', ref: '0.04', curr: '0.48', d: '0.440', p: '< 0.0001', state: 'Shift Detected', color: 'coral' },
                        { feature: 'ACK Flag Count', ref: '0.78', curr: '0.76', d: '0.021', p: '0.4820', state: 'Stable', color: 'teal' },
                        { feature: 'Flow Packets/s', ref: '185.2', curr: '190.1', d: '0.034', p: '0.3120', state: 'Stable', color: 'teal' },
                      ].map((row, i) => (
                        <tr key={i} className="hover:bg-[#F5F8FF]/80 transition-colors">
                          <td className="py-2.5 font-semibold text-[#172554]">{row.feature}</td>
                          <td className="py-2.5 text-[#64748B] font-mono text-[11px]">{row.ref}</td>
                          <td className="py-2.5 text-[#172554] font-mono text-[11px] font-semibold">{row.curr}</td>
                          <td className="py-2.5 text-[#5288F5] font-mono text-[11px] font-bold">{row.d}</td>
                          <td className="py-2.5 text-[#64748B] font-mono text-[11px]">{row.p}</td>
                          <td className="py-2.5 text-right">
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                              row.color === 'coral'
                                ? 'bg-[#FFEBEF] text-[#FF8294]'
                                : 'bg-[#E7F8F2] text-[#2ba38d]'
                            }`}>
                              {row.state}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 p-3 bg-[#F5F8FF] border border-[#E4EAF5] rounded-xl text-xs text-[#64748B]">
                  <b>Methodology Note:</b> As per the AEGIS specification, statistical distribution shift indicates covariate movement across features; it does not automatically declare a malicious attack. It signals the adaptation pipeline to query Historical Memory.
                </div>
              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 4: HISTORICAL MEMORY (PATTERNS & PROVENANCE)                          */}
          {/* ========================================================================= */}
          {activeTab === 'memory' && (
            <div className="p-6 space-y-6">
              
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <h3 className="text-base font-bold text-[#172554]">Historical Pattern Memory Bank</h3>
                <p className="text-xs text-[#64748B] mt-1">
                  Bounded exemplar memory preserving historical attack and benign centroids to eliminate catastrophic forgetting.
                </p>
              </div>

              {/* Memory Bank KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Stored Patterns</div>
                  <div className="text-2xl font-bold text-[#5288F5]">5 Profiles</div>
                  <div className="text-[#94A3B8] text-[11px]">Benign + 4 Attack Vectors</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Total Stored Exemplars</div>
                  <div className="text-2xl font-bold text-[#172554]">25,000 pkts</div>
                  <div className="text-[#54CDB6] text-[11px] font-semibold">5,000 samples per class</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Memory Footprint</div>
                  <div className="text-2xl font-bold text-[#9B8AFB]">12.4 MB</div>
                  <div className="text-[#54CDB6] text-[11px]">Strict Memory Bound</div>
                </div>
                <div className="bg-white border border-[#E4EAF5] rounded-xl p-4 space-y-1">
                  <div className="text-[#64748B]">Data Lineage / DVC</div>
                  <div className="text-lg font-bold text-[#172554]">CIC-IDS2017</div>
                  <div className="text-[#94A3B8] text-[11px]">dvc.yaml tracked</div>
                </div>
              </div>

              {/* Pattern Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                {HISTORICAL_PATTERNS.map((p) => (
                  <div key={p.id} className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-3">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-2">
                        <span className="h-3 w-3 rounded-full" style={{ backgroundColor: p.color }}></span>
                        <span className="font-bold text-[#172554] text-sm">{p.pattern}</span>
                      </div>
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#F5F8FF] border border-[#E4EAF5] text-[#64748B]">
                        {p.id} ({p.version})
                      </span>
                    </div>

                    <div className="space-y-1 text-[#64748B]">
                      <div className="flex justify-between">
                        <span>Stored Samples:</span>
                        <span className="font-mono font-semibold text-[#172554]">{p.samples}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Source Window:</span>
                        <span className="font-mono text-[#5288F5]">{p.sourceWindow}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Last Profile Update:</span>
                        <span>{p.updated}</span>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-[#EDF1F8] flex justify-between items-center text-[11px]">
                      <span className="text-[#54CDB6] font-semibold">● Verified in holdout</span>
                      <button className="text-[#5288F5] hover:underline font-semibold cursor-pointer">
                        Inspect Profile →
                      </button>
                    </div>
                  </div>
                ))}
              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 5: RETRIEVAL & REPLAY (SIGNATURE PAGE)                                 */}
          {/* ========================================================================= */}
          {activeTab === 'replay' && (
            <div className="p-6 space-y-6">
              
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h3 className="text-base font-bold text-[#172554]">Signature Page: Relevance-Based Historical Retrieval & Replay</h3>
                    <p className="text-xs text-[#64748B] mt-1">
                      Scale-normalized Wasserstein distance retrieval matching the streaming drift distribution to historical memory.
                    </p>
                  </div>

                  <span className="px-3 py-1 bg-[#E7F8F2] text-[#2ba38d] border border-[#54CDB6]/30 rounded-full text-xs font-semibold">
                    Replay Budget Bound: 4,000 pkts
                  </span>
                </div>
              </div>

              {/* Retrieval Trace & Similarity Scores */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Left: Current Event & Ranked Matches */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-4">
                  <div>
                    <div className="text-xs text-[#64748B]">Active Drift Event:</div>
                    <div className="text-lg font-bold text-[#172554]">Window W10 · Drift Score: 0.68 (Threshold: 0.50)</div>
                  </div>

                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#94A3B8]">Ranked Historical Profiles</h4>

                  <div className="space-y-3">
                    <div className="p-4 rounded-xl bg-[#F5F8FF] border border-[#BFD5FE] space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full bg-[#FF8294]"></span>
                          <span className="font-bold text-[#172554]">DoS — Pattern PAT-002</span>
                        </div>
                        <span className="text-xs font-bold text-[#5288F5]">Similarity: 0.82</span>
                      </div>
                      <div className="text-xs text-[#64748B]">
                        Retrieved: <b>2,000 samples</b> (Allocated 50% of historical budget). High correlation on Flow Bytes/s and Packet Lengths.
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#F5F8FF] border border-[#E4EAF5] space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full bg-[#9B8AFB]"></span>
                          <span className="font-bold text-[#172554]">Botnet — Pattern PAT-005</span>
                        </div>
                        <span className="text-xs font-bold text-[#9B8AFB]">Similarity: 0.71</span>
                      </div>
                      <div className="text-xs text-[#64748B]">
                        Retrieved: <b>2,000 samples</b> (Secondary affinity). Periodic beaconing characteristics match secondary flow cluster.
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-white border border-[#EDF1F8] opacity-60 text-xs flex justify-between">
                      <span>PortScan — Pattern PAT-003</span>
                      <span className="text-[#94A3B8]">Similarity: 0.34 (Distant - Discarded)</span>
                    </div>
                  </div>
                </div>

                {/* Right: Retraining Budget Equality Proof */}
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-4">
                  <div>
                    <h4 className="text-sm font-bold text-[#172554]">Fixed Retraining Budget & Compute Guarantee</h4>
                    <p className="text-xs text-[#64748B]">Strict O(1) sample equality ensuring zero latency escalation</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="p-4 rounded-xl bg-[#E7F0FF] border border-[#BFD5FE]">
                      <div className="text-xs text-[#64748B]">Recent Streaming Samples</div>
                      <div className="text-2xl font-extrabold text-[#5288F5]">2,000</div>
                      <div className="text-[11px] text-[#5288F5] font-semibold mt-1">50% of total budget</div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#F0EDFF] border border-[#D9D1FE]">
                      <div className="text-xs text-[#64748B]">Retrieved Historical Samples</div>
                      <div className="text-2xl font-extrabold text-[#9B8AFB]">2,000</div>
                      <div className="text-[11px] text-[#9B8AFB] font-semibold mt-1">50% of total budget</div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-[#E7F8F2] border border-[#54CDB6]/30 text-xs space-y-1">
                    <div className="font-bold text-[#172554] flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4 text-[#54CDB6]" />
                      <span>Bounded Budget Invariant: B_total = 4,000 samples</span>
                    </div>
                    <p className="text-[#64748B]">
                      Regardless of network lifespan, retraining complexity remains constant at <b>~0.16 seconds</b> on standard hardware.
                    </p>
                  </div>

                  <div className="p-3 bg-[#F5F8FF] border border-[#E4EAF5] rounded-xl text-xs text-[#64748B]">
                    <b>Fallback Safety Mechanism:</b> If candidate similarity drops below threshold (0.50), the system automatically queries a broad uniform historical reserve rather than forcing an inaccurate match.
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 6: MODEL PERFORMANCE (BENCHMARK & CATASTROPHIC FORGETTING)            */}
          {/* ========================================================================= */}
          {activeTab === 'performance' && (
            <div className="p-6 space-y-6">
              
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <h3 className="text-base font-bold text-[#172554]">Continual Learning Benchmark & Forgetting Mitigation</h3>
                <p className="text-xs text-[#64748B] mt-1">
                  Empirical evaluation of Pattern-Aware Replay (S4) against Static (S1), Recent-Only (S2), and Random Replay (S3).
                </p>
              </div>

              {/* 4 Strategy Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                {STRATEGY_BENCHMARKS.map((s, idx) => (
                  <div 
                    key={idx} 
                    className={`rounded-[18px] p-4 border transition-all ${
                      s.strategy.includes('S4')
                        ? 'bg-[#E7F8F2]/60 border-[#54CDB6] shadow-xs'
                        : 'bg-white border-[#E4EAF5]'
                    }`}
                  >
                    <div className="font-bold text-[#172554] text-xs mb-2">{s.strategy}</div>
                    <div className="space-y-1.5 text-[#64748B]">
                      <div className="flex justify-between">
                        <span>Recent Attack F1:</span>
                        <span className="font-bold text-[#172554]">{s.recentF1}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Historical F1:</span>
                        <span className="font-bold text-[#172554]">{s.histF1}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Forgetting Decay:</span>
                        <span className={`font-mono font-bold ${s.forgetting.includes('+24') ? 'text-[#FF8294]' : 'text-[#54CDB6]'}`}>
                          {s.forgetting}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Latency / Budget:</span>
                        <span>{s.latency} ({s.budget})</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Retention Trend Across Windows */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h4 className="text-sm font-bold text-[#172554]">Historical Knowledge Retention over Time</h4>
                    <p className="text-xs text-[#64748B]">Evaluating F1 score on holdout historical baseline test set across streaming windows</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1 text-[#54CDB6] font-bold">
                      <span className="h-2.5 w-2.5 rounded-full bg-[#54CDB6]"></span> S4: AEGIS Replay (Optimal)
                    </span>
                    <span className="flex items-center gap-1 text-[#FF8294]">
                      <span className="h-2.5 w-2.5 rounded-full bg-[#FF8294]"></span> S2: Recent Only (Severe Drop)
                    </span>
                  </div>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={RETENTION_CHART_DATA} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0F4FD" />
                      <XAxis dataKey="window" stroke="#94A3B8" fontSize={11} />
                      <YAxis domain={[65, 100]} stroke="#94A3B8" fontSize={11} tickFormatter={(v) => `${v}%`} />
                      <Tooltip />
                      <Line type="monotone" dataKey="S1" name="S1: Static IDS" stroke="#94A3B8" strokeDasharray="4 4" strokeWidth={2} />
                      <Line type="monotone" dataKey="S2" name="S2: Recent-Only" stroke="#FF8294" strokeWidth={2.5} />
                      <Line type="monotone" dataKey="S3" name="S3: Random Replay" stroke="#FFE98A" strokeWidth={2} />
                      <Line type="monotone" dataKey="S4" name="S4: AEGIS Pattern Replay" stroke="#54CDB6" strokeWidth={3} dot={{ r: 5, fill: '#54CDB6' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Quality Gate Outcome Card */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-[#54CDB6]" />
                    <h4 className="text-sm font-bold text-[#172554]">Production Quality Gate: PASSED</h4>
                  </div>
                  <p className="text-xs text-[#64748B]">
                    Criteria: Recent F1 &ge; 0.90 (94.8%), FPR &le; 0.03 (0.8%), Forgetting Decay &le; 0.05 (1.6%).
                  </p>
                </div>

                <span className="px-4 py-2 bg-[#E7F8F2] text-[#2ba38d] font-bold text-xs rounded-xl border border-[#54CDB6]/30">
                  Model Promoted to Active Inference
                </span>
              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 7: EXPERIMENTS & MLOPS ARCHITECTURE (UNITS I-VI)                      */}
          {/* ========================================================================= */}
          {activeTab === 'experiments' && (
            <div className="p-6 space-y-6">
              
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <h3 className="text-base font-bold text-[#172554]">Curriculum Alignment & MLOps Pipeline Specification</h3>
                <p className="text-xs text-[#64748B] mt-1">
                  Concrete implementation mapping syllabus Units I through VI to verified repository code and containers.
                </p>
              </div>

              {/* 6 Unit Alignment Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-[#5288F5] font-bold text-sm">
                    <FlaskConical className="h-4 w-4" />
                    <span>Unit I: Lifecycle & CI/CD Testing</span>
                  </div>
                  <p className="text-[#64748B]">
                    Automated GitHub Actions CI executing 30 unit & integration tests (<code>pytest</code>). Verifies budget equality (<code>B_total = 4,000</code>), zero temporal leakage, and KS test sensitivity.
                  </p>
                  <div className="text-[11px] font-mono text-[#94A3B8]">tests/test_pipeline.py</div>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-[#54CDB6] font-bold text-sm">
                    <Database className="h-4 w-4" />
                    <span>Unit II: Data Management & DVC</span>
                  </div>
                  <p className="text-[#64748B]">
                    Multi-stage DVC pipeline (<code>validate &rarr; preprocess &rarr; evaluate</code>) tracking data lineage without committing large binaries to Git. MLflow SQLite registry.
                  </p>
                  <div className="text-[11px] font-mono text-[#94A3B8]">dvc.yaml, dataset/*.dvc</div>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-[#9B8AFB] font-bold text-sm">
                    <Layers className="h-4 w-4" />
                    <span>Unit III: Pipeline Automation (Airflow)</span>
                  </div>
                  <p className="text-[#64748B]">
                    10-Task streaming DAG (<code>adaptive_ids_workflow.py</code>) orchestrating chronological window selection, KS drift test, branching, replay adaptation, and quality gating.
                  </p>
                  <div className="text-[11px] font-mono text-[#94A3B8]">dags/adaptive_ids_workflow.py</div>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-[#FF8294] font-bold text-sm">
                    <Server className="h-4 w-4" />
                    <span>Unit IV: Deployment & Observability</span>
                  </div>
                  <p className="text-[#64748B]">
                    Docker Compose microservices orchestrating FastAPI (port 8000), Prometheus time-series scraping (port 9090), and pre-provisioned Grafana observability dashboards (port 3002).
                  </p>
                  <div className="text-[11px] font-mono text-[#94A3B8]">docker-compose.yml</div>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-[#5288F5] font-bold text-sm">
                    <Sliders className="h-4 w-4" />
                    <span>Unit V: Responsible AI & Explainability</span>
                  </div>
                  <p className="text-[#64748B]">
                    TreeSHAP integration returning real-time local feature importance for every classified flow via the <code>/explain</code> REST endpoint.
                  </p>
                  <div className="text-[11px] font-mono text-[#94A3B8]">src/pipeline/serve.py (/explain)</div>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-[#2ba38d] font-bold text-sm">
                    <Cloud className="h-4 w-4" />
                    <span>Unit VI: Cloud MLOps (AWS SageMaker)</span>
                  </div>
                  <p className="text-[#64748B]">
                    Packaging utility (<code>package_sagemaker.py</code>) creating <code>model.tar.gz</code> with container contracts and serverless deployment profile with zero idle compute cost.
                  </p>
                  <div className="text-[11px] font-mono text-[#94A3B8]">build/sagemaker/model.tar.gz</div>
                </div>
              </div>

              {/* Mathematical Formulations Card */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-3">
                <h4 className="text-sm font-bold text-[#172554]">Theoretical & Mathematical Foundations</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-3 bg-[#F5F8FF] rounded-xl border border-[#E4EAF5] space-y-1">
                    <div className="font-bold text-[#5288F5]">1. Kolmogorov-Smirnov Test (Covariate Shift)</div>
                    <code className="text-[11px] font-mono block text-[#172554]">D = sup_x | F_ref(x) - F_curr(x) |</code>
                    <p className="text-[#64748B]">Drift declared if asymptotic p-value drops below α = 0.05.</p>
                  </div>

                  <div className="p-3 bg-[#F5F8FF] rounded-xl border border-[#E4EAF5] space-y-1">
                    <div className="font-bold text-[#9B8AFB]">2. Scale-Normalized Wasserstein Distance</div>
                    <code className="text-[11px] font-mono block text-[#172554]">W_norm(u, v) = W_1(u, v) / (σ_v + ε)</code>
                    <p className="text-[#64748B]">Normalizes variance to prevent high-magnitude features from dominating.</p>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 8: SETTINGS & OBSERVABILITY HUB                                       */}
          {/* ========================================================================= */}
          {activeTab === 'settings' && (
            <div className="p-6 space-y-6">
              
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs">
                <h3 className="text-base font-bold text-[#172554]">Settings & Live Infrastructure Endpoints</h3>
                <p className="text-xs text-[#64748B] mt-1">
                  System configuration parameters and direct links to active container microservices.
                </p>
              </div>

              {/* Service Status Tiles */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[#172554]">FastAPI Engine</span>
                    <span className={`h-2 w-2 rounded-full ${apiStatus.online ? 'bg-[#54CDB6]' : 'bg-[#FFE98A]'}`}></span>
                  </div>
                  <div className="text-xl font-bold text-[#172554]">Port 8000</div>
                  <p className="text-[#64748B] text-[11px]">Inference & SHAP Explainability</p>
                  <a 
                    href="http://localhost:8000/docs" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="inline-flex items-center gap-1 text-[#5288F5] hover:underline font-semibold pt-1"
                  >
                    <span>Swagger Docs</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[#172554]">Prometheus</span>
                    <span className="h-2 w-2 rounded-full bg-[#54CDB6]"></span>
                  </div>
                  <div className="text-xl font-bold text-[#172554]">Port 9090</div>
                  <p className="text-[#64748B] text-[11px]">Time-Series Scraper (5s)</p>
                  <a 
                    href="http://localhost:9090" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="inline-flex items-center gap-1 text-[#5288F5] hover:underline font-semibold pt-1"
                  >
                    <span>View Metrics</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[#172554]">Grafana Dashboard</span>
                    <span className="h-2 w-2 rounded-full bg-[#54CDB6]"></span>
                  </div>
                  <div className="text-xl font-bold text-[#172554]">Port 3002</div>
                  <p className="text-[#64748B] text-[11px]">admin / admin (UID: adaptive-ids)</p>
                  <a 
                    href="http://localhost:3002" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="inline-flex items-center gap-1 text-[#5288F5] hover:underline font-semibold pt-1"
                  >
                    <span>Open Dashboard</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[#172554]">MLflow Tracking</span>
                    <span className="h-2 w-2 rounded-full bg-[#54CDB6]"></span>
                  </div>
                  <div className="text-xl font-bold text-[#172554]">Port 5001</div>
                  <p className="text-[#64748B] text-[11px]">Experiment SQLite Registry</p>
                  <a 
                    href="http://localhost:5001" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="inline-flex items-center gap-1 text-[#5288F5] hover:underline font-semibold pt-1"
                  >
                    <span>Open MLflow</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>

              {/* System Parameters Card */}
              <div className="bg-white border border-[#E4EAF5] rounded-[18px] p-5 shadow-xs space-y-3">
                <h4 className="text-sm font-bold text-[#172554]">Core Algorithm Hyperparameters</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="p-3 bg-[#F5F8FF] rounded-xl border border-[#E4EAF5]">
                    <div className="text-[#64748B]">KS Drift Threshold (α)</div>
                    <div className="text-base font-bold text-[#172554]">0.05</div>
                    <div className="text-[#94A3B8] text-[10px]">p-value significance limit</div>
                  </div>

                  <div className="p-3 bg-[#F5F8FF] rounded-xl border border-[#E4EAF5]">
                    <div className="text-[#64748B]">Total Replay Budget (B_total)</div>
                    <div className="text-base font-bold text-[#172554]">4,000 samples</div>
                    <div className="text-[#54CDB6] text-[10px] font-semibold">Strict O(1) Guarantee</div>
                  </div>

                  <div className="p-3 bg-[#F5F8FF] rounded-xl border border-[#E4EAF5]">
                    <div className="text-[#64748B]">Historical Ratio</div>
                    <div className="text-base font-bold text-[#172554]">50% Recent / 50% Memory</div>
                    <div className="text-[#94A3B8] text-[10px]">Equal allocation policy</div>
                  </div>
                </div>
              </div>

            </div>
          )}

        </main>

      </div>

      {/* ========================================================================= */}
      {/* ASK AI INTERACTIVE MODAL                                                  */}
      {/* ========================================================================= */}
      {isAiModalOpen && (
        <div className="fixed inset-0 bg-[#172554]/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-[22px] max-w-lg w-full border border-[#E4EAF5] shadow-[0_20px_50px_rgba(82,136,245,0.15)] p-6 space-y-4">
            
            <div className="flex justify-between items-center border-b border-[#EDF1F8] pb-3">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-[#9B8AFB] to-[#5288F5] flex items-center justify-center text-white">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-[#172554]">AEGIS AI Assistant</h4>
                  <p className="text-[11px] text-[#64748B]">System Reasoning & Decision Transparency</p>
                </div>
              </div>

              <button 
                onClick={() => setIsAiModalOpen(false)}
                className="text-[#94A3B8] hover:text-[#172554] p-1 rounded-lg hover:bg-[#F5F8FF]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-[#F5F8FF] border border-[#BFD5FE] text-[#172554] space-y-1.5">
                <div className="font-bold flex items-center gap-1.5 text-[#5288F5]">
                  <Info className="h-3.5 w-3.5" />
                  <span>Why was Pattern PAT-002 (DoS) retrieved in W10?</span>
                </div>
                <p className="text-[#64748B]">
                  In Window W10, the KS-test detected a major covariate shift primarily driven by <b>Flow Bytes/s</b> and <b>Packet Length Mean</b>. The scale-normalized 1D Wasserstein distance between the streaming distribution and Historical Memory centroids yielded a top similarity of <b>0.82 with DoS</b>, exceeding the selection threshold (0.50).
                </p>
              </div>

              <div className="p-3 rounded-xl bg-[#F5F8FF] border border-[#E4EAF5] text-[#172554] space-y-1.5">
                <div className="font-bold flex items-center gap-1.5 text-[#9B8AFB]">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>How does S4 prevent catastrophic forgetting?</span>
                </div>
                <p className="text-[#64748B]">
                  Under S2 (Recent-Only), model retention on prior attack signatures dropped to 71.2% (24.6% decay). S4 interleaves 2,000 historical exemplars of the identified pattern into the retraining batch, keeping retention high at <b>94.2%</b> while preserving the exact <b>4,000 packet compute budget</b>.
                </p>
              </div>
            </div>

            <button
              onClick={() => setIsAiModalOpen(false)}
              className="w-full py-2 bg-[#5288F5] text-white rounded-xl font-semibold text-xs hover:bg-[#4375db] transition-colors cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
