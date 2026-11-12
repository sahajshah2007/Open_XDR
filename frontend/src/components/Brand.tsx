import { PROJECT } from '../project';

export const BrandMark = ({ className = '' }: { className?: string }) => <svg viewBox="0 0 40 40" fill="none" aria-hidden="true" className={className}>
  <path d="M6 11 20 3l14 8v18L20 37 6 29V11Z" stroke="currentColor" strokeWidth="1.5" />
  <path d="m12 14 8-5 8 5v12l-8 5-8-5V14Z" stroke="currentColor" strokeWidth="1.5" opacity=".4" />
  <path d="m12 14 8 6 8-6M20 20v11M6 11l6 3m16 12 6 3" stroke="currentColor" strokeWidth="1.5" />
  <circle cx="20" cy="20" r="3" fill="currentColor" /><circle cx="6" cy="11" r="2" fill="currentColor" /><circle cx="34" cy="29" r="2" fill="currentColor" />
</svg>;

export default function Brand({ large = false }: { large?: boolean }) {
  return <div className={`brand ${large ? 'brand-large' : ''}`}><span className="brand-icon"><BrandMark /></span><div><span className="brand-name">{PROJECT.name}</span><span className="brand-caption">{PROJECT.tagline}</span></div></div>;
}
