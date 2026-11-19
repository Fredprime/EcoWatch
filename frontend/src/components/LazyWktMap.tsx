import { lazy, Suspense } from 'react';
import type { WktFeature } from './wkt';

const WktMap = lazy(() => import('./WktMap').then((module) => ({ default: module.WktMap })));

interface LazyWktMapProps {
  features: WktFeature[];
  skipped: number;
  emptyNote: string;
  ariaLabel: string;
}

/** MapLibre is large and only needed when stored geometry exists. */
export function LazyWktMap(props: LazyWktMapProps) {
  if (props.features.length === 0) {
    return <div className="notice notice-info" role="note">{props.emptyNote}</div>;
  }
  return (
    <Suspense fallback={<div className="notice notice-info" role="note">Loading stored geometry map…</div>}>
      <WktMap {...props} />
    </Suspense>
  );
}
