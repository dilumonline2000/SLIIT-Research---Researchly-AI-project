declare module "react-force-graph-2d" {
  import { ComponentType, MutableRefObject, RefAttributes } from "react";

  // Loose typing — the real lib has many props; we use a permissive any-friendly type.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type ForceGraph2DProps = Record<string, any> & RefAttributes<unknown>;

  const ForceGraph2D: ComponentType<ForceGraph2DProps>;
  export default ForceGraph2D;
}
