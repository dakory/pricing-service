declare module "react-dom" {
  const ReactDOM: { createPortal(children: unknown, container: Element): unknown };
  export default ReactDOM;
}
