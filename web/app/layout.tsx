// web/app/layout.tsx
import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-linear-to-br/oklch from-yellow-200 via-amber-200 to-yellow-100 text-zinc-950 antialiased">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_12%,rgba(255,255,255,0.85),transparent_55%)]" />
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_85%_25%,rgba(245,158,11,0.35),transparent_45%)]" />
        <div className="pointer-events-none fixed inset-0 bg-grain opacity-[0.10]" />
        {children}
      </body>
    </html>
  );
}
