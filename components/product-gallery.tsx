'use client';

import { useState } from 'react';

export function ProductGallery({ name, images }: { name: string; images: string[] }) {
  const [active, setActive] = useState(images[0]);
  return <div className="product-gallery" data-testid="product-gallery"><div className="product-gallery__main" data-testid="product-main-image"><img src={active} alt={name} fetchPriority="high" /></div>{images.length > 1 && <div className="product-gallery__thumbs" data-testid="product-gallery-thumbnails">{images.map((image, index) => <button type="button" key={image} className={image === active ? 'selected' : ''} onClick={() => setActive(image)} data-testid={`product-gallery-thumb-${index}`} aria-label={`View image ${index + 1} of ${name}`}><img src={image} alt={`${name} view ${index + 1}`} /></button>)}</div>}</div>;
}