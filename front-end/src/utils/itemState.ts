export type ItemStatus = 'IN_USE' | 'MAINTENANCE' | 'AVAILABLE' | 'UNAVAILABLE' | 'UNSERVICEABLE';
export type ItemCondition = 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'DAMAGED';

export type BadgeVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info';

export const ITEM_STATUS_OPTIONS: Array<{ value: ItemStatus; label: string }> = [
    { value: 'AVAILABLE', label: 'Available' },
    { value: 'IN_USE', label: 'In use' },
    { value: 'MAINTENANCE', label: 'Maintenance' },
    { value: 'UNAVAILABLE', label: 'Unavailable' },
    { value: 'UNSERVICEABLE', label: 'Unserviceable' },
];

export const ITEM_CONDITION_OPTIONS: Array<{ value: ItemCondition; label: string }> = [
    { value: 'EXCELLENT', label: 'Excellent' },
    { value: 'GOOD', label: 'Good' },
    { value: 'FAIR', label: 'Fair' },
    { value: 'POOR', label: 'Poor' },
    { value: 'DAMAGED', label: 'Damaged' },
];

export function formatItemStatus(status?: string | null): string {
    return ITEM_STATUS_OPTIONS.find((option) => option.value === status)?.label || 'Available';
}

export function formatItemCondition(condition?: string | null): string {
    return ITEM_CONDITION_OPTIONS.find((option) => option.value === condition)?.label || 'Good';
}

export function getItemStatusBadge(status?: string | null): BadgeVariant {
    switch (status) {
        case 'AVAILABLE':
            return 'success';
        case 'IN_USE':
            return 'primary';
        case 'MAINTENANCE':
            return 'warning';
        case 'UNAVAILABLE':
            return 'secondary';
        case 'UNSERVICEABLE':
            return 'danger';
        default:
            return 'secondary';
    }
}

export function getItemConditionBadge(condition?: string | null): BadgeVariant {
    switch (condition) {
        case 'EXCELLENT':
            return 'success';
        case 'GOOD':
            return 'info';
        case 'FAIR':
            return 'warning';
        case 'POOR':
        case 'DAMAGED':
            return 'danger';
        default:
            return 'secondary';
    }
}
