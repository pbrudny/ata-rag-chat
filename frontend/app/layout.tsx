import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AkademiaTA Assistant",
  description: "AI assistant for AkademiaTA students and applicants",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
