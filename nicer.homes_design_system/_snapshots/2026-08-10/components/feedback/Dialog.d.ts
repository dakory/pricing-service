import * as React from 'react';
export interface DialogProps {
  open: boolean;
  title?: string;
  children?: React.ReactNode;
  onClose?: () => void;
  footer?: React.ReactNode;
}
export declare function Dialog(props: DialogProps): JSX.Element | null;
