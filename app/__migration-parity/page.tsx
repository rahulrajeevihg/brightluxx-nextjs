import type { Metadata } from 'next';
import { MigrationParityDashboard } from '../../components/migration-parity-dashboard';

export const metadata: Metadata = {
  title: 'Migration Parity Dashboard',
  robots: { index: false, follow: false },
};

export default function MigrationParityPage() {
  return <MigrationParityDashboard />;
}