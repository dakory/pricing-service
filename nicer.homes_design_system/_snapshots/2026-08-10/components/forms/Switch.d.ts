import * as React from 'react';
export interface SwitchProps {
  checked?: boolean;
  onChange?: (checked: boolean) => void;
  label?: string;
}
export declare function Switch(props: SwitchProps): JSX.Element;
