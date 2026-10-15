import NextLink from 'next/link';
import type { ComponentProps } from 'react';

type SafeLinkProps = ComponentProps<typeof NextLink>;

export function SafeLink({ prefetch: _prefetch, ...props }: SafeLinkProps) {
  return <NextLink {...props} prefetch={false} />;
}