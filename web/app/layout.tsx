import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Srecko Kosovel AI Chat",
  description:
    "Chat with Srecko Kosovel (1904-1926), Slovenian avant-garde poet.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[var(--color-paper)] font-sans text-[var(--color-ink)] antialiased">
        {children}
      </body>
    </html>
  );
}
