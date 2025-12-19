"use client";

import * as React from "react";
import { SearchPanel } from "@/components/SearchPanel";
import { BidsTable } from "@/components/BidsTable";
import type { SearchResponse } from "@/lib/types";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";

export default function Page() {
  const [data, setData] = React.useState<SearchResponse>({ items: [], debug: {} });
  const [showDebug, setShowDebug] = React.useState(false);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8 flex flex-col gap-3">
        <div className="inline-flex items-center gap-3">
          <div className="h-11 w-11 rounded-2xl bg-yellow-400/70 ring-1 ring-yellow-700/20 shadow-[0_10px_30px_rgba(0,0,0,0.10)]" />
          <div>
            <h1 className="text-2xl font-semibold text-zinc-950">
              US Gov Bids Finder
            </h1>
            <p className="text-sm font-medium text-zinc-800">
              One search UI for contracts, grants, awards, and optional local datasets.
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-yellow-700/15 bg-white/70 px-4 py-3 text-sm text-zinc-900 shadow-[0_10px_30px_rgba(0,0,0,0.06)]">
          <span className="font-semibold">Tip:</span>{" "}
          For SAM.gov and Simpler Grants, set API keys in{" "}
          <code className="rounded-md bg-black/5 px-2 py-0.5 font-medium text-zinc-900">
            api/.env
          </code>
          .
        </div>
      </header>

      <div className="grid gap-6">
        <SearchPanel onResults={setData} />
        <BidsTable items={data.items} />

        <Card>
          <CardHeader className="flex items-center justify-between">
            <div>
              <div className="text-lg font-semibold text-zinc-950">Debug</div>
              <div className="text-sm text-zinc-700">
                Raw payloads per source (helpful for tuning and troubleshooting)
              </div>
            </div>

            <button
              onClick={() => setShowDebug((v) => !v)}
              className="rounded-xl border border-black/10 bg-white/60 px-3 py-2 text-sm font-medium text-zinc-900 shadow-sm hover:bg-white/80"
            >
              {showDebug ? "Hide" : "Show"}
            </button>
          </CardHeader>

          <CardContent>
            {showDebug ? (
              <pre className="max-h-[420px] overflow-auto rounded-2xl border border-black/10 bg-white/70 p-4 text-xs text-zinc-900">
                {JSON.stringify(data.debug, null, 2)}
              </pre>
            ) : (
              <div className="text-sm text-zinc-700">Hidden</div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
