import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '食愿 | 让校园好食物不被浪费',
  description: '发现校园周边的剩余食物盲盒，也让每一个小愿望找到回应。',
  metadataBase: new URL(process.env.SITE_URL ?? 'http://localhost:3000'),
  openGraph: {
    title: '食愿 | 让校园好食物不被浪费',
    description: '发现校园周边的剩余食物盲盒，也让每一个小愿望找到回应。',
    images: [{ url: '/og.png', width: 1792, height: 1024, alt: '食愿校园剩余食物领取场景' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: '食愿 | 让校园好食物不被浪费',
    description: '发现校园周边的剩余食物盲盒，也让每一个小愿望找到回应。',
    images: ['/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
