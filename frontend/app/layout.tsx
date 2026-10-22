import "./globals.css";

export const metadata = {
  title: "Media Copilot | Inteligencia informativa",
  manifest: "/manifest.webmanifest",
  description: "Explora señales públicas, evalúa evidencia y crea informes revisables para diferentes organizaciones.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="es"><body>{children}</body></html>;
}
