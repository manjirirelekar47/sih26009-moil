import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

/**
 * Global application shell: fixed dark sidebar + white sticky header +
 * scrollable light-gray content area.
 *
 * Layout geometry from the mockup:
 *   sidebar 240px fixed · header 70px sticky · content padded 24px
 */
export default function DashboardGroupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar />
      <div className="pl-[var(--sidebar-w)]">
        <Header />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
