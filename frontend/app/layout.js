import './globals.css';

export const metadata = {
  title: 'Sales Insight Automator',
  description: 'AI-powered sales data analyzer',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
