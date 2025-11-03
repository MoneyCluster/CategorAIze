import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type {Preset} from '@docusaurus/preset-classic';

const config: Config = {
  title: 'CategorAIze',
  tagline: 'Documentation',
  favicon: 'img/favicon.ico',

  // Replace <org> and <repo>
  url: 'https://<org>.github.io',
  baseUrl: '/CategorAIze/',

  organizationName: '<org>',
  projectName: 'CategorAIze',
  deploymentBranch: 'gh-pages',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  trailingSlash: false,
  i18n: {
    defaultLocale: 'ru',
    locales: ['ru'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../docs',
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.ts'),
          editUrl: 'https://github.com/<org>/CategorAIze/edit/main/docs/',
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'CategorAIze',
      logo: {alt: 'Logo', src: 'img/logo.svg'},
      items: [
        {to: '/', label: 'Документация', position: 'left'},
        {href: 'https://github.com/<org>/CategorAIze', label: 'GitHub', position: 'right'},
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {title: 'Docs', items: [{label: 'Введение', to: '/'}]},
        {title: 'Сообщество', items: [{label: 'Issues', href: 'https://github.com/<org>/CategorAIze/issues'}]},
        {title: 'Исходники', items: [{label: 'GitHub', href: 'https://github.com/<org>/CategorAIze'}]},
      ],
      copyright: `© ${new Date().getFullYear()} CategorAIze`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;


