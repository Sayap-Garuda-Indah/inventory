import { BarChart3, CheckCircle2, FileText, Package, XCircle } from 'lucide-react';
import { Card, CardBody } from './UI';

export interface IssueStatisticsData {
    total: number;
    status_breakdown: {
        draft: { count: number; percentage: number };
        approved: { count: number; percentage: number };
        issued: { count: number; percentage: number };
        cancelled: { count: number; percentage: number };
    };
}

interface IssueStatisticsCardsProps {
    statistics: IssueStatisticsData | null;
    isLoading: boolean;
    scale?: 'sm' | 'md' | 'lg';
}

const formatPercentage = (value: number) => `${Number(value.toFixed(2)).toString()}%`;

const scaleStyles = {
    sm: {
        sectionTitle: 'text-xl mb-3',
        gridGap: 'gap-2.5',
        cardRadius: 'rounded-xl',
        cardBody: 'p-3',
        icon: 'w-7 h-7',
        title: 'text-2xl mb-1',
        value: 'text-[2.1rem] mt-1 mb-1.5',
        percentage: 'text-[1.35rem] mb-1.5',
        progress: 'h-2',
    },
    md: {
        sectionTitle: 'text-2xl mb-4',
        gridGap: 'gap-3',
        cardRadius: 'rounded-xl',
        cardBody: 'p-4',
        icon: 'w-9 h-9',
        title: 'text-[1.9rem] mb-1',
        value: 'text-5xl mt-1 mb-2',
        percentage: 'text-3xl mb-2',
        progress: 'h-2.5',
    },
    lg: {
        sectionTitle: 'text-3xl mb-5',
        gridGap: 'gap-4',
        cardRadius: 'rounded-2xl',
        cardBody: 'p-5',
        icon: 'w-10 h-10',
        title: 'text-[2.1rem] mb-1',
        value: 'text-6xl mt-1 mb-2.5',
        percentage: 'text-4xl mb-2.5',
        progress: 'h-3',
    },
} as const;

export function IssueStatisticsCards({ statistics, isLoading, scale = 'md' }: IssueStatisticsCardsProps) {
    if (isLoading || !statistics) return null;
    const current = scaleStyles[scale];

    const cards = [
        {
            key: 'total',
            title: 'Total Issues',
            value: statistics.total,
            percentage: null as number | null,
            icon: BarChart3,
            palette: {
                bg: 'from-blue-50 to-blue-100',
                border: 'border-blue-200',
                icon: 'text-blue-500',
                value: 'text-blue-500',
                track: 'bg-blue-200/70',
                fill: 'bg-blue-400',
            },
        },
        {
            key: 'draft',
            title: 'Draft',
            value: statistics.status_breakdown.draft.count,
            percentage: statistics.status_breakdown.draft.percentage,
            icon: FileText,
            palette: {
                bg: 'from-amber-50 to-amber-100',
                border: 'border-amber-200',
                icon: 'text-amber-500',
                value: 'text-amber-500',
                track: 'bg-amber-200/80',
                fill: 'bg-amber-500',
            },
        },
        {
            key: 'approved',
            title: 'Approved',
            value: statistics.status_breakdown.approved.count,
            percentage: statistics.status_breakdown.approved.percentage,
            icon: CheckCircle2,
            palette: {
                bg: 'from-cyan-50 to-cyan-100',
                border: 'border-cyan-200',
                icon: 'text-cyan-500',
                value: 'text-cyan-500',
                track: 'bg-cyan-200/80',
                fill: 'bg-cyan-500',
            },
        },
        {
            key: 'issued',
            title: 'Issued',
            value: statistics.status_breakdown.issued.count,
            percentage: statistics.status_breakdown.issued.percentage,
            icon: Package,
            palette: {
                bg: 'from-green-50 to-green-100',
                border: 'border-green-200',
                icon: 'text-green-500',
                value: 'text-green-500',
                track: 'bg-green-200/80',
                fill: 'bg-green-500',
            },
        },
        {
            key: 'cancelled',
            title: 'Cancelled',
            value: statistics.status_breakdown.cancelled.count,
            percentage: statistics.status_breakdown.cancelled.percentage,
            icon: XCircle,
            palette: {
                bg: 'from-rose-50 to-rose-100',
                border: 'border-rose-200',
                icon: 'text-rose-500',
                value: 'text-rose-500',
                track: 'bg-rose-200/80',
                fill: 'bg-rose-500',
            },
        },
    ];

    return (
        <div className="mb-6">
            <h4 className={`font-bold ${current.sectionTitle}`}>Issues Statistics</h4>
            <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 ${current.gridGap}`}>
                {cards.map((card) => {
                    const Icon = card.icon;
                    return (
                        <Card
                            key={card.key}
                            className={`${current.cardRadius} border shadow-sm bg-gradient-to-br ${card.palette.bg} ${card.palette.border}`}
                        >
                            <CardBody className={`h-full flex flex-col ${current.cardBody}`}>
                                <div className="mb-2">
                                    <Icon className={`${current.icon} ${card.palette.icon}`} strokeWidth={1.8} />
                                </div>
                                <p className={`font-semibold tracking-tight text-gray-900 leading-tight ${current.title}`}>
                                    {card.title}
                                </p>
                                <p className={`leading-none font-extrabold ${card.palette.value} ${current.value}`}>
                                    {card.value}
                                </p>
                                {card.percentage !== null && (
                                    <>
                                        <p className={`font-bold text-gray-900 ${current.percentage}`}>
                                            {formatPercentage(card.percentage)}
                                        </p>
                                        <div className={`w-full rounded-full ${card.palette.track} ${current.progress}`}>
                                            <div
                                                className={`rounded-full ${card.palette.fill} ${current.progress}`}
                                                style={{ width: `${Math.max(0, Math.min(100, card.percentage))}%` }}
                                            />
                                        </div>
                                    </>
                                )}
                            </CardBody>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
