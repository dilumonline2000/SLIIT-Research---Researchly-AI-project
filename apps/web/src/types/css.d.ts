// Lets TypeScript accept stylesheet imports such as `import "./globals.css"`.
// Newer TypeScript versions (incl. the one bundled with VS Code) enable
// `noUncheckedSideEffectImports`, which errors on side-effect imports that
// have no type declaration (TS2882). Next.js handles the actual CSS bundling.
declare module "*.css";
