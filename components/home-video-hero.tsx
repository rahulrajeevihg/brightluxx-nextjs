'use client';

import { useEffect, useRef, useState } from 'react';
import { SafeLink as Link } from './safe-link';

const HERO_VIDEO = 'https://customer-assets-jt897jd0.emergentagent.net/job_ac1c0cf4-c62d-45c1-91c0-8447971ba1b1/artifacts/a1d6k1sy_brightluxx%20video.MOV';
const POSTER = 'https://files.ihgbrands.com/hero-video-poster.webp';

export function HomeVideoHero() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      videoRef.current?.pause();
      setPaused(true);
    }
  }, []);

  const togglePlayback = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().then(() => setPaused(false)).catch(() => setPaused(true));
    } else {
      video.pause();
      setPaused(true);
    }
  };

  return (
    <section className="home-video-hero" data-testid="homepage-hero-video-container">
      <video
        ref={videoRef}
        className="home-video-hero__media"
        data-testid="homepage-hero-video-element"
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        poster={POSTER}
        aria-hidden="true"
      >
        <source src={HERO_VIDEO} type="video/quicktime" />
      </video>
      <div className="home-video-hero__scrim" />
      <div className="home-video-hero__content">
        <p className="eyebrow">Brightluxx · UAE & GCC</p>
        <h1 data-testid="hero-title">Visual systems with presence.</h1>
        <p>From first brief to live environment, Brightluxx engineers display systems that make architecture, information and experience feel more alive.</p>
        <nav aria-label="Hero actions">
          <Link href="/products" data-testid="homepage-hero-cta-primary">Explore Displays</Link>
          <Link href="/projects" data-testid="homepage-hero-cta-secondary">View Projects <span>→</span></Link>
        </nav>
        <div className="home-video-hero__ledger" data-testid="homepage-hero-proof-points">
          <span>Design + engineering</span><span>Manufacturing + QA</span><span>Installation + lifecycle</span>
        </div>
      </div>
      <button type="button" className="home-video-hero__toggle" onClick={togglePlayback} data-testid="homepage-hero-video-toggle" aria-label={paused ? 'Play hero video' : 'Pause hero video'}>
        {paused ? 'Play film' : 'Pause film'}
      </button>
    </section>
  );
}