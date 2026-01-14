import type { ReactNode } from 'react';
import {
    BarChart3,
    Grid,
    Tag,
    Ruler,
    Users,
    Settings,
    Package,
    Plus,
    LogOut,
    Receipt,
    Home,
    FileText,
    ShoppingCart,
    TrendingUp,
    Clock,
    AlertCircle,
    CheckCircle,
    ChevronDown,
    ChevronRight,
    Menu,
    X,
    Search,
    Edit,
    Trash2,
    Eye,
    Download,
    Upload,
    Save,
    XCircle,
    Archive,
    RotateCcw,
} from 'lucide-react';
import type { LucideProps } from 'lucide-react';

interface IconComponentProps {
    name: string;
    size?: number;
    className?: string;
}

type IconType = React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;

// Map Bootstrap icon names (bi-*) to lucide-react icons
const iconMap: Record<string, IconType> = {
    'bi-speedometer2': BarChart3,
    'bi-grid': Grid,
    'bi-tag': Tag,
    'bi-rulers': Ruler,
    'bi-people': Users,
    'bi-gear': Settings,
    'bi-box': Package,
    'bi-plus-circle': Plus,
    'bi-box-arrow-right': LogOut,
    'bi-receipt': Receipt,
    'bi-house': Home,
    'bi-file-text': FileText,
    'bi-cart': ShoppingCart,
    'bi-graph-up': TrendingUp,
    'bi-clock': Clock,
    'bi-exclamation-circle': AlertCircle,
    'bi-check-circle': CheckCircle,
    'bi-clipboard-check': CheckCircle,
    'bi-chevron-down': ChevronDown,
    'bi-chevron-right': ChevronRight,
    'bi-menu': Menu,
    'bi-x': X,
    'bi-search': Search,
    'bi-pencil': Edit,
    'bi-trash': Trash2,
    'bi-eye': Eye,
    'bi-download': Download,
    'bi-upload': Upload,
    'bi-check': Save,
    'bi-x-circle': XCircle,
    'bi-archive': Archive,
    'bi-archive-fill': RotateCcw,
};

export function IconComponent({
    name,
    size = 16,
    className = '',
}: IconComponentProps): ReactNode {
    const Icon = iconMap[name];

    if (!Icon) {
        console.warn(`Icon not found: ${name}. Using default icon.`);
        return <AlertCircle size={size} className={className} />;
    }

    return <Icon size={size} className={className} />;
}

export default IconComponent;
