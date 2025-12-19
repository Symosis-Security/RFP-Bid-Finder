export type BidItem = {
  source: string;
  title: string;
  buyer: string;
  posted_date: string;
  due_date: string;
  url: string;
  item_id: string;
};

export type SearchPayload = {
  sources: string[];
  keyword: string;
  days_back: number;
  max_rows: number;
  timeout_s: number;
  cache_ttl_s: number;
  fpds_atom_url?: string;
  socrata_dataset_url?: string;
};

export type SearchResponse = {
  items: BidItem[];
  debug: any;
};
