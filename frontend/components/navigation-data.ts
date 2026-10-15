export type NavLink = readonly [label: string, href: string];

export const productGroups: ReadonlyArray<{ title: string; links: readonly NavLink[] }> = [
  {
    title: 'BY PRODUCT',
    links: [
      ['Indoor LED Displays', '/products?category=indoor'],
      ['Outdoor LED Displays', '/products?category=outdoor'],
      ['COB / MicroLED', '/products?category=cob-microled'],
      ['Transparent LED', '/products?category=transparent'],
      ['Interactive Displays', '/products?category=interactive'],
      ['Creative LED', '/products?category=flexible'],
    ],
  },
  {
    title: 'BY APPLICATION',
    links: [
      ['Retail', '/solutions/retail'],
      ['Corporate', '/solutions/corporate'],
      ['Control Rooms', '/solutions/control-rooms'],
      ['Transportation', '/solutions/transportation'],
      ['Events & XR', '/solutions/entertainment'],
      ['Architecture', '/solutions/architecture'],
    ],
  },
  {
    title: 'BY TECHNOLOGY',
    links: [
      ['COB Technology', '/technology/cob'],
      ['MicroLED & MiP', '/technology/microled'],
      ['Fine-Pitch LED', '/products?category=indoor'],
      ['Transparent LED', '/products?category=transparent'],
      ['Flexible LED', '/products?category=flexible'],
      ['Interactive Display', '/products?category=interactive'],
    ],
  },
];

export const solutionLinks: readonly NavLink[] = [
  ['Retail & Hospitality', '/solutions/retail'],
  ['Corporate & Offices', '/solutions/corporate'],
  ['Entertainment & Events', '/solutions/entertainment'],
  ['Transportation', '/solutions/transportation'],
  ['Control Rooms', '/solutions/control-rooms'],
  ['Architecture', '/solutions/architecture'],
  ['Dubai', '/led-screen-suppliers-dubai'],
  ['Saudi Arabia', '/saudi-arabia'],
];

export const moreLinks: readonly NavLink[] = [
  ['Technology', '/technology'],
  ['Calculators', '/tools'],
  ['Blog', '/blog'],
  ['Resources', '/resources'],
  ['Projects', '/projects'],
  ['About Us', '/about'],
  ['Contact Us', '/contact'],
];

export const mobileLinks: readonly NavLink[] = [
  ['Products', '/products'],
  ['Solutions', '/solutions'],
  ['Technology', '/technology'],
  ['Case Studies', '/case-studies'],
  ['Resources', '/resources'],
  ['For Architects', '/for-architects'],
  ['Contact', '/contact'],
];

export function navigationTestId(prefix: string, label: string) {
  return `${prefix}-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')}`;
}