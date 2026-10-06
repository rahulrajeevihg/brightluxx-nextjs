type VideoShowcase = { eyebrow: string; title: string; copy: string; source: string; testId: string };

const videos: Record<string, VideoShowcase> = {
  '/about': {
    eyebrow: 'Engineering in motion',
    title: 'How Brightluxx brings a system to life',
    copy: 'A closer view of the craftsmanship, testing and care behind every Brightluxx display environment.',
    source: 'https://files.ihgbrands.com/videos_hero-video-converted.mp4',
    testId: 'about-us-relocated-video',
  },
  '/solutions': {
    eyebrow: 'Applications in motion',
    title: 'Displays made for real environments',
    copy: 'From architecture to retail and public spaces, explore how visual systems shape the experience of a place.',
    source: 'https://files.ihgbrands.com/videos_hero-video-1.mp4',
    testId: 'solutions-relocated-video',
  },
};

export function BrandVideoShowcase({ route }: { route: string }) {
  const video = videos[route];
  if (!video) return null;
  return (
    <section className="brand-video-showcase" data-testid={video.testId}>
      <div className="brand-video-showcase__copy"><p className="eyebrow">{video.eyebrow}</p><h2>{video.title}</h2><p>{video.copy}</p></div>
      <div className="brand-video-showcase__media">
        <video muted autoPlay loop playsInline preload="metadata" poster="https://files.ihgbrands.com/hero-video-poster.webp" aria-hidden="true">
          <source src={video.source} type="video/mp4" />
        </video>
      </div>
    </section>
  );
}