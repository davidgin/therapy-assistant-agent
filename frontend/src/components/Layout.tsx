import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  HomeIcon, 
  ClipboardDocumentCheckIcon, 
  PresentationChartLineIcon,
  DocumentMagnifyingGlassIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout, isLicensedProfessional } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon, current: location.pathname === '/' },
    { 
      name: 'Diagnostic Assistant', 
      href: '/diagnostic', 
      icon: ClipboardDocumentCheckIcon, 
      current: location.pathname === '/diagnostic',
      licensed: true
    },
    { 
      name: 'Treatment Planning', 
      href: '/treatment', 
      icon: PresentationChartLineIcon, 
      current: location.pathname === '/treatment',
      licensed: true
    },
    { 
      name: 'Case Analysis', 
      href: '/case-analysis', 
      icon: DocumentMagnifyingGlassIcon, 
      current: location.pathname === '/case-analysis',
      licensed: true
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between items-center">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Therapy Assistant Agent
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <UserCircleIcon className="h-6 w-6 text-gray-400" />
                <span className="text-sm text-gray-700">
                  {user?.first_name} {user?.last_name}
                </span>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  {user?.role}
                </span>
              </div>
              
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                <ArrowRightOnRectangleIcon className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <nav className="bg-white w-64 min-h-screen shadow-sm border-r border-gray-200">
          <div className="p-4 space-y-2">
            {navigation.map((item) => {
              // Hide licensed features for students
              if (item.licensed && !isLicensedProfessional) {
                return (
                  <div
                    key={item.name}
                    className="flex items-center px-3 py-2 text-sm font-medium text-gray-400 cursor-not-allowed"
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                    <span className="ml-auto text-xs bg-gray-100 px-2 py-1 rounded">
                      Licensed Only
                    </span>
                  </div>
                );
              }

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    item.current
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;