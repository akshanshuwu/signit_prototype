declare module "plotly.js-dist-min" {
  const Plotly: { react: (...args: unknown[]) => Promise<void> };
  export default Plotly;
}
