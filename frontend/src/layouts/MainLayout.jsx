import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { Menu, Sun, Moon } from 'lucide-react';

export default function MainLayout() {
  const location = useLocation();
  const [theme, setTheme] = React.useState(localStorage.getItem('theme') || 'dark');

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Dashboard';
      case '/predict': return 'Predict Delay';
      case '/history': return 'Prediction History';
      case '/analytics': return 'Analytics';
      case '/model': return 'AI Model Management';
      case '/model-history': return 'Model History';
      case '/settings': return 'Settings';
      default: return 'BhoomiGuard AI';
    }
  };

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col h-screen">
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center px-8 flex-shrink-0 sticky top-0 z-10">
          <button className="mr-4 lg:hidden text-slate-400 hover:text-slate-200">
            <Menu className="w-6 h-6" />
          </button>
          <h2 className="text-xl font-semibold text-slate-100">{getPageTitle()}</h2>
          <div className="ml-auto flex items-center gap-4">
            <div id="header-filters-portal"></div>
            <button 
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-100 border border-border"
              title="Toggle Theme"
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-8 scrollbar-thin">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
