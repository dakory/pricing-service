import * as React from 'react';
export interface SelectOption { label?: string; value?: string; }
export interface SelectProps {
  label?: string;
  options?: (SelectOption | string)[];
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  pill?: boolean;
}
export declare function Select(props: SelectProps): JSX.Element;
