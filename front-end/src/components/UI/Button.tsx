import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline-primary' | 'outline-secondary' | 'outline-danger' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  rounded?: 'full' | 'md' | 'lg';
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  rounded = 'full',
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const baseClasses = 'ui-btn rounded-md';

  const variants = {
    primary: 'bg-primary hover:bg-primary-dark text-white shadow-sm focus:ring-primary',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white shadow-sm focus:ring-gray-500',
    danger: 'bg-danger hover:bg-red-700 text-white shadow-sm focus:ring-danger',
    success: 'bg-success hover:bg-green-700 text-white shadow-sm focus:ring-success',
    'outline-primary': 'border border-gray-300 text-primary hover:text-primary-dark hover:bg-gray-50 focus:ring-primary',
    'outline-secondary': 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500',
    'outline-danger': 'border border-gray-300 text-danger hover:text-red-700 hover:bg-gray-50 focus:ring-danger',
  };

  const sizes = {
    sm: 'ui-btn-sm',
    md: '',
    lg: 'ui-btn-lg',
  };

  const rounding = {
    full: 'rounded-full',
    md: 'rounded-md',
    lg: 'rounded-lg',
  };

  return (
    <button
      className={`${baseClasses} ${rounding[rounded]} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {children}
    </button>
  );
}
