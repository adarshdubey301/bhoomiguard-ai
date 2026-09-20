import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import MainLayout from './layouts/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import PredictionHistory from './pages/PredictionHistory';
import Analytics from './pages/Analytics';
import ModelManagement from './pages/ModelManagement';
import ModelHistory from './pages/ModelHistory';
import Settings from './pages/Settings';

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const RoleRoute = ({ children, allowedRoles }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!allowedRoles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="predict" element={<Predict />} />
        <Route path="history" element={<PredictionHistory />} />
        <Route path="analytics" element={<RoleRoute allowedRoles={['admin', 'district_officer']}><Analytics /></RoleRoute>} />
        <Route path="model" element={<RoleRoute allowedRoles={['admin']}><ModelManagement /></RoleRoute>} />
        <Route path="model-history" element={<RoleRoute allowedRoles={['admin']}><ModelHistory /></RoleRoute>} />
        <Route path="settings" element={<Settings />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
