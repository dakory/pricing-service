Centered modal — confirmations, small forms.

```jsx
<Dialog open={open} title="Cancel booking?" onClose={close} footer={<><Button variant="secondary" onClick={close}>Back</Button><Button variant="primary" onClick={confirm}>Confirm</Button></>}>
  This can't be undone.
</Dialog>
```
