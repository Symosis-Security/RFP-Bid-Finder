"use client";

import * as React from "react";

type Props = {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
};

export function Checkbox({ label, checked, onChange, disabled }: Props) {
  return (
    <label
      className={[
        "flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 transition",
        "border-black/10 bg-white/55 hover:bg-white/75",
        disabled ? "cursor-not-allowed opacity-60" : "",
      ].join(" ")}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-yellow-500"
      />

      <span className="text-sm font-medium text-zinc-950">
        {label}
      </span>
    </label>
  );
}
