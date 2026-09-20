import { redirect } from 'next/navigation';

/** The app entry always lands on the dashboard. */
export default function RootPage() {
  redirect('/dashboard');
}
