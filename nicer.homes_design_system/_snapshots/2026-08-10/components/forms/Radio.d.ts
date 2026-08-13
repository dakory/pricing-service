import * as React from 'react';
export interface RadioProps {
  label?: string;
  checked?: boolean;
  onChange?: () => void;
  name?: string;
}
export declare function Radio(props: RadioProps): JSX.Element;
