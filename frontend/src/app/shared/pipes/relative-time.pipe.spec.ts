import { RelativeTimePipe } from './relative-time.pipe';

describe('RelativeTimePipe', () => {
  const pipe = new RelativeTimePipe();
  const now = new Date('2026-11-17T12:00:00Z');

  it('handles empty and invalid values', () => {
    expect(pipe.transform(null, now)).toBe('—');
    expect(pipe.transform('not a date', now)).toBe('—');
  });

  it('says "just now" for the last few seconds', () => {
    expect(pipe.transform('2026-11-17T11:59:40Z', now)).toBe('just now');
  });

  it('uses the largest sensible unit', () => {
    expect(pipe.transform('2026-11-17T11:55:00Z', now)).toBe('5 minutes ago');
    expect(pipe.transform('2026-11-17T09:00:00Z', now)).toBe('3 hours ago');
    expect(pipe.transform('2026-11-16T12:00:00Z', now)).toBe('yesterday');
    expect(pipe.transform('2026-11-03T12:00:00Z', now)).toBe('2 weeks ago');
  });
});
