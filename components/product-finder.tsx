'use client';

import { useState } from 'react';
import { trackEvent } from '../lib/analytics';

const steps = [
  { id: 'environment', question: 'Where will the display be used?', options: [['indoor', 'Indoor'], ['outdoor', 'Outdoor']] },
  { id: 'application', question: 'What is the main application?', options: [['retail', 'Retail'], ['corporate', 'Corporate'], ['hospitality', 'Hospitality'], ['control-room', 'Control room'], ['advertising', 'Digital advertising'], ['education', 'Education'], ['home-cinema', 'Home cinema'], ['other', 'Other']] },
  { id: 'viewing', question: 'Approximate viewing distance?', options: [['close', 'Close'], ['medium', 'Medium'], ['long', 'Long'], ['unknown', 'Not sure']] },
  { id: 'priority', question: 'What matters most?', options: [['quality', 'Highest image quality'], ['brightness', 'High brightness'], ['transparent', 'Transparent'], ['interactive', 'Interactive'], ['large-format', 'Large format'], ['efficiency', 'Budget efficiency'], ['unknown', 'Not sure']] },
] as const;

function chooseCategory(answers: Record<string, string>) {
  if (answers.priority === 'transparent') return 'transparent';
  if (answers.priority === 'interactive') return 'interactive';
  if (answers.environment === 'outdoor' || answers.priority === 'brightness' || answers.application === 'advertising') return 'outdoor';
  if (answers.application === 'control-room' || answers.priority === 'quality' || answers.viewing === 'close') return 'cob-microled';
  if (answers.application === 'home-cinema') return 'cinema-led';
  return answers.priority === 'large-format' ? 'flexible' : (answers.environment === 'indoor' ? 'indoor' : 'all-in-one');
}

export function ProductFinder({ onApply }: { onApply: (category: string) => void }) {
  const [step, setStep] = useState(0); const [answers, setAnswers] = useState<Record<string, string>>({}); const [started, setStarted] = useState(false);
  const complete = step === steps.length; const active = steps[step]; const category = chooseCategory(answers);
  const select = (value: string) => { const next = { ...answers, [active.id]: value }; if (!started) { setStarted(true); trackEvent('product_finder_started'); } if (step + 1 === steps.length) trackEvent('product_finder_completed', { finder_result: chooseCategory(next) }); setAnswers(next); setStep(step + 1); };
  return <section id="product-finder" className="product-finder" data-testid="product-finder"><div><p className="eyebrow">Guided selection</p>{!complete ? <><h2>{active.question}</h2><div className="finder-options">{active.options.map(([value, label]) => <button type="button" key={value} onClick={() => select(value)} data-testid={`product-finder-${active.id}-${value}`}>{label}</button>)}</div><small>Step {step + 1} of {steps.length}</small></> : <div className="finder-complete"><div><h2>A focused starting point for your brief</h2><p>We’ve selected a relevant product category. Review the results, then speak with an engineer if site requirements are still developing.</p><p className="finder-summary" data-testid="product-finder-category-summary"><strong>{category.replaceAll('-', ' ')}</strong> is prioritised from your environment, viewing-distance and performance answers.</p></div><div><button type="button" onClick={() => onApply(category)} data-testid="product-finder-view-results">View recommendations →</button><a href="/contact" data-testid="product-finder-engineer-link">Talk to an Engineer</a><button type="button" className="finder-restart" onClick={() => { setAnswers({}); setStep(0); }} data-testid="product-finder-restart">Start again</button></div></div>}</div></section>;
}