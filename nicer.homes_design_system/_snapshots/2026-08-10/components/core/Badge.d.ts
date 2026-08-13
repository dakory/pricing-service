import * as React from 'react';
export interface BadgeProps {
  tone?: 'neutral' | 'accent' | 'success' | 'danger' | 'inverse';
  children?: React.ReactNode;
}
export declare function Badge(props: BadgeProps): JSX.Element;
