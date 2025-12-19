import * as React from "react";
import { cn } from "@/lib/utils";

export function Select({
  className,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-2xl border border-black/10 bg-white/80 px-3 text-sm text-zinc-950 shadow-sm outline-none focus:border-black/25 focus:ring-4 focus:ring-yellow-300/40",
        className
      )}
      {...props}
    />
  );
}
