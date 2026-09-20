import PageHeader from '@/components/layout/PageHeader';
import KpiRow from '@/components/widgets/KpiRow';
import ActiveAlerts from '@/components/widgets/ActiveAlerts';
import QuickActions from '@/components/widgets/QuickActions';
import PromoCard from '@/components/widgets/PromoCard';
import ReserveMapCard from '@/components/map/ReserveMapCard';
import ProductionTrendChart from '@/components/charts/ProductionTrendChart';

/**
 * Dashboard — the 12-column grid from the mockup.
 * Left: KPI row (5 cards) then map (8 cols) + chart (4 cols).
 * Right rail: alerts, quick actions, promo card.
 */
export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Welcome back, Samiksha!"
        subtitle="AI-powered insights for a more productive and sustainable tomorrow."
      />

      <div className="space-y-4">
        <KpiRow />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          {/* Map + trend occupy the wide column */}
          <div className="space-y-4 xl:col-span-8">
            <ReserveMapCard height={380} />
            <ProductionTrendChart height={250} />
          </div>

          {/* Right rail */}
          <div className="space-y-4 xl:col-span-4">
            <ActiveAlerts />
            <QuickActions />
            <PromoCard />
          </div>
        </div>
      </div>
    </>
  );
}
