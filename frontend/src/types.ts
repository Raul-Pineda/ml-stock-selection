export interface ColumnInfo {
  name: string;
  dtype: string;
  sample: string;
}

export interface Schema {
  rows: number;
  quarters: number;
  quarter_range: string;
  features: string[];
  columns: ColumnInfo[];
}

export interface ComparisonRow {
  model: string;
  feature_set: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  roc_auc: number | null;
  spearman_ic: number | null;
  ndcg_at_k: number | null;
  precision_at_k: number | null;
  cagr: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  n_folds: number;
}

export interface PerQuarterRow {
  model: string;
  feature_set: string;
  quarter: string;
  [key: string]: string | number | null;
}

export interface FeatureImportance {
  features: string[];
  importances: number[];
}

export interface ModelRoster {
  model: string;
  layer: string;
}

export interface TrainProgress {
  event?: string;
  model?: string;
  layer?: string;
  fold?: number;
  total?: number;
  auc?: number;
}
