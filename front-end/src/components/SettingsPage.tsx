import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Save, Info, Cpu, HardDrive, MemoryStick } from 'lucide-react';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    Alert,
    Spinner,
    FormInput,
    FormCheckbox,
} from './UI';

interface SettingsState {
    app_name: string;
    items_per_page: string;
    allow_negative_stock: boolean;
    auto_backup_enabled: boolean;
    backup_retention_days: string;
    low_stock_threshold: string;
    enable_notifications: boolean;
}

interface SystemInfo {
    platform: string;
    platform_release: string;
    platform_version: string;
    python_version: string;
    cpu_count: number;
    cpu_usage_percent: number;
    memory_total_gb: number;
    memory_used_gb: number;
    memory_usage_percent: number;
    disk_total_gb: number;
    disk_used_gb: number;
    disk_usage_percent: number;
    uptime: string;
}

function SettingsPage() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
    const [settings, setSettings] = useState<SettingsState>({
        app_name: 'Inventory Management System',
        items_per_page: '50',
        allow_negative_stock: false,
        auto_backup_enabled: true,
        backup_retention_days: '30',
        low_stock_threshold: '10',
        enable_notifications: true,
    });

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && user?.role !== 'ADMIN') {
            navigate('/dashboard');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (!token) return;

        const fetchSettings = async () => {
            setIsLoading(true);
            try {
                const response = await fetch(`${API_BASE_URL}/settings`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    const data = await response.json();
                    setSettings({
                        app_name: data.app_name || 'Inventory Management System',
                        items_per_page: String(data.items_per_page || 50),
                        allow_negative_stock: Boolean(data.allow_negative_stock),
                        auto_backup_enabled: Boolean(data.auto_backup_enabled),
                        backup_retention_days: String(data.backup_retention_days || 30),
                        low_stock_threshold: String(data.low_stock_threshold || 10),
                        enable_notifications: Boolean(data.enable_notifications),
                    });
                }
            } catch (err) {
                console.error('Error fetching settings:', err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchSettings();
        fetchSystemInfo();
    }, [API_BASE_URL, token]);

    const fetchSystemInfo = async () => {
        if (!token) return;

        try {
            const response = await fetch(`${API_BASE_URL}/settings/system-info`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data: SystemInfo = await response.json();
                setSystemInfo(data);
            }
        } catch (err) {
            console.error('Failed to fetch system info:', err);
        }
    };

    const handleChange = (field: keyof SettingsState, value: string | boolean) => {
        setSettings((prev) => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        if (!token) return;

        setIsSaving(true);
        setError(null);
        setSuccess(null);

        const payload = {
            app_name: settings.app_name.trim(),
            items_per_page: Number(settings.items_per_page),
            allow_negative_stock: settings.allow_negative_stock,
            auto_backup_enabled: settings.auto_backup_enabled,
            backup_retention_days: Number(settings.backup_retention_days),
            low_stock_threshold: Number(settings.low_stock_threshold),
            enable_notifications: settings.enable_notifications,
        };

        try {
            const response = await fetch(`${API_BASE_URL}/settings`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to save settings');
            }

            setSuccess('Settings saved successfully');
        } catch (err) {
            setError((err as Error).message || 'Failed to save settings');
        } finally {
            setIsSaving(false);
        }
    };

    if (authLoading || isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <h2 className="text-3xl font-bold text-gray-900">⚙️ Settings</h2>
                    <p className="text-gray-600 mt-1">Configure application settings</p>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
                        {error}
                    </Alert>
                )}
                {success && (
                    <Alert variant="success" dismissible onClose={() => setSuccess(null)} className="mb-4">
                        {success}
                    </Alert>
                )}

                {/* System Info */}
                {systemInfo && (
                    <Card className="mb-6 bg-blue-50 border-blue-200">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Info className="w-5 h-5 text-blue-600" />
                                <h5 className="font-bold text-blue-900">System Information</h5>
                            </div>
                        </CardHeader>
                        <CardBody>
                            {/* Platform Info */}
                            <div className="mb-6">
                                <h6 className="font-semibold text-sm text-gray-700 mb-3 flex items-center gap-2">
                                    <Info className="w-4 h-4" />
                                    Platform
                                </h6>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div>
                                        <p className="text-sm text-gray-600">Operating System</p>
                                        <p className="font-semibold text-gray-900">{systemInfo.platform}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Release</p>
                                        <p className="font-semibold text-gray-900">{systemInfo.platform_release}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Python Version</p>
                                        <p className="font-semibold text-gray-900">{systemInfo.python_version}</p>
                                    </div>
                                    <div className="md:col-span-2 lg:col-span-3">
                                        <p className="text-sm text-gray-600">Uptime</p>
                                        <p className="font-semibold text-gray-900 text-xs">{systemInfo.uptime}</p>
                                    </div>
                                </div>
                            </div>

                            {/* CPU Info */}
                            <div className="mb-6">
                                <h6 className="font-semibold text-sm text-gray-700 mb-3 flex items-center gap-2">
                                    <Cpu className="w-4 h-4" />
                                    CPU
                                </h6>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-gray-600">CPU Cores</p>
                                        <p className="font-semibold text-gray-900">{systemInfo.cpu_count}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">CPU Usage</p>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-blue-600 h-2 rounded-full transition-all"
                                                    style={{ width: `${systemInfo.cpu_usage_percent}%` }}
                                                />
                                            </div>
                                            <p className="font-semibold text-gray-900">{systemInfo.cpu_usage_percent}%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Memory Info */}
                            <div className="mb-6">
                                <h6 className="font-semibold text-sm text-gray-700 mb-3 flex items-center gap-2">
                                    <MemoryStick className="w-4 h-4" />
                                    Memory
                                </h6>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-gray-600">Total / Used</p>
                                        <p className="font-semibold text-gray-900">
                                            {systemInfo.memory_used_gb} GB / {systemInfo.memory_total_gb} GB
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Memory Usage</p>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                                                <div
                                                    className={`h-2 rounded-full transition-all ${
                                                        systemInfo.memory_usage_percent > 80
                                                            ? 'bg-red-600'
                                                            : systemInfo.memory_usage_percent > 60
                                                            ? 'bg-yellow-600'
                                                            : 'bg-green-600'
                                                    }`}
                                                    style={{ width: `${systemInfo.memory_usage_percent}%` }}
                                                />
                                            </div>
                                            <p className="font-semibold text-gray-900">{systemInfo.memory_usage_percent}%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Disk Info */}
                            <div>
                                <h6 className="font-semibold text-sm text-gray-700 mb-3 flex items-center gap-2">
                                    <HardDrive className="w-4 h-4" />
                                    Disk
                                </h6>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-gray-600">Total / Used</p>
                                        <p className="font-semibold text-gray-900">
                                            {systemInfo.disk_used_gb} GB / {systemInfo.disk_total_gb} GB
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Disk Usage</p>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                                                <div
                                                    className={`h-2 rounded-full transition-all ${
                                                        systemInfo.disk_usage_percent > 80
                                                            ? 'bg-red-600'
                                                            : systemInfo.disk_usage_percent > 60
                                                            ? 'bg-yellow-600'
                                                            : 'bg-green-600'
                                                    }`}
                                                    style={{ width: `${systemInfo.disk_usage_percent}%` }}
                                                />
                                            </div>
                                            <p className="font-semibold text-gray-900">{systemInfo.disk_usage_percent}%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardBody>
                    </Card>
                )}

                {/* General Settings */}
                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="font-bold">General Settings</h5>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormInput
                                label="Application Name"
                                placeholder="Enter app name"
                                value={settings.app_name}
                                onChange={(e) => handleChange('app_name', e.target.value)}
                            />
                            <FormInput
                                label="Items Per Page"
                                type="number"
                                min="10"
                                max="500"
                                value={settings.items_per_page}
                                onChange={(e) => handleChange('items_per_page', e.target.value)}
                            />
                        </div>
                    </CardBody>
                </Card>

                {/* Stock Settings */}
                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="font-bold">Stock Settings</h5>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <FormInput
                                label="Low Stock Threshold"
                                type="number"
                                min="0"
                                value={settings.low_stock_threshold}
                                onChange={(e) => handleChange('low_stock_threshold', e.target.value)}
                            />
                        </div>
                        <div>
                            <FormCheckbox
                                id="allow-negative"
                                label="Allow Negative Stock"
                                checked={settings.allow_negative_stock}
                                onChange={(e) => handleChange('allow_negative_stock', e.target.checked)}
                            />
                        </div>
                    </CardBody>
                </Card>

                {/* Backup Settings */}
                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="font-bold">Backup Settings</h5>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <FormInput
                                label="Backup Retention Days"
                                type="number"
                                min="1"
                                max="365"
                                value={settings.backup_retention_days}
                                onChange={(e) => handleChange('backup_retention_days', e.target.value)}
                            />
                        </div>
                        <div>
                            <FormCheckbox
                                id="auto-backup"
                                label="Enable Automatic Backups"
                                checked={settings.auto_backup_enabled}
                                onChange={(e) => handleChange('auto_backup_enabled', e.target.checked)}
                            />
                        </div>
                    </CardBody>
                </Card>

                {/* Notification Settings */}
                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="font-bold">Notification Settings</h5>
                    </CardHeader>
                    <CardBody>
                        <div>
                            <FormCheckbox
                                id="enable-notifications"
                                label="Enable Notifications"
                                checked={settings.enable_notifications}
                                onChange={(e) => handleChange('enable_notifications', e.target.checked)}
                            />
                        </div>
                    </CardBody>
                </Card>

                {/* Save Button */}
                <div className="flex justify-end gap-2">
                    <Button
                        variant="primary"
                        onClick={handleSave}
                        disabled={isSaving}
                    >
                        {isSaving ? (
                            <>
                                <Spinner size="sm" className="mr-2" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4 mr-2" />
                                Save Settings
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}

export default SettingsPage;
