import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Menu, X, ChevronDown, ChevronRight, LogOut } from 'lucide-react';
import { Badge, IconComponent } from './UI';

interface LayoutProps {
    children: React.ReactNode;
}

interface MenuItem {
    path: string;
    icon: string;
    label: string;
    subMenu?: MenuItem[];
    action?: 'logout';
}

function Layout({ children }: LayoutProps) {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [itemsMenuOpen, setItemsMenuOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const dashboardItem: MenuItem = { path: '/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' };
    const managementItems: MenuItem[] = [
        {
            path: '/items',
            icon: 'bi-grid',
            label: 'Items',
            subMenu: [
                { path: '/items', icon: 'bi-box', label: 'All Items' },
                { path: '/categories', icon: 'bi-tag', label: 'Categories' },
                { path: '/units', icon: 'bi-rulers', label: 'Units' },
            ],
        },
    ];

    const transactionItems: MenuItem[] = [
        { path: '/transactions', icon: 'bi-receipt', label: 'Transactions' },
    ];

    const adminItems: MenuItem[] = [];
    if (user?.role === 'ADMIN') {
        adminItems.push({ path: '/users', icon: 'bi-people', label: 'Users' });
        adminItems.push({ path: '/settings', icon: 'bi-gear', label: 'Settings' });
    }

    const auditItems: MenuItem[] = [];
    if (user?.role === 'ADMIN' || user?.role === 'AUDITOR') {
        auditItems.push({ path: '/audit', icon: 'bi-clipboard-check', label: 'Audit' });
    }

    const isActive = (path: string) => location.pathname === path;
    const isItemsMenuActive = () => {
        return location.pathname === '/items' ||
            location.pathname === '/categories' ||
            location.pathname === '/units';
    };

    const renderMenuItems = (items: MenuItem[], isMobile: boolean = false) => (
        <>
            {items.map((item) => (
                <div key={item.path}>
                    <button
                        className={`w-full text-start px-3 py-2 rounded-full transition-colors flex items-center justify-between text-sm font-medium ${
                            item.subMenu
                                ? isItemsMenuActive()
                                    ? 'bg-blue-600 text-white'
                                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                                : isActive(item.path)
                                    ? 'bg-blue-600 text-white'
                                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                        }`}
                        onClick={() => {
                            if (item.subMenu) {
                                setItemsMenuOpen(!itemsMenuOpen);
                            } else if (item.action === 'logout') {
                                handleLogout();
                            } else {
                                navigate(item.path);
                                if (isMobile) setSidebarOpen(false);
                            }
                        }}
                    >
                        <div className="flex items-center gap-2">
                            <IconComponent name={item.icon} size={16} />
                            <span>{item.label}</span>
                        </div>
                        {item.subMenu && (
                            itemsMenuOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />
                        )}
                    </button>

                    {item.subMenu && itemsMenuOpen && (
                        <div className="ml-6 mt-1 flex flex-col gap-1">
                            {item.subMenu.map((subItem) => (
                                <button
                                    key={subItem.path}
                                    className={`w-full text-start px-3 py-2 rounded-full transition-colors flex items-center gap-2 text-sm ${
                                        isActive(subItem.path)
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                                    }`}
                                    onClick={() => {
                                        navigate(subItem.path);
                                        if (isMobile) setSidebarOpen(false);
                                    }}
                                >
                                    <IconComponent name={subItem.icon} size={14} />
                                    {subItem.label}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            ))}
        </>
    );

    return (
        <div className="flex min-h-screen bg-gray-100">
            {/* Desktop Sidebar */}
            <div className="hidden lg:flex lg:flex-col bg-gray-900 text-white w-64 fixed inset-y-0 left-0 shadow-lg">
                <div className="border-b border-gray-700 p-4">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-gradient-to-br from-gray-700 to-gray-600 flex items-center justify-center text-xs font-bold border border-gray-600">
                            SGi
                        </div>
                        <div className="leading-tight">
                            <div className="font-semibold text-sm">Inventory</div>
                            <div className="font-semibold text-sm">Management</div>
                            <div className="font-semibold text-sm">System</div>
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    <nav className="flex flex-col gap-1 px-3 py-4">
                        {renderMenuItems([dashboardItem])}
                        <div className="pt-2 pb-1">
                            <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Management</p>
                        </div>
                        {renderMenuItems(managementItems)}
                        <div className="pt-2 pb-1">
                            <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Transaction</p>
                        </div>
                        {renderMenuItems(transactionItems)}
                        {auditItems.length > 0 && (
                            <>
                                <div className="pt-2 pb-1">
                                    <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Audit</p>
                                </div>
                                {renderMenuItems(auditItems, true)}
                            </>
                        )}
                        {adminItems.length > 0 && (
                            <>
                                <div className="pt-2 pb-1">
                                    <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Admin</p>
                                </div>
                                {renderMenuItems(adminItems, true)}
                            </>
                        )}
                    </nav>
                </div>

                {user && (
                    <div className="border-t border-gray-700 p-4">
                        <div className="mb-3">
                            <div className="font-bold text-sm">{user.name}</div>
                            <Badge variant="primary">{user.role}</Badge>
                        </div>
                        <button
                            className="w-full flex items-center justify-center px-4 py-2 border border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-300 bg-transparent hover:bg-gray-800 hover:text-white transition-colors"
                            onClick={handleLogout}
                        >
                            <LogOut size={16} className="mr-2" />
                            Logout
                        </button>
                    </div>
                )}
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col lg:ml-64">
                {/* Mobile Top Bar */}
                <nav className="lg:hidden bg-gray-900 text-white shadow-lg sticky top-0 z-40">
                    <div className="px-4 py-3 flex items-center justify-between">
                        <button
                            onClick={() => setSidebarOpen(true)}
                            className="text-white hover:text-gray-300"
                        >
                            <Menu size={24} />
                        </button>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded bg-gradient-to-br from-gray-700 to-gray-600 flex items-center justify-center text-xs font-bold border border-gray-600">
                                SGi
                            </div>
                            <span className="font-semibold text-sm">Inventory</span>
                        </div>
                        <div className="w-6" />
                    </div>
                </nav>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto">
                    {children}
                </main>
            </div>

            {/* Mobile Sidebar Backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Mobile Sidebar */}
            <div className={`fixed inset-y-0 left-0 w-64 bg-gray-900 text-white z-50 lg:hidden transform transition-transform ${
                sidebarOpen ? 'translate-x-0' : '-translate-x-full'
            }`}>
                <div className="border-b border-gray-700 p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-gradient-to-br from-gray-700 to-gray-600 flex items-center justify-center text-xs font-bold border border-gray-600">
                            SGi
                        </div>
                        <div className="leading-tight">
                            <div className="font-semibold text-sm">Inventory</div>
                            <div className="font-semibold text-sm">Management</div>
                        </div>
                    </div>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="text-white hover:text-gray-300"
                    >
                        <X size={24} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    <nav className="flex flex-col gap-1 px-3 py-4">
                        {renderMenuItems([dashboardItem], true)}
                        <div className="pt-2 pb-1">
                            <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Management</p>
                        </div>
                        {renderMenuItems(managementItems, true)}
                        <div className="pt-2 pb-1">
                            <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Transaction</p>
                        </div>
                        {renderMenuItems(transactionItems, true)}
                        {auditItems.length > 0 && (
                            <>
                                <div className="pt-2 pb-1">
                                    <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Audit</p>
                                </div>
                                {renderMenuItems(auditItems, true)}
                            </>
                        )}
                        {adminItems.length > 0 && (
                            <>
                                <div className="pt-2 pb-1">
                                    <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Admin</p>
                                </div>
                                {renderMenuItems(adminItems, true)}
                            </>
                        )}
                    </nav>
                </div>

                {user && (
                    <div className="border-t border-gray-700 p-4">
                        <div className="mb-3">
                            <div className="font-bold text-sm">{user.name}</div>
                            <Badge variant="primary">{user.role}</Badge>
                        </div>
                        <button
                            className="w-full flex items-center justify-center px-4 py-2 border border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-300 bg-transparent hover:bg-gray-800 hover:text-white transition-colors"
                            onClick={handleLogout}
                        >
                            <LogOut size={16} className="mr-2" />
                            Logout
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Layout;
