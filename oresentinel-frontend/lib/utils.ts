import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Tailwind-aware className merge used by every component. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** 245.6 -> "245.6" ; 1234.5 -> "1,234.5" */
export function fmt(n: number, digits = 1) {
  return n.toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** "-10" -> "-10%" ; 7 -> "+7%" */
export function signedPct(n: number) {
  return `${n > 0 ? '+' : ''}${n}%`;
}

/** "2h ago" style relative labels (mock payloads already ship these). */
export function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
