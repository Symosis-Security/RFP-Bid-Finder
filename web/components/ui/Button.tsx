import * as React from "react";
import { cn } from "@/lib/utils";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({
  className,
  variant = "primary",
  ...props
}: Props) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold transition active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none";

  const variants: Record<string, string> = {
    primary:
      "text-zinc-950 bg-linear-to-r/oklch from-yellow-300 via-amber-300 to-yellow-200 border border-white/60 shadow-[0_12px_30px_rgba(245,158,11,0.35)] hover:brightness-[0.98]",
    secondary:
      "text-zinc-950 bg-white/55 border border-white/70 hover:bg-white/70",
    ghost: "text-zinc-950 hover:bg-white/45",
  };

  return (
    <button className={cn(base, variants[variant], className)} {...props} />
  );
}
