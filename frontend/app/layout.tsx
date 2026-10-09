import "./globals.css";

export const metadata = {
  title: "Mesa de Redacción | TVN Media Copilot",
  manifest: "/manifest.webmanifest",
  description: "Consulta titulares, contrasta fuentes y revisa borradores antes de tomar decisiones editoriales.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="es"><body>{children}</body></html>;
}
