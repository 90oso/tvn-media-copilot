import "./globals.css";

export const metadata = {
  title: "Mesa de Redacción | TVN Media Copilot",
  description: "Investiga titulares, contrasta evidencia y registra decisiones editoriales humanas.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="es"><body>{children}</body></html>;
}
