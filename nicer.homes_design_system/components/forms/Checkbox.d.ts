import * as React from 'react';
export interface CheckboxProps {
  label?: string;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
}
export declare function Checkbox(props: CheckboxProps): JSX.Element;
