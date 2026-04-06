declare module "react-plotly.js" {
  import { Component } from "react";
  import { PlotParams } from "plotly.js";
  export default class Plot extends Component<Partial<PlotParams> & { style?: React.CSSProperties; config?: Record<string, unknown> }> {}
}
