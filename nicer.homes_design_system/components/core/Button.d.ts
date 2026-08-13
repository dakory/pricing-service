import * as React from 'react';
export interface ButtonProps {
  variant?: 'primary' | 'accent' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  type?: 'button' | 'submit';
  onClick?: () => void;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): JSX.Element;
