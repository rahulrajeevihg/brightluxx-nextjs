export const sitemapExcludedRoutes = new Set(['/lumimorph-elite']);

type CitySeoOverride = {
  title: string;
  description: string;
  heading?: string;
};

export const citySeo: Record<string, CitySeoOverride> = {
  '/abu-dhabi': {
    title: 'Video Walls & LED Screens in Abu Dhabi | Brightluxx',
    description: 'Plan video walls and LED screens for Abu Dhabi projects with Brightluxx engineering support, specification guidance and installation coordination.',
    heading: 'Video Walls & LED Screens in Abu Dhabi',
  },
  '/dubai': {
    title: 'LED Screens & Video Walls in Dubai | Brightluxx',
    description: 'Specify LED screens, video walls and digital signage for Dubai projects with Brightluxx engineering, delivery and installation support.',
  },
  '/oman': {
    title: 'LED Screens & Video Walls in Oman | Brightluxx',
    description: 'Plan LED screens and video walls for Oman projects with Brightluxx specification support, display selection and delivery coordination.',
  },
};

export const familyProductSchemas = {
  '/pixelvue': { name: 'PixelVue LED Display Range', sku: 'pixelvue', description: 'Brightluxx PixelVue LED display range for professional display projects.', image: 'https://files.ihgbrands.com/hero-video-poster.webp' },
  '/lumimorph': { name: 'LumiMorph LED Display Range', sku: 'lumimorph', description: 'Brightluxx LumiMorph LED display range for designed interior environments.', image: 'https://files.ihgbrands.com/brightluxx/site-images/opt-family-lumimorph.webp' },
  '/glassmorph': { name: 'GlassMorph LED Display Range', sku: 'glassmorph', description: 'Brightluxx GlassMorph display solutions for architectural glass and digital signage.', image: 'https://files.ihgbrands.com/hero-video-poster.webp' },
  '/naturatex': { name: 'NaturaTex LED Display Range', sku: 'naturatex', description: 'Brightluxx NaturaTex LED display range for textured display environments.', image: 'https://files.ihgbrands.com/brightluxx/site-images/opt_fam_naturatex.webp' },
  '/signatouch': { name: 'SignaTouch Interactive Display Range', sku: 'signatouch', description: 'Brightluxx SignaTouch interactive LED display range for public-facing environments.', image: 'https://files.ihgbrands.com/hero-video-poster.webp' },
} as const;

export type DetailContent = {
  heading: string;
  paragraphs: readonly string[];
  checklist: readonly string[];
};

export const routeSeoDetails: Record<string, DetailContent> = {
  '/applications/retail': {
    heading: 'Retail display planning',
    paragraphs: ['Retail LED systems need to work with the customer journey, viewing distance and the changing mix of campaign, brand and wayfinding content. The display is specified around the storefront, window, aisle, atrium or feature wall rather than around a panel alone.', 'Brightluxx helps project teams assess pixel pitch, ambient light, cabinet depth, sightlines and service access before a display family is selected. The same review also defines content resolution, processing, power distribution and the practical installation sequence.', 'For retail teams, the goal is a display that supports daily operation as well as launch-day impact. A coordinated brief helps marketing, fit-out, MEP and operations teams make decisions using the same dimensions, ownership and maintenance assumptions.'],
    checklist: ['Viewing distance and shopper dwell zones', 'Daylight, reflections and brightness target', 'Content workflow, resolution and processing', 'Power, mounting and service access'],
  },
  '/applications/corporate-av': {
    heading: 'Corporate AV display planning',
    paragraphs: ['Corporate AV displays are planned around meeting formats, presentation sources, camera positions and the viewing conditions of the room. Boardrooms, lobbies and collaboration spaces each require a different balance of resolution, brightness, acoustics and integration.', 'Brightluxx reviews the room geometry with the AV and interiors teams so pixel pitch, wall finish, processing, control and signal paths can be coordinated before installation. This reduces late changes around mounting depth, power and ventilation.', 'The resulting specification can support presentations, dashboards and video collaboration while preserving access for commissioning and long-term service.'],
    checklist: ['Room geometry and closest viewing position', 'Camera, audio and signal integration', 'Wall structure, ventilation and access', 'Control, processing and commissioning plan'],
  },
  '/applications/worship': {
    heading: 'Worship space display planning',
    paragraphs: ['Display systems for worship spaces need to support readable lyrics, live camera feeds and seasonal production without overwhelming the architecture or the congregation. Screen size, viewing angles and content contrast should be considered alongside stage lighting and acoustics.', 'Brightluxx works from the room layout and programming needs to guide pitch, brightness, image processing and mounting. The team also reviews sightlines from seating areas and the service approach for equipment installed above or behind the stage.', 'A coordinated specification keeps technical choices understandable for facilities teams while leaving flexibility for future content and production changes.'],
    checklist: ['Seating sightlines and text legibility', 'Stage lighting and camera compatibility', 'Rigging, wall loads and maintenance access', 'Content processing and operator workflow'],
  },
  '/applications/outdoor': {
    heading: 'Outdoor LED display planning',
    paragraphs: ['Outdoor LED projects are planned around daylight, weather exposure, viewing distance and local site constraints. Brightness alone is not the answer: cabinet protection, heat management, structure, access and content scheduling all affect long-term performance.', 'Brightluxx helps teams review the display location, approach routes, façade or steelwork, power availability and service method before selecting a product. This creates a clearer brief for structural, electrical and content stakeholders.', 'The result is an outdoor system selected for its operating environment and maintainability, not only for its initial visual impact.'],
    checklist: ['Daylight, weather and heat exposure', 'Viewing distance and approach speed', 'Structure, power and safe access', 'Content brightness and operating schedule'],
  },
  '/applications/transport': {
    heading: 'Transport display planning',
    paragraphs: ['Transport displays have to communicate quickly in spaces where people are moving, waiting and making decisions. Readability, redundancy, operating hours and integration with information systems are key specification topics.', 'Brightluxx helps project teams assess sightlines, pixel pitch, brightness, service access and the location of control equipment. The review also considers how the screen will be commissioned, monitored and maintained without disrupting the wider environment.', 'A clear display brief supports passenger information, wayfinding and commercial content while keeping the technical system practical for operations teams.'],
    checklist: ['Viewing distance and decision points', 'Content hierarchy and legibility', 'Operating hours and service access', 'Power, processing and monitoring'],
  },
  '/for-contractors': {
    heading: 'Contractor specification support',
    paragraphs: ['Contractors need display information that can be coordinated with drawings, finishes, MEP requirements and programme constraints. Brightluxx supports early review so the selected display and its interfaces are understood before site work begins.', 'The process focuses on measurable inputs: screen dimensions, pitch, brightness, weight, power, processing, mounting and access. These items help teams coordinate responsibility across fit-out, electrical, structural and AV work packages.', 'Project-specific support keeps technical decisions traceable and gives delivery teams a defined path from approved specification to commissioning.'],
    checklist: ['Drawing review and dimensional coordination', 'Power, data and ventilation allowances', 'Mounting, loads and access planning', 'Commissioning and handover scope'],
  },
  '/resource-library': {
    heading: 'LED display specification resources',
    paragraphs: ['The resource library helps specifiers turn an early display idea into a practical project brief. It brings together planning topics that influence performance, installation and ownership across different display environments.', 'Use the resources to compare technical terms, prepare questions for a supplier review and identify the information needed from architecture, AV, electrical and operations stakeholders. A clearer brief produces more useful options and avoids assumptions moving downstream.', 'When a project reaches a defined layout or scope, Brightluxx can review the technical inputs and help translate them into a coordinated display recommendation.'],
    checklist: ['Pixel pitch and viewing-distance guidance', 'Brightness, content and operating context', 'Power, structure and maintenance planning', 'Specification and enquiry preparation'],
  },
  '/compare-products': {
    heading: 'Compare LED display specifications',
    paragraphs: ['A comparison is most useful when the products are assessed against the same project conditions. Start with the display location, viewing distance, content type and operating hours, then compare the technical differences that affect the installation.', 'Brightluxx comparison guidance focuses on decision-relevant fields such as pixel pitch, brightness, resolution, applications and published specifications. This makes it easier for teams to narrow a shortlist before requesting a project-specific review.', 'For a final decision, the selected products should be checked against mounting, processing, power, service access and programme requirements as well as the visible display specification.'],
    checklist: ['Compare products against one brief', 'Review pitch, brightness and resolution together', 'Check published application suitability', 'Request engineering review before commitment'],
  },
  '/abu-dhabi': {
    heading: 'Fine-pitch video walls and installation',
    paragraphs: ['Fine-pitch video walls in Abu Dhabi are selected around the closest viewer, the purpose of the room and the content that will be displayed every day. Control rooms, executive spaces, visitor environments and public-facing areas can require very different pixel pitch, brightness and processing choices.', 'Video wall installation needs early coordination with the wall build-up, ventilation, power, signal distribution and safe maintenance access. Brightluxx reviews these practical conditions with the project team before finalising a display recommendation.', 'A defined scope helps align consultants, contractors and operations teams around the display system from early planning through commissioning and support.'],
    checklist: ['Fine-pitch selection for close viewing', 'Video wall installation coordination', 'Power, processing and service access', 'Project-specific engineering review'],
  },
};