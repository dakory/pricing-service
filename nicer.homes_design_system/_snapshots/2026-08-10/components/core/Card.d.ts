import * as React from 'react';
export interface CardProps {
  padding?: string;
  elevated?: boolean;
  glass?: boolean;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}
export declare function Card(props: CardProps): JSX.Element;
