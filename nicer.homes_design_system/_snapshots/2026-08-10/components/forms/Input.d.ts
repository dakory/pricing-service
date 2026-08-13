import * as React from 'react';
export interface InputProps {
  label?: string;
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  prefix?: React.ReactNode;
}
export declare function Input(props: InputProps): JSX.Element;
