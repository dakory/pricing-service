import * as React from 'react';
export interface InputWithSelectFieldOption {
  label: string;
  value: string;
  linked?: boolean;
}
export interface InputWithSelectFieldProps {
  label?: string;
  options?: InputWithSelectFieldOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
}
export declare function InputWithSelectField(props: InputWithSelectFieldProps): JSX.Element;
