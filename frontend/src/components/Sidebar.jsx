import { NavLink } from 'react-router-dom';
import { Shield, Home, Zap, Clock, BarChart2, Brain, GitBranch, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function Sidebar() {
  const { user, logout } = useAuth();

  const links = [
    { to: '/', icon: Home, label: 'Dashboard', roles: ['admin', 'district_officer', 'project_officer'] },
    { to: '/predict', icon: Zap, label: 'Predict Delay', roles: ['admin', 'district_officer', 'project_officer'] },
    { to: '/history', icon: Clock, label: 'Prediction History', roles: ['admin', 'district_officer', 'project_officer'] },
    { to: '/analytics', icon: BarChart2, label: 'Analytics', roles: ['admin', 'district_officer'] },
    { to: '/model', icon: Brain, label: 'AI Model', roles: ['admin'] },
    { to: '/model-history', icon: GitBranch, label: 'Model History', roles: ['admin'] },
    { to: '/settings', icon: Settings, label: 'Settings', roles: ['admin', 'district_officer', 'project_officer'] },
  ].filter(link => !link.roles || link.roles.includes(user?.role));

  return (
    <div className="w-64 h-screen bg-card border-r border-border flex flex-col fixed left-0 top-0">
      <div className="p-6 flex items-center gap-3 border-b border-border">
        <img src="/logo.jpg" alt="Logo" className="w-10 h-10 object-contain rounded-lg shadow-sm" />
        <div>
          <h1 className="font-bold text-lg leading-tight text-slate-100">BhoomiGuard</h1>
          <span className="text-xs text-primary-500 font-semibold uppercase tracking-wider">AI System</span>
        </div>
      </div>
      
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive 
                  ? 'bg-primary-500/10 text-primary-500 border border-primary-500/20' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`
            }
          >
            <link.icon className="w-5 h-5" />
            <span className="font-medium">{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 mb-4 px-2">
          <div className="w-10 h-10 rounded-full bg-primary-900 flex items-center justify-center text-primary-100 font-bold border border-primary-700">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">{user?.username}</p>
            <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors border border-transparent hover:border-red-500/20"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
