"use client";

import * as React from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Checkbox } from "@/components/ui/Checkbox";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import type { SearchPayload, SearchResponse } from "@/lib/types";

const ALL_SOURCES = [
  "SAM.gov (contracts)",
  "Grants.gov (grants)",
  "Simpler.Grants.gov (grants)",
  "USAspending (awards)",
  "FPDS Atom (awards)",
  "Data.gov CKAN (discovery)",
  "Socrata dataset (local)",
];

type Props = {
  onResults: (data: SearchResponse) => void;
};

export function SearchPanel({ onResults }: Props) {
  const [sources, setSources] = React.useState<string[]>([
    "SAM.gov (contracts)",
    "Grants.gov (grants)",
  ]);
  const [keyword, setKeyword] = React.useState("");
  const [daysBack, setDaysBack] = React.useState(30);
  const [maxRows, setMaxRows] = React.useState(50);
  const [timeoutS, setTimeoutS] = React.useState(20);
  const [cacheTtl, setCacheTtl] = React.useState(900);
  const [fpdsAtomUrl, setFpdsAtomUrl] = React.useState("");
  const [socrataUrl, setSocrataUrl] = React.useState("");

  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  function toggleSource(src: string, checked: boolean) {
    setSources((prev) => {
      if (checked) return Array.from(new Set([...prev, src]));
      return prev.filter((s) => s !== src);
    });
  }

  async function runSearch() {
    setLoading(true);
    setError(null);

    try {
      const payload: SearchPayload = {
        sources,
        keyword,
        days_back: daysBack,
        max_rows: maxRows,
        timeout_s: timeoutS,
        cache_ttl_s: cacheTtl,
        fpds_atom_url: fpdsAtomUrl,
        socrata_dataset_url: socrataUrl,
      };

      const res = await fetch(`${apiBase}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const data = (await res.json()) as SearchResponse;
      onResults(data);
    } catch (e: any) {
      setError(e?.message || "Search failed");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setKeyword("");
    setSources(["SAM.gov (contracts)", "Grants.gov (grants)"]);
    setDaysBack(30);
    setMaxRows(50);
    setTimeoutS(20);
    setCacheTtl(900);
    setFpdsAtomUrl("");
    setSocrataUrl("");
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-lg font-semibold text-zinc-950">Search</div>
            <div className="text-sm text-zinc-800">
              Federal contracts, grants, awards, plus optional local datasets.
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={reset} disabled={loading}>
              Reset
            </Button>

            <Button onClick={runSearch} disabled={loading || sources.length === 0}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner />
                  Searching
                </span>
              ) : (
                "Search"
              )}
            </Button>
          </div>
        </div>

        {error ? (
          <div className="rounded-xl border border-red-600/30 bg-red-50 px-3 py-2 text-sm text-red-900">
            {error}
          </div>
        ) : null}
      </CardHeader>

      <CardContent className="grid gap-5 text-zinc-950">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Keyword
            </div>
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="cybersecurity, SOC 2, NIST, chatbot, confluence"
            />
          </div>

          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Days back (SAM posted range)
            </div>
            <Select
              value={String(daysBack)}
              onChange={(e) => setDaysBack(parseInt(e.target.value, 10))}
            >
              {[7, 14, 30, 60, 90, 180, 365].map((d) => (
                <option key={d} value={d}>
                  {d} days
                </option>
              ))}
            </Select>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Max rows
            </div>
            <Select
              value={String(maxRows)}
              onChange={(e) => setMaxRows(parseInt(e.target.value, 10))}
            >
              {[25, 50, 100, 200].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
          </div>

          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Timeout
            </div>
            <Select
              value={String(timeoutS)}
              onChange={(e) => setTimeoutS(parseInt(e.target.value, 10))}
            >
              {[10, 15, 20, 30, 45, 60].map((n) => (
                <option key={n} value={n}>
                  {n} sec
                </option>
              ))}
            </Select>
          </div>

          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Cache TTL
            </div>
            <Select
              value={String(cacheTtl)}
              onChange={(e) => setCacheTtl(parseInt(e.target.value, 10))}
            >
              {[0, 300, 900, 1800, 3600].map((n) => (
                <option key={n} value={n}>
                  {n === 0 ? "Off" : `${n} sec`}
                </option>
              ))}
            </Select>
          </div>

          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Quick presets
            </div>
            <Button
              variant="secondary"
              onClick={() => {
                setKeyword("cybersecurity");
                setDaysBack(30);
                setMaxRows(50);
                setTimeoutS(20);
                setCacheTtl(900);
                setSources(["SAM.gov (contracts)", "Grants.gov (grants)"]);
              }}
              disabled={loading}
            >
              Default
            </Button>
          </div>
        </div>

        <div className="grid gap-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
            Sources
          </div>

          <div className="rounded-2xl border border-black/10 bg-white/60 p-3 shadow-sm">
            <div className="grid gap-2 md:grid-cols-2">
              {ALL_SOURCES.map((s) => (
                <Checkbox
                  key={s}
                  label={s}
                  checked={sources.includes(s)}
                  onChange={(checked) => toggleSource(s, checked)}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              FPDS Atom feed URL (optional)
            </div>
            <Input
              value={fpdsAtomUrl}
              onChange={(e) => setFpdsAtomUrl(e.target.value)}
              placeholder="Paste Atom feed URL from FPDS"
            />
            <div className="text-xs text-zinc-700">
              FPDS supports Atom feeds you generate in the FPDS UI.
            </div>
          </div>

          <div className="grid gap-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-800">
              Socrata dataset .json URL (optional)
            </div>
            <Input
              value={socrataUrl}
              onChange={(e) => setSocrataUrl(e.target.value)}
              placeholder="https://data.cityof.../resource/xxxx.json"
            />
            <div className="text-xs text-zinc-700">
              Use a direct .json endpoint from a city or county open data portal.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
