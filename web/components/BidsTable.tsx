// web/components/BidsTable.tsx
"use client";

import * as React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { BidItem } from "@/lib/types";

function downloadCsv(rows: BidItem[]) {
  const header = ["source", "title", "buyer", "posted_date", "due_date", "url", "item_id"];
  const escape = (v: string) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const lines = [
    header.join(","),
    ...rows.map((r) => header.map((k) => escape((r as any)[k] ?? "")).join(",")),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "gov_bids.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function RowLink({ url }: { url: string }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-2 rounded-2xl border border-black/10 bg-white/70 px-3 py-2 text-sm font-semibold text-zinc-950 shadow-sm hover:bg-white/85"
    >
      Open <span className="opacity-60">↗</span>
    </a>
  );
}

export function BidsTable({ items }: { items: BidItem[] }) {
  return (
    <Card className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_100%_0%,rgba(245,158,11,0.20),transparent_55%)]" />

      <CardHeader className="relative flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-lg font-extrabold text-zinc-950">Results</div>
          <div className="text-sm text-zinc-700">{items.length} items</div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => downloadCsv(items)}
            disabled={items.length === 0}
          >
            Export CSV
          </Button>
        </div>
      </CardHeader>

      <CardContent className="relative">
        <div className="overflow-hidden rounded-2xl border border-black/10 bg-white/55 shadow-sm">
          <div className="max-h-[520px] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-white/85 backdrop-blur">
                <tr className="text-zinc-900">
                  <th className="px-4 py-3 font-bold">Source</th>
                  <th className="px-4 py-3 font-bold">Title</th>
                  <th className="px-4 py-3 font-bold">Buyer</th>
                  <th className="px-4 py-3 font-bold">Posted</th>
                  <th className="px-4 py-3 font-bold">Due</th>
                  <th className="px-4 py-3 font-bold">Link</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-black/10 text-zinc-950">
                {items.map((it, idx) => (
                  <tr
                    key={`${it.source}-${it.item_id}-${idx}`}
                    className="hover:bg-yellow-200/35"
                  >
                    <td className="px-4 py-3">
                      <Badge className="border-black/10 bg-yellow-200/55 text-zinc-950">
                        {it.source}
                      </Badge>
                    </td>

                    <td className="px-4 py-3">
                      <div className="line-clamp-2 font-semibold">{it.title}</div>
                      <div className="mt-1 text-xs text-zinc-600">{it.item_id}</div>
                    </td>

                    <td className="px-4 py-3 text-zinc-800">
                      <div className="line-clamp-2">{it.buyer || "-"}</div>
                    </td>

                    <td className="px-4 py-3 text-zinc-800">{it.posted_date || "-"}</td>
                    <td className="px-4 py-3 text-zinc-800">{it.due_date || "-"}</td>

                    <td className="px-4 py-3">
                      {it.url ? <RowLink url={it.url} /> : <span className="text-zinc-500">-</span>}
                    </td>
                  </tr>
                ))}

                {items.length === 0 ? (
                  <tr>
                    <td className="px-4 py-10 text-center text-zinc-700" colSpan={6}>
                      No results yet. Run a search.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
