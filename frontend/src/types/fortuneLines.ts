export type FortuneLinesData = {
  version: number;
  sourceFile?: string;
  generatedAt?: string;
  counts?: Record<string, number>;
  /** 피드 카테고리 id → 한 줄 문장 목록 */
  byCategory: Record<string, string[]>;
  note?: string;
};
