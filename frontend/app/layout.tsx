import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PortfolioQuant Engine",
  description: "Recomendador cuantitativo de carteras de inversión",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
